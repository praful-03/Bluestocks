-- ============================================================
-- BLUESTOCK MF CAPSTONE — 10 SQL Analytics Queries
-- Day 2: Basic Analytics on bluestock_mf.db
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- Q1: Top 5 Funds by AUM
-- ─────────────────────────────────────────────────────────────
SELECT
    p.amfi_code,
    p.scheme_name,
    p.fund_house,
    p.aum_crore,
    p.category,
    p.plan
FROM fact_performance p
ORDER BY p.aum_crore DESC
LIMIT 5;


-- ─────────────────────────────────────────────────────────────
-- Q2: Average NAV per Month (for top 5 funds by AUM)
-- ─────────────────────────────────────────────────────────────
SELECT
    d.scheme_name,
    strftime('%Y-%m', n.nav_date) AS month,
    ROUND(AVG(n.nav), 4) AS avg_nav,
    COUNT(*) AS trading_days
FROM fact_nav n
JOIN dim_fund d ON n.amfi_code = d.amfi_code
WHERE n.amfi_code IN (
    SELECT amfi_code FROM fact_performance ORDER BY aum_crore DESC LIMIT 5
)
GROUP BY d.scheme_name, month
ORDER BY d.scheme_name, month;


-- ─────────────────────────────────────────────────────────────
-- Q3: SIP Inflow Year-over-Year Growth
-- ─────────────────────────────────────────────────────────────
SELECT
    strftime('%Y', month) AS year,
    ROUND(SUM(sip_inflow_crore), 2) AS total_sip_inflow_crore,
    ROUND(AVG(yoy_growth_pct), 2) AS avg_yoy_growth_pct,
    ROUND(MAX(sip_inflow_crore), 2) AS peak_monthly_inflow
FROM fact_sip_inflows
GROUP BY year
ORDER BY year;


-- ─────────────────────────────────────────────────────────────
-- Q4: Total Transaction Amount by State (Top 10)
-- ─────────────────────────────────────────────────────────────
SELECT
    state,
    COUNT(*) AS num_transactions,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr,
    COUNT(DISTINCT investor_id) AS unique_investors
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q5: Funds with Expense Ratio < 1% (Direct plans, cost-efficient)
-- ─────────────────────────────────────────────────────────────
SELECT
    d.amfi_code,
    d.scheme_name,
    d.fund_house,
    d.sub_category,
    d.expense_ratio_pct,
    d.plan
FROM dim_fund d
WHERE d.expense_ratio_pct < 1.0
ORDER BY d.expense_ratio_pct ASC;


-- ─────────────────────────────────────────────────────────────
-- Q6: Fund Performance Ranking by Sharpe Ratio (Risk-adjusted)
-- ─────────────────────────────────────────────────────────────
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    sharpe_ratio,
    sortino_ratio,
    return_3yr_pct,
    RANK() OVER (ORDER BY sharpe_ratio DESC) AS sharpe_rank
FROM fact_performance
WHERE category = 'Equity'
ORDER BY sharpe_ratio DESC;


-- ─────────────────────────────────────────────────────────────
-- Q7: Monthly Net Inflow by Category (Pivot-style)
-- ─────────────────────────────────────────────────────────────
SELECT
    month,
    ROUND(SUM(CASE WHEN category = 'Large Cap' THEN net_inflow_crore ELSE 0 END), 2) AS large_cap,
    ROUND(SUM(CASE WHEN category = 'Mid Cap' THEN net_inflow_crore ELSE 0 END), 2) AS mid_cap,
    ROUND(SUM(CASE WHEN category = 'Small Cap' THEN net_inflow_crore ELSE 0 END), 2) AS small_cap,
    ROUND(SUM(CASE WHEN category = 'ELSS' THEN net_inflow_crore ELSE 0 END), 2) AS elss,
    ROUND(SUM(CASE WHEN category = 'Liquid' THEN net_inflow_crore ELSE 0 END), 2) AS liquid,
    ROUND(SUM(net_inflow_crore), 2) AS total_net_inflow
FROM fact_category_inflows
GROUP BY month
ORDER BY month;


-- ─────────────────────────────────────────────────────────────
-- Q8: Investor Demographics — SIP Amount by Age Group & Gender
-- ─────────────────────────────────────────────────────────────
SELECT
    age_group,
    gender,
    COUNT(*) AS num_transactions,
    COUNT(DISTINCT investor_id) AS unique_investors,
    ROUND(SUM(amount_inr), 2) AS total_invested,
    ROUND(AVG(amount_inr), 2) AS avg_sip_amount
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group, gender
ORDER BY age_group, gender;


-- ─────────────────────────────────────────────────────────────
-- Q9: AUM Growth Trajectory by Fund House (CTE + Window)
-- ─────────────────────────────────────────────────────────────
WITH aum_ranked AS (
    SELECT
        fund_house,
        date,
        aum_crore,
        LAG(aum_crore) OVER (PARTITION BY fund_house ORDER BY date) AS prev_aum,
        ROUND(
            (aum_crore - LAG(aum_crore) OVER (PARTITION BY fund_house ORDER BY date))
            / NULLIF(LAG(aum_crore) OVER (PARTITION BY fund_house ORDER BY date), 0) * 100,
            2
        ) AS qoq_growth_pct
    FROM fact_aum
)
SELECT
    fund_house,
    date,
    aum_crore,
    qoq_growth_pct
FROM aum_ranked
ORDER BY fund_house, date;


-- ─────────────────────────────────────────────────────────────
-- Q10: Top Stock Holdings Across All Equity Funds (Overlap Analysis)
-- ─────────────────────────────────────────────────────────────
SELECT
    h.stock_name,
    h.sector,
    COUNT(DISTINCT h.amfi_code) AS num_funds_holding,
    ROUND(AVG(h.weight_pct), 2) AS avg_weight_pct,
    ROUND(SUM(h.market_value_cr), 2) AS total_market_value_cr
FROM fact_holdings h
GROUP BY h.stock_name, h.sector
HAVING num_funds_holding >= 3
ORDER BY num_funds_holding DESC, avg_weight_pct DESC
LIMIT 20;
