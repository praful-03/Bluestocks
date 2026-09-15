"""
export_mf_dashboard.py
======================
Extracts aggregated metrics and analytical tables from bluestock_mf.db
and exports them into dashboard/mf_data.js for instant browser-based visualization.
"""

import os
import json
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
OUT_JS = os.path.join(DASHBOARD_DIR, "mf_data.js")

os.makedirs(DASHBOARD_DIR, exist_ok=True)


def export_dashboard_data():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    data = {}

    try:
        # 1. Headline KPIs
        data["kpis"] = {
            "total_aum_lakh_cr": 81.0,
            "monthly_sip_inflow_cr": 31002.0,
            "total_folios_cr": 26.12,
            "active_sip_accounts_cr": 9.35,
            "total_schemes_tracked": 40,
            "industry_schemes": 1908,
            "avg_equity_sharpe": 0.91,
            "top_performing_fund": "SBI Small Cap Fund (23.39% 3Y CAGR)",
        }

        # 2. AUM by Fund House (Fact AUM)
        aum_df = pd.read_sql("SELECT date, fund_house, aum_lakh_crore, aum_crore FROM fact_aum ORDER BY date, aum_crore DESC", conn)
        data["aum_by_fund_house"] = aum_df.to_dict(orient="records")

        # Top 10 fund houses latest AUM
        latest_date = aum_df["date"].max()
        top_amcs = aum_df[aum_df["date"] == latest_date].sort_values("aum_crore", ascending=False)
        data["latest_top_amcs"] = top_amcs.to_dict(orient="records")

        # 3. Monthly SIP Inflows & Market Comparison (Fact SIP Inflows + Nifty 50)
        sip_df = pd.read_sql("""
            SELECT month, sip_inflow_crore, active_sip_accounts_crore, new_sip_accounts_lakh, sip_aum_lakh_crore, yoy_growth_pct 
            FROM fact_sip_inflows 
            ORDER BY month
        """, conn)
        
        # Monthly Nifty 50 close proxy from fact_benchmark
        bench_df = pd.read_sql("""
            SELECT strftime('%Y-%m', date) as month, AVG(close_value) as nifty50_avg
            FROM fact_benchmark 
            WHERE index_name = 'NIFTY50'
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """, conn)
        
        sip_merged = sip_df.merge(bench_df, on="month", how="left")
        sip_merged["nifty50_avg"] = sip_merged["nifty50_avg"].ffill().fillna(18000)
        data["monthly_sip_trends"] = sip_merged.to_dict(orient="records")

        # 4. Industry Folio Growth
        folio_df = pd.read_sql("SELECT month, total_folios_crore, equity_folios_crore, debt_folios_crore, hybrid_folios_crore FROM fact_folio_count ORDER BY month", conn)
        data["folio_growth"] = folio_df.to_dict(orient="records")

        # 5. Category-wise Inflows
        cat_df = pd.read_sql("SELECT month, category, net_inflow_crore FROM fact_category_inflows ORDER BY month, net_inflow_crore DESC", conn)
        data["category_inflows"] = cat_df.to_dict(orient="records")

        # 6. Fund Performance & Scorecard (40 Funds)
        perf_query = """
            SELECT 
                f.amfi_code,
                f.scheme_name,
                f.fund_house,
                f.category,
                f.sub_category,
                f.plan,
                f.expense_ratio_pct,
                f.risk_category,
                p.return_1yr_pct,
                p.return_3yr_pct,
                p.return_5yr_pct,
                p.benchmark_3yr_pct,
                p.alpha,
                p.beta,
                p.sharpe_ratio,
                p.sortino_ratio,
                p.std_dev_ann_pct,
                p.max_drawdown_pct,
                p.aum_crore,
                p.morningstar_rating
            FROM dim_fund f
            INNER JOIN fact_performance p ON f.amfi_code = p.amfi_code
            ORDER BY p.sharpe_ratio DESC
        """
        perf_df = pd.read_sql(perf_query, conn)
        data["funds"] = perf_df.to_dict(orient="records")

        # 7. Investor Demographic & Transaction Insights (Fact Transactions)
        # Transactions by State
        state_df = pd.read_sql("""
            SELECT state, COUNT(*) as tx_count, SUM(amount_inr) as total_volume_inr, AVG(amount_inr) as avg_ticket_inr
            FROM fact_transactions
            GROUP BY state
            ORDER BY total_volume_inr DESC
        """, conn)
        data["investor_by_state"] = state_df.to_dict(orient="records")

        # Transaction Type Split
        type_df = pd.read_sql("""
            SELECT transaction_type, COUNT(*) as tx_count, SUM(amount_inr) as total_volume_inr
            FROM fact_transactions
            GROUP BY transaction_type
        """, conn)
        data["transaction_types"] = type_df.to_dict(orient="records")

        # Age Group vs Average SIP
        age_df = pd.read_sql("""
            SELECT age_group, COUNT(*) as tx_count, AVG(amount_inr) as avg_amount_inr, SUM(amount_inr) as total_volume_inr
            FROM fact_transactions
            WHERE transaction_type = 'SIP'
            GROUP BY age_group
            ORDER BY age_group
        """, conn)
        data["sip_by_age"] = age_df.to_dict(orient="records")

        # City Tier (T30 vs B30)
        tier_df = pd.read_sql("""
            SELECT city_tier, COUNT(*) as tx_count, SUM(amount_inr) as total_volume_inr, AVG(amount_inr) as avg_ticket_inr
            FROM fact_transactions
            GROUP BY city_tier
        """, conn)
        data["city_tier_split"] = tier_df.to_dict(orient="records")

        # Payment Mode
        pay_df = pd.read_sql("""
            SELECT payment_mode, COUNT(*) as tx_count, SUM(amount_inr) as total_volume_inr
            FROM fact_transactions
            GROUP BY payment_mode
            ORDER BY tx_count DESC
        """, conn)
        data["payment_modes"] = pay_df.to_dict(orient="records")

        # 8. Historical NAV trend comparison (Sampled monthly for 5 funds + benchmark)
        nav_sample_df = pd.read_sql("""
            SELECT 
                strftime('%Y-%m', nav_date) as month,
                amfi_code,
                AVG(nav) as avg_nav
            FROM fact_nav
            WHERE amfi_code IN (119551, 125497, 120503, 118632, 120841)
            GROUP BY strftime('%Y-%m', nav_date), amfi_code
            ORDER BY month
        """, conn)
        data["nav_samples"] = nav_sample_df.to_dict(orient="records")

    finally:
        conn.close()

    # Write to mf_data.js
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("// Bluestock Mutual Fund Analytics Platform — Generated Data Export\n")
        f.write("const MF_DASHBOARD_DATA = ")
        json.dump(data, f, indent=2)
        f.write(";\n")

    print(f"  Successfully exported mutual fund dashboard data -> {OUT_JS}")


def main():
    export_dashboard_data()


if __name__ == "__main__":
    main()
