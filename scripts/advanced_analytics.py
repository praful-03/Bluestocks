"""
advanced_analytics.py
=====================
Day 6 Advanced Analytics & Quantitative Risk Modeling for Bluestock MF Capstone.

Computes:
  1. Historical Value at Risk (VaR 95%) & Conditional VaR (CVaR) for all 40 funds
  2. Rolling 90-day Sharpe ratio time-series for 5 key equity schemes
  3. Investor cohort retention and ticket size analysis (2022-2025)
  4. SIP continuation & churn risk modeling (gap > 35 days flagged as at-risk)
  5. Sector concentration risk via Herfindahl-Hirschman Index (HHI)
  6. Composite Fund Scorecard (0-100 normalized ranking)

Outputs saved to:
  - data/processed/var_cvar_report.csv
  - data/processed/cohort_analysis.csv
  - data/processed/sip_continuity.csv
  - data/processed/sector_hhi.csv
  - data/processed/fund_scorecard.csv
  - reports/charts/09_rolling_sharpe.png
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CHARTS_DIR = os.path.join(REPORTS_DIR, "charts")

os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

DARK_BG = "#0D1117"
CARD_BG = "#161B22"
TEXT_COL = "#C9D1D9"
ACCENT = "#58A6FF"
GRID_COL = "#21262D"

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": GRID_COL,
    "axes.labelcolor": TEXT_COL,
    "xtick.color": TEXT_COL,
    "ytick.color": TEXT_COL,
    "text.color": TEXT_COL,
    "grid.color": GRID_COL,
    "grid.linewidth": 0.5,
    "legend.facecolor": CARD_BG,
    "legend.edgecolor": GRID_COL,
    "font.family": "DejaVu Sans",
    "font.size": 9,
})


def run_var_cvar_analysis(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calculate 95% Historical VaR and CVaR for all 40 funds from daily returns."""
    print("  Computing Historical VaR (95%) and CVaR...")
    nav_df = pd.read_sql("SELECT amfi_code, nav_date, nav, daily_return FROM fact_nav ORDER BY amfi_code, nav_date", conn)
    fund_df = pd.read_sql("SELECT amfi_code, scheme_name, category, sub_category FROM dim_fund", conn)

    nav_df["nav_date"] = pd.to_datetime(nav_df["nav_date"])
    # If daily_return has nulls or isn't computed, calculate pct_change
    if nav_df["daily_return"].isna().sum() > len(nav_df) * 0.5:
        nav_df["daily_return"] = nav_df.groupby("amfi_code")["nav"].pct_change()

    results = []
    for amfi, group in nav_df.groupby("amfi_code"):
        returns = group["daily_return"].dropna()
        if len(returns) < 50:
            continue
        
        # 95% Historical VaR (5th percentile of daily returns)
        var_95_daily = np.percentile(returns, 5)
        # CVaR: mean of returns at or below VaR
        tail_losses = returns[returns <= var_95_daily]
        cvar_95_daily = tail_losses.mean() if len(tail_losses) > 0 else var_95_daily
        
        # Annualized VaR / CVaR
        var_95_annual = var_95_daily * np.sqrt(252)
        cvar_95_annual = cvar_95_daily * np.sqrt(252)

        results.append({
            "amfi_code": amfi,
            "daily_var_95_pct": round(var_95_daily * 100, 2),
            "daily_cvar_95_pct": round(cvar_95_daily * 100, 2),
            "annual_var_95_pct": round(var_95_annual * 100, 2),
            "annual_cvar_95_pct": round(cvar_95_annual * 100, 2),
        })

    var_df = pd.DataFrame(results).merge(fund_df, on="amfi_code", how="left")
    out_path = os.path.join(PROC_DIR, "var_cvar_report.csv")
    var_df.to_csv(out_path, index=False)
    print(f"  Saved VaR/CVaR report -> {out_path}")
    return var_df


def run_rolling_sharpe_analysis(conn: sqlite3.Connection) -> None:
    """Generate 90-day rolling Sharpe ratio chart for 5 prominent funds."""
    print("  Generating 90-day Rolling Sharpe chart...")
    nav_df = pd.read_sql("SELECT amfi_code, nav_date, nav, daily_return FROM fact_nav ORDER BY amfi_code, nav_date", conn)
    nav_df["nav_date"] = pd.to_datetime(nav_df["nav_date"])
    
    # Select 5 major representative funds
    funds_to_plot = [
        (119551, "SBI Bluechip (Large Cap)", "#2196F3"),
        (125497, "HDFC Top 100 (Large Cap)", "#00BCD4"),
        (120503, "ICICI Pru Bluechip (Large Cap)", "#4CAF50"),
        (118632, "Nippon Large Cap (Large Cap)", "#FF9800"),
        (120841, "Kotak Emerging Eq (Mid Cap)", "#E91E63"),
    ]
    
    rf_daily = 0.065 / 252  # 6.5% annual risk free rate
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for amfi, label, color in funds_to_plot:
        sub = nav_df[nav_df["amfi_code"] == amfi].sort_values("nav_date").copy()
        if sub.empty:
            continue
        if sub["daily_return"].isna().sum() > len(sub) * 0.5:
            sub["daily_return"] = sub["nav"].pct_change()
        rolling_mean = sub["daily_return"].rolling(90).mean()
        rolling_std = sub["daily_return"].rolling(90).std()
        sub["rolling_sharpe"] = ((rolling_mean - rf_daily) / rolling_std) * np.sqrt(252)
        
        ax.plot(sub["nav_date"], sub["rolling_sharpe"], label=label, color=color, linewidth=1.8)

    ax.axhline(0, color="#6E7681", linestyle="--", linewidth=1, alpha=0.7)
    ax.axhline(1.0, color="#2EA043", linestyle=":", linewidth=1, alpha=0.8, label="Sharpe = 1.0 (Good)")
    ax.set_title("90-Day Rolling Sharpe Ratio (Annualized) — Top Funds", fontsize=13, fontweight="bold", color="#FFFFFF", pad=15)
    ax.set_xlabel("Date", color=TEXT_COL, labelpad=8)
    ax.set_ylabel("Rolling Sharpe Ratio", color=TEXT_COL, labelpad=8)
    ax.legend(loc="upper left", framealpha=0.8)
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    
    chart_path = os.path.join(CHARTS_DIR, "09_rolling_sharpe.png")
    fig.savefig(chart_path, dpi=200)
    plt.close(fig)
    print(f"  Saved chart -> {chart_path}")


def run_cohort_analysis(conn: sqlite3.Connection) -> pd.DataFrame:
    """Group investors by first transaction year (2024/2025) and assess behavioral metrics."""
    print("  Performing Investor Cohort Analysis...")
    tx_df = pd.read_sql("""
        SELECT 
            investor_id, 
            transaction_date, 
            transaction_type, 
            amount_inr, 
            city_tier, 
            age_group 
        FROM fact_transactions
    """, conn)
    tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction_date"])
    
    # Determine cohort by year of first transaction
    first_tx = tx_df.groupby("investor_id")["transaction_date"].min().reset_index()
    first_tx["cohort_year"] = first_tx["transaction_date"].dt.year
    
    tx_merged = tx_df.merge(first_tx[["investor_id", "cohort_year"]], on="investor_id")
    
    cohort_summary = tx_merged.groupby("cohort_year").agg(
        total_investors=("investor_id", "nunique"),
        total_volume_inr=("amount_inr", "sum"),
        total_transactions=("amount_inr", "count"),
        avg_transaction_val=("amount_inr", "mean"),
        sip_transactions=("transaction_type", lambda x: (x == "SIP").sum()),
        lumpsum_transactions=("transaction_type", lambda x: (x == "Lumpsum").sum()),
        redemption_transactions=("transaction_type", lambda x: (x == "Redemption").sum()),
    ).reset_index()
    
    cohort_summary["avg_investor_spend"] = cohort_summary["total_volume_inr"] / cohort_summary["total_investors"]
    cohort_summary["sip_ratio_pct"] = round(cohort_summary["sip_transactions"] / cohort_summary["total_transactions"] * 100, 2)
    cohort_summary["redemption_ratio_pct"] = round(cohort_summary["redemption_transactions"] / cohort_summary["total_transactions"] * 100, 2)
    
    out_path = os.path.join(PROC_DIR, "cohort_analysis.csv")
    cohort_summary.to_csv(out_path, index=False)
    print(f"  Saved cohort analysis -> {out_path}")
    return cohort_summary


def run_sip_continuity_analysis(conn: sqlite3.Connection) -> pd.DataFrame:
    """Analyze SIP consistency and flag accounts with gaps > 35 days as at-risk."""
    print("  Analyzing SIP Continuity & Churn Risk...")
    sip_df = pd.read_sql("""
        SELECT investor_id, transaction_date, amount_inr 
        FROM fact_transactions 
        WHERE transaction_type = 'SIP'
        ORDER BY investor_id, transaction_date
    """, conn)
    sip_df["transaction_date"] = pd.to_datetime(sip_df["transaction_date"])
    
    results = []
    for inv_id, group in sip_df.groupby("investor_id"):
        if len(group) < 6:
            continue
        gaps = group["transaction_date"].diff().dt.days.dropna()
        avg_gap = gaps.mean()
        max_gap = gaps.max()
        std_gap = gaps.std() if len(gaps) > 1 else 0.0
        
        is_at_risk = 1 if max_gap > 35 else 0
        results.append({
            "investor_id": inv_id,
            "sip_count": len(group),
            "avg_gap_days": round(avg_gap, 1),
            "max_gap_days": int(max_gap),
            "std_gap_days": round(std_gap, 1),
            "is_at_risk": is_at_risk,
            "total_sip_inr": group["amount_inr"].sum(),
            "avg_sip_amount": round(group["amount_inr"].mean(), 2),
        })
        
    continuity_df = pd.DataFrame(results)
    out_path = os.path.join(PROC_DIR, "sip_continuity.csv")
    continuity_df.to_csv(out_path, index=False)
    
    at_risk_count = continuity_df["is_at_risk"].sum()
    total_qual = len(continuity_df)
    print(f"  Identified {at_risk_count}/{total_qual} ({at_risk_count/total_qual*100:.1f}%) at-risk SIP investors.")
    print(f"  Saved SIP continuity report -> {out_path}")
    return continuity_df


def run_sector_hhi_analysis(conn: sqlite3.Connection) -> pd.DataFrame:
    """Compute Herfindahl-Hirschman Index (HHI) for equity fund portfolio sector concentration."""
    print("  Calculating Sector Concentration HHI...")
    holdings_df = pd.read_sql("""
        SELECT amfi_code, sector, SUM(weight_pct) as sector_weight
        FROM fact_holdings
        GROUP BY amfi_code, sector
    """, conn)
    fund_df = pd.read_sql("SELECT amfi_code, scheme_name, sub_category FROM dim_fund", conn)
    
    # HHI = sum(weight_i ^ 2)
    holdings_df["weight_sq"] = holdings_df["sector_weight"] ** 2
    hhi_df = holdings_df.groupby("amfi_code")["weight_sq"].sum().reset_index()
    hhi_df.rename(columns={"weight_sq": "sector_hhi"}, inplace=True)
    hhi_df["sector_hhi"] = round(hhi_df["sector_hhi"], 2)
    
    # Interpretation: < 1500 = Diversified, 1500-2500 = Moderately Concentrated, > 2500 = Highly Concentrated
    def classify_hhi(val):
        if val < 1500:
            return "Diversified"
        elif val <= 2500:
            return "Moderately Concentrated"
        else:
            return "Highly Concentrated"
            
    hhi_df["concentration_grade"] = hhi_df["sector_hhi"].apply(classify_hhi)
    hhi_df = hhi_df.merge(fund_df, on="amfi_code", how="left")
    
    out_path = os.path.join(PROC_DIR, "sector_hhi.csv")
    hhi_df.to_csv(out_path, index=False)
    print(f"  Saved Sector HHI report -> {out_path}")
    return hhi_df


def run_fund_scorecard(conn: sqlite3.Connection) -> pd.DataFrame:
    """Build composite 0-100 Fund Scorecard based on multi-factor weighted rankings."""
    print("  Computing Composite Fund Scorecard (0-100)...")
    query = """
        SELECT 
            f.amfi_code,
            f.scheme_name,
            f.fund_house,
            f.sub_category,
            f.expense_ratio_pct,
            p.return_3yr_pct,
            p.sharpe_ratio,
            p.alpha,
            p.max_drawdown_pct
        FROM dim_fund f
        INNER JOIN fact_performance p ON f.amfi_code = p.amfi_code
    """
    df = pd.read_sql(query, conn)
    
    # Normalized ranks (0 to 1)
    df["rank_return"] = df["return_3yr_pct"].rank(pct=True)
    df["rank_sharpe"] = df["sharpe_ratio"].rank(pct=True)
    df["rank_alpha"] = df["alpha"].rank(pct=True)
    df["rank_expense"] = df["expense_ratio_pct"].rank(pct=True, ascending=False)  # lower TER is better
    df["rank_drawdown"] = df["max_drawdown_pct"].rank(pct=True)  # less negative is better
    
    # Composite formula: 30% 3Y Return + 25% Sharpe + 20% Alpha + 15% Expense + 10% Max DD
    df["composite_score"] = round((
        0.30 * df["rank_return"] +
        0.25 * df["rank_sharpe"] +
        0.20 * df["rank_alpha"] +
        0.15 * df["rank_expense"] +
        0.10 * df["rank_drawdown"]
    ) * 100, 1)
    
    df["composite_rank"] = df["composite_score"].rank(ascending=False, method="min").astype(int)
    scorecard = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
    
    cols = [
        "composite_rank", "composite_score", "scheme_name", "fund_house", 
        "sub_category", "return_3yr_pct", "sharpe_ratio", "alpha", 
        "expense_ratio_pct", "max_drawdown_pct"
    ]
    scorecard = scorecard[cols]
    
    out_path = os.path.join(PROC_DIR, "fund_scorecard.csv")
    scorecard.to_csv(out_path, index=False)
    print(f"  Saved Fund Scorecard -> {out_path}")
    return scorecard


def main():
    print("=" * 75)
    print("  BLUESTOCK MF CAPSTONE — DAY 6 ADVANCED ANALYTICS")
    print("=" * 75)
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found. Run ETL pipeline first.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    try:
        run_var_cvar_analysis(conn)
        run_rolling_sharpe_analysis(conn)
        run_cohort_analysis(conn)
        run_sip_continuity_analysis(conn)
        run_sector_hhi_analysis(conn)
        run_fund_scorecard(conn)
    finally:
        conn.close()
    print("=" * 75)
    print("  Advanced analytics execution completed successfully.")
    print("=" * 75)


if __name__ == "__main__":
    main()
