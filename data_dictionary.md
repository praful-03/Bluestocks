# Data Dictionary — Bluestock MF Capstone

All datasets sourced from AMFI India, mfapi.in, NSE, and BSE public data.

---

## dim_fund (01_fund_master.csv)
Master reference for all 40 mutual fund schemes.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| amfi_code | INTEGER (PK) | Unique AMFI scheme code (6 digits) | AMFI India |
| fund_house | TEXT | Asset Management Company name | AMFI India |
| scheme_name | TEXT | Full scheme name (includes plan type) | AMFI India |
| category | TEXT | Broad category: Equity / Debt | SEBI classification |
| sub_category | TEXT | Sub-category: Large Cap, Mid Cap, Small Cap, Liquid, etc. | SEBI classification |
| plan | TEXT | Regular / Direct | AMFI India |
| launch_date | DATE | Scheme inception date | AMFI India |
| benchmark | TEXT | Benchmark index (e.g., NIFTY 100 TRI) | AMFI India |
| expense_ratio_pct | REAL | Total expense ratio as percentage | AMFI Monthly factsheet |
| exit_load_pct | REAL | Exit load percentage | AMFI factsheet |
| min_sip_amount | INTEGER | Minimum SIP investment (INR) | AMC website |
| min_lumpsum_amount | INTEGER | Minimum lumpsum investment (INR) | AMC website |
| fund_manager | TEXT | Name of the fund manager | AMC factsheet |
| risk_category | TEXT | Risk level: Low / Moderate / Moderately High / High / Very High | SEBI riskometer |
| sebi_category_code | TEXT | SEBI category code (e.g., EC01 = Large Cap) | SEBI |

---

## fact_nav (02_nav_history.csv)
Daily Net Asset Value for all 40 schemes, Jan 2022 – May 2026.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code | AMFI India |
| nav_date | DATE | Trading date | mfapi.in / AMFI |
| nav | REAL | Net Asset Value per unit (INR), must be > 0 | mfapi.in |
| daily_return | REAL | Daily return: (NAV_t / NAV_{t-1}) - 1 | Computed |

---

## fact_transactions (08_investor_transactions.csv)
Simulated investor transactions across 5,000 investors.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| investor_id | TEXT | Unique investor identifier (INV_XXXX) | Simulated |
| transaction_date | DATE | Date of transaction | Simulated |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code | AMFI India |
| transaction_type | TEXT | SIP / Lumpsum / Redemption | Simulated |
| amount_inr | REAL | Transaction amount in INR, must be > 0 | Simulated |
| state | TEXT | Indian state of investor | Simulated |
| city | TEXT | City of investor | Simulated |
| city_tier | TEXT | T30 (Top 30) / B30 (Beyond 30) | AMFI classification |
| age_group | TEXT | Age bracket: 18-25, 26-35, 36-45, 46-55, 55+ | Simulated |
| gender | TEXT | Male / Female / Other | Simulated |
| annual_income_lakh | REAL | Annual income in lakhs | Simulated |
| payment_mode | TEXT | UPI / Net Banking / NACH / Cheque | Simulated |
| kyc_status | TEXT | Verified / Pending / Incomplete | Simulated |

---

## fact_performance (07_scheme_performance.csv)
Pre-computed performance and risk metrics for all 40 schemes.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| amfi_code | INTEGER (PK) | References dim_fund.amfi_code | AMFI India |
| scheme_name | TEXT | Scheme name | AMFI India |
| fund_house | TEXT | AMC name | AMFI India |
| category | TEXT | Equity / Debt | SEBI |
| plan | TEXT | Regular / Direct | AMFI India |
| return_1yr_pct | REAL | 1-year CAGR (%) | Computed from NAV |
| return_3yr_pct | REAL | 3-year CAGR (%) | Computed from NAV |
| return_5yr_pct | REAL | 5-year CAGR (%) | Computed from NAV |
| benchmark_3yr_pct | REAL | Benchmark 3-year return (%) | NSE/BSE index data |
| alpha | REAL | Jensen's Alpha (annualised) | Computed: OLS regression |
| beta | REAL | Market sensitivity (slope of regression) | Computed: OLS regression |
| sharpe_ratio | REAL | (Rp - Rf) / Std(Rp), Rf = 6.5% | Computed |
| sortino_ratio | REAL | (Rp - Rf) / Downside_Std | Computed |
| std_dev_ann_pct | REAL | Annualised standard deviation (%) | Computed |
| max_drawdown_pct | REAL | Maximum peak-to-trough decline (%) | Computed |
| aum_crore | INTEGER | Assets Under Management (INR crore) | AMFI quarterly |
| expense_ratio_pct | REAL | Total expense ratio (0.05–2.5%) | AMFI factsheet |
| morningstar_rating | INTEGER | Star rating 1–5 | Morningstar |
| risk_grade | TEXT | Risk classification | SEBI riskometer |

---

## fact_aum (03_aum_by_fund_house.csv)
Quarterly AUM for 10 major fund houses, 2022–2025.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| date | DATE | Quarter-end date | AMFI quarterly report |
| fund_house | TEXT | AMC name | AMFI India |
| aum_lakh_crore | REAL | AUM in lakh crore (INR) | AMFI quarterly |
| aum_crore | REAL | AUM in crore (INR) | AMFI quarterly |
| num_schemes | INTEGER | Number of active schemes | AMFI quarterly |

---

## fact_sip_inflows (04_monthly_sip_inflows.csv)
Monthly industry-level SIP data, Jan 2022 – Dec 2025.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| month | DATE | Calendar month | AMFI Monthly Note |
| sip_inflow_crore | REAL | Monthly SIP inflow (INR crore) | AMFI Monthly Note |
| active_sip_accounts_crore | REAL | Active SIP accounts (crore) | AMFI Monthly Note |
| new_sip_accounts_lakh | REAL | New SIP registrations (lakh) | AMFI Monthly Note |
| sip_aum_lakh_crore | REAL | SIP AUM (lakh crore) | AMFI Monthly Note |
| yoy_growth_pct | REAL | Year-over-year growth (%). NULL for first 12 months | Computed |

---

## fact_category_inflows (05_category_inflows.csv)
Net inflows by fund category, monthly.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| month | DATE | Calendar month | AMFI |
| category | TEXT | Fund category (Large Cap, Mid Cap, etc.) | SEBI classification |
| net_inflow_crore | REAL | Net inflow/outflow (INR crore) | AMFI Monthly Note |

---

## fact_folio_count (06_industry_folio_count.csv)
Industry-level folio counts by type.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| month | DATE | Calendar month | AMFI |
| total_folios_crore | REAL | Total MF folios (crore) | AMFI |
| equity_folios_crore | REAL | Equity-only folios (crore) | AMFI |
| debt_folios_crore | REAL | Debt-only folios (crore) | AMFI |
| hybrid_folios_crore | REAL | Hybrid folios (crore) | AMFI |
| others_folios_crore | REAL | Other category folios (crore) | AMFI |

---

## fact_holdings (09_portfolio_holdings.csv)
Top equity holdings per fund as of Dec 2025.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code | AMFI India |
| stock_symbol | TEXT | NSE/BSE ticker symbol | NSE India |
| stock_name | TEXT | Company name | NSE India |
| sector | TEXT | Industry sector | NSE India |
| weight_pct | REAL | Portfolio weight (%) | AMC factsheet |
| market_value_cr | REAL | Market value (INR crore) | AMC factsheet |
| as_of_date | DATE | Holdings date | AMC factsheet |
| report_quarter | TEXT | Reporting quarter | AMC factsheet |

---

## fact_benchmark (10_benchmark_indices.csv)
Daily closing values for benchmark indices.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| id | INTEGER (PK) | Auto-increment row ID | Generated |
| date | DATE | Trading date | NSE/BSE |
| index_name | TEXT | Index name (Nifty 50, Nifty 100, etc.) | NSE/BSE |
| close_value | REAL | Closing value | NSE/BSE daily reports |
