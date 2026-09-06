-- ============================================================
-- BLUESTOCK MF CAPSTONE — SQLite Database Schema
-- Day 2: Star Schema Design
-- ============================================================
-- 1 Dimension table  + 7 Fact/Reference tables
-- ============================================================

-- ── DIMENSION TABLE ──────────────────────────────────────────

-- Master reference for all 40 mutual fund schemes
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code         INTEGER PRIMARY KEY,
    fund_house        TEXT NOT NULL,
    scheme_name       TEXT NOT NULL,
    category          TEXT NOT NULL,          -- Equity / Debt
    sub_category      TEXT NOT NULL,          -- Large Cap, Mid Cap, etc.
    plan              TEXT NOT NULL,          -- Regular / Direct
    launch_date       DATE,
    benchmark         TEXT,
    expense_ratio_pct REAL,
    exit_load_pct     REAL,
    min_sip_amount    INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager      TEXT,
    risk_category     TEXT,                   -- Low / Moderate / High / Very High
    sebi_category_code TEXT
);

-- ── FACT TABLES ──────────────────────────────────────────────

-- Daily NAV values with computed daily returns
CREATE TABLE IF NOT EXISTS fact_nav (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code     INTEGER NOT NULL,
    nav_date      DATE NOT NULL,
    nav           REAL NOT NULL CHECK(nav > 0),
    daily_return  REAL,                      -- (nav_t / nav_t-1) - 1
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    UNIQUE(amfi_code, nav_date)
);

-- Investor buy/sell/SIP transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT NOT NULL,
    transaction_date    DATE NOT NULL,
    amfi_code           INTEGER NOT NULL,
    transaction_type    TEXT NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr          REAL NOT NULL CHECK(amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Scheme-level performance & risk metrics
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code          INTEGER PRIMARY KEY,
    scheme_name        TEXT,
    fund_house         TEXT,
    category           TEXT,
    plan               TEXT,
    return_1yr_pct     REAL,
    return_3yr_pct     REAL,
    return_5yr_pct     REAL,
    benchmark_3yr_pct  REAL,
    alpha              REAL,
    beta               REAL,
    sharpe_ratio       REAL,
    sortino_ratio      REAL,
    std_dev_ann_pct    REAL,
    max_drawdown_pct   REAL,
    aum_crore          INTEGER,
    expense_ratio_pct  REAL CHECK(expense_ratio_pct BETWEEN 0.0 AND 5.0),
    morningstar_rating INTEGER CHECK(morningstar_rating BETWEEN 1 AND 5),
    risk_grade         TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Quarterly AUM by fund house
CREATE TABLE IF NOT EXISTS fact_aum (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              DATE NOT NULL,
    fund_house        TEXT NOT NULL,
    aum_lakh_crore    REAL,
    aum_crore         REAL,
    num_schemes       INTEGER
);

-- Monthly SIP industry inflows
CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    month                      DATE NOT NULL,
    sip_inflow_crore           REAL,
    active_sip_accounts_crore  REAL,
    new_sip_accounts_lakh      REAL,
    sip_aum_lakh_crore         REAL,
    yoy_growth_pct             REAL
);

-- Category-wise net inflows
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    month            DATE NOT NULL,
    category         TEXT NOT NULL,
    net_inflow_crore REAL
);

-- Industry folio count
CREATE TABLE IF NOT EXISTS fact_folio_count (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    month                 DATE NOT NULL,
    total_folios_crore    REAL,
    equity_folios_crore   REAL,
    debt_folios_crore     REAL,
    hybrid_folios_crore   REAL,
    others_folios_crore   REAL
);

-- Portfolio holdings (stock-level)
CREATE TABLE IF NOT EXISTS fact_holdings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,
    stock_symbol    TEXT,
    stock_name      TEXT,
    sector          TEXT,
    weight_pct      REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date  DATE,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Benchmark index daily close values
CREATE TABLE IF NOT EXISTS fact_benchmark (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    date         DATE NOT NULL,
    index_name   TEXT NOT NULL,
    close_value  REAL NOT NULL,
    UNIQUE(date, index_name)
);

-- ── INDEXES FOR PERFORMANCE ─────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_nav_amfi_date ON fact_nav(amfi_code, nav_date);
CREATE INDEX IF NOT EXISTS idx_nav_date ON fact_nav(nav_date);
CREATE INDEX IF NOT EXISTS idx_txn_investor ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_txn_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_benchmark_date ON fact_benchmark(date);
CREATE INDEX IF NOT EXISTS idx_holdings_amfi ON fact_holdings(amfi_code);
