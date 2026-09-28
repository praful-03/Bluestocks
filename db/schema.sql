 -- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
-- SQLite Relational Database Schema (10+ Tables)
-- PRAGMA foreign_keys = ON must be enabled per connection

PRAGMA foreign_keys = ON;

-- 1. Master Company Reference
CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(12) PRIMARY KEY,
    company_logo TEXT,
    company_name VARCHAR(255) NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value NUMERIC,
    book_value NUMERIC,
    roce_percentage NUMERIC,
    roe_percentage NUMERIC
);

-- 2. Annual Profit & Loss Statements
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER,
    company_id VARCHAR(12) NOT NULL,
    year VARCHAR(10) NOT NULL,
    sales NUMERIC,
    expenses NUMERIC,
    operating_profit NUMERIC,
    opm_percentage NUMERIC,
    other_income NUMERIC,
    interest NUMERIC,
    depreciation NUMERIC,
    profit_before_tax NUMERIC,
    tax_percentage NUMERIC,
    net_profit NUMERIC,
    eps NUMERIC,
    dividend_payout NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 3. Annual Balance Sheet
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER,
    company_id VARCHAR(12) NOT NULL,
    year VARCHAR(10) NOT NULL,
    equity_capital NUMERIC,
    reserves NUMERIC,
    borrowings NUMERIC,
    other_liabilities NUMERIC,
    total_liabilities NUMERIC,
    fixed_assets NUMERIC,
    cwip NUMERIC,
    investments NUMERIC,
    other_asset NUMERIC,
    total_assets NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 4. Annual Cash Flow Statements
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER,
    company_id VARCHAR(12) NOT NULL,
    year VARCHAR(10) NOT NULL,
    operating_activity NUMERIC,
    investing_activity NUMERIC,
    financing_activity NUMERIC,
    net_cash_flow NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 5. Pre-computed Growth Metrics (Analysis)
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY,
    company_id VARCHAR(12) NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 6. Annual Report Documents Repository
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    company_id VARCHAR(12) NOT NULL,
    year INTEGER NOT NULL,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 7. Qualitative Pros & Cons
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY,
    company_id VARCHAR(12) NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 8. Company Sector Mapping
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER,
    company_id VARCHAR(12) PRIMARY KEY,
    broad_sector VARCHAR(100) NOT NULL,
    sub_sector VARCHAR(100) NOT NULL,
    index_weight_pct NUMERIC,
    market_cap_category VARCHAR(50),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 9. Monthly OHLCV Stock Prices
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER,
    company_id VARCHAR(12) NOT NULL,
    date VARCHAR(10) NOT NULL,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume INTEGER,
    adjusted_close NUMERIC,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 10. Annual Market Capitalisation & Valuation Multiples
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER,
    company_id VARCHAR(12) NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore NUMERIC,
    enterprise_value_crore NUMERIC,
    pe_ratio NUMERIC,
    pb_ratio NUMERIC,
    ev_ebitda NUMERIC,
    dividend_yield_pct NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 11. Pre-Computed Financial Ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER,
    company_id VARCHAR(12) NOT NULL,
    year VARCHAR(10) NOT NULL,
    net_profit_margin_pct NUMERIC,
    operating_profit_margin_pct NUMERIC,
    return_on_equity_pct NUMERIC,
    debt_to_equity NUMERIC,
    interest_coverage NUMERIC,
    asset_turnover NUMERIC,
    free_cash_flow_cr NUMERIC,
    capex_cr NUMERIC,
    earnings_per_share NUMERIC,
    book_value_per_share NUMERIC,
    dividend_payout_ratio_pct NUMERIC,
    total_debt_cr NUMERIC,
    cash_from_operations_cr NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 12. Peer Comparison Groups
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name VARCHAR(100) NOT NULL,
    company_id VARCHAR(12) NOT NULL,
    is_benchmark BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_pl_cid_yr ON profitandloss(company_id, year);
CREATE INDEX IF NOT EXISTS idx_bs_cid_yr ON balancesheet(company_id, year);
CREATE INDEX IF NOT EXISTS idx_cf_cid_yr ON cashflow(company_id, year);
CREATE INDEX IF NOT EXISTS idx_sp_cid_dt ON stock_prices(company_id, date);
CREATE INDEX IF NOT EXISTS idx_fr_cid_yr ON financial_ratios(company_id, year);
CREATE INDEX IF NOT EXISTS idx_mc_cid_yr ON market_cap(company_id, year);
CREATE INDEX IF NOT EXISTS idx_sectors_broad ON sectors(broad_sector);
CREATE INDEX IF NOT EXISTS idx_peer_group ON peer_groups(peer_group_name);
