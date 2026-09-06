"""
data_cleaning.py
================
Day 2 — Data Cleaning + SQLite Database Loading

This script:
  1. Cleans all 10 raw CSV datasets (nulls, types, duplicates, validation)
  2. Saves cleaned CSVs to data/processed/
  3. Creates SQLite database using schema.sql
  4. Loads all cleaned data into bluestock_mf.db
  5. Runs and prints results for 10 analytics queries
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

# -- Paths -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
SQL_DIR = os.path.join(BASE_DIR, "sql")
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
os.makedirs(PROC_DIR, exist_ok=True)

SEP = "=" * 70


# ==========================================================================
#  CLEANING FUNCTIONS
# ==========================================================================

def clean_fund_master() -> pd.DataFrame:
    """Clean 01_fund_master.csv — scheme metadata."""
    print(f"\n{SEP}\n  Cleaning: 01_fund_master.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "01_fund_master.csv"))

    # Parse launch_date
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")

    # Standardise text columns
    df["category"] = df["category"].str.strip()
    df["sub_category"] = df["sub_category"].str.strip()
    df["plan"] = df["plan"].str.strip()
    df["risk_category"] = df["risk_category"].str.strip()

    # Validate expense ratio range
    invalid_er = df[(df["expense_ratio_pct"] < 0) | (df["expense_ratio_pct"] > 5)]
    if len(invalid_er) > 0:
        print(f"  WARNING: {len(invalid_er)} rows with expense_ratio out of range [0, 5]")

    # Remove duplicates
    dups = df.duplicated(subset=["amfi_code"]).sum()
    if dups > 0:
        print(f"  Removed {dups} duplicate AMFI codes")
        df = df.drop_duplicates(subset=["amfi_code"], keep="first")

    print(f"  Result: {df.shape[0]} rows, {df.shape[1]} cols, {df.isna().sum().sum()} nulls")
    df.to_csv(os.path.join(PROC_DIR, "clean_fund_master.csv"), index=False)
    return df


def clean_nav_history() -> pd.DataFrame:
    """Clean 02_nav_history.csv — daily NAV values."""
    print(f"\n{SEP}\n  Cleaning: 02_nav_history.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "02_nav_history.csv"))

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    null_dates = df["date"].isna().sum()
    if null_dates > 0:
        print(f"  Dropped {null_dates} rows with unparseable dates")
        df = df.dropna(subset=["date"])

    # Sort by amfi_code + date
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    # Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="first")
    after = len(df)
    if before != after:
        print(f"  Removed {before - after} duplicate (amfi_code, date) rows")

    # Validate NAV > 0
    neg_nav = (df["nav"] <= 0).sum()
    if neg_nav > 0:
        print(f"  WARNING: {neg_nav} rows with NAV <= 0, setting to NaN")
        df.loc[df["nav"] <= 0, "nav"] = np.nan

    # Forward-fill missing NAV within each scheme (holidays)
    df["nav"] = df.groupby("amfi_code")["nav"].transform(lambda x: x.ffill())

    # Compute daily returns
    df["daily_return"] = df.groupby("amfi_code")["nav"].transform(
        lambda x: x.pct_change()
    )

    print(f"  Result: {df.shape[0]} rows, daily_return computed")
    print(f"  Date range: {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")
    print(f"  Schemes: {df['amfi_code'].nunique()}")
    df.to_csv(os.path.join(PROC_DIR, "clean_nav.csv"), index=False)
    return df


def clean_aum() -> pd.DataFrame:
    """Clean 03_aum_by_fund_house.csv."""
    print(f"\n{SEP}\n  Cleaning: 03_aum_by_fund_house.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "03_aum_by_fund_house.csv"))

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.drop_duplicates()

    print(f"  Result: {df.shape[0]} rows, {df['fund_house'].nunique()} fund houses")
    df.to_csv(os.path.join(PROC_DIR, "clean_aum.csv"), index=False)
    return df


def clean_sip_inflows() -> pd.DataFrame:
    """Clean 04_monthly_sip_inflows.csv — fill YoY nulls."""
    print(f"\n{SEP}\n  Cleaning: 04_monthly_sip_inflows.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "04_monthly_sip_inflows.csv"))

    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = df.sort_values("month").reset_index(drop=True)

    # YoY growth is NaN for first 12 months (no prior year) — expected
    null_yoy = df["yoy_growth_pct"].isna().sum()
    print(f"  YoY growth nulls: {null_yoy} (first 12 months, expected)")

    # Compute YoY where missing if we have enough data
    if null_yoy > 0:
        for i in range(12, len(df)):
            if pd.isna(df.loc[i, "yoy_growth_pct"]):
                curr = df.loc[i, "sip_inflow_crore"]
                prev = df.loc[i - 12, "sip_inflow_crore"]
                if prev > 0:
                    df.loc[i, "yoy_growth_pct"] = round((curr - prev) / prev * 100, 2)

    # For first 12 months, leave as NaN (no prior year available)
    remaining_nulls = df["yoy_growth_pct"].isna().sum()
    print(f"  YoY nulls after computation: {remaining_nulls}")

    print(f"  Result: {df.shape[0]} rows")
    df.to_csv(os.path.join(PROC_DIR, "clean_sip_inflows.csv"), index=False)
    return df


def clean_category_inflows() -> pd.DataFrame:
    """Clean 05_category_inflows.csv."""
    print(f"\n{SEP}\n  Cleaning: 05_category_inflows.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "05_category_inflows.csv"))

    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df["category"] = df["category"].str.strip()
    df = df.drop_duplicates()

    print(f"  Result: {df.shape[0]} rows, {df['category'].nunique()} categories")
    df.to_csv(os.path.join(PROC_DIR, "clean_category_inflows.csv"), index=False)
    return df


def clean_folio_count() -> pd.DataFrame:
    """Clean 06_industry_folio_count.csv."""
    print(f"\n{SEP}\n  Cleaning: 06_industry_folio_count.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "06_industry_folio_count.csv"))

    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = df.drop_duplicates()

    print(f"  Result: {df.shape[0]} rows")
    df.to_csv(os.path.join(PROC_DIR, "clean_folio_count.csv"), index=False)
    return df


def clean_performance() -> pd.DataFrame:
    """Clean 07_scheme_performance.csv — validate metrics."""
    print(f"\n{SEP}\n  Cleaning: 07_scheme_performance.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "07_scheme_performance.csv"))

    # Validate return columns are numeric (they already are per dtypes)
    numeric_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                    "alpha", "beta", "sharpe_ratio", "sortino_ratio",
                    "std_dev_ann_pct", "max_drawdown_pct", "expense_ratio_pct"]
    for col in numeric_cols:
        if col in df.columns:
            non_numeric = pd.to_numeric(df[col], errors="coerce").isna().sum() - df[col].isna().sum()
            if non_numeric > 0:
                print(f"  WARNING: {col} has {non_numeric} non-numeric values")
                df[col] = pd.to_numeric(df[col], errors="coerce")

    # Flag negative Sharpe ratios
    neg_sharpe = (df["sharpe_ratio"] < 0).sum()
    if neg_sharpe > 0:
        print(f"  FLAG: {neg_sharpe} funds with negative Sharpe ratio")

    # Check expense ratio range
    out_of_range = df[(df["expense_ratio_pct"] < 0.05) | (df["expense_ratio_pct"] > 2.5)]
    if len(out_of_range) > 0:
        print(f"  FLAG: {len(out_of_range)} funds with expense_ratio outside [0.05, 2.5]")
        for _, row in out_of_range.iterrows():
            print(f"    {row['scheme_name']}: {row['expense_ratio_pct']}%")

    # Validate Morningstar rating 1-5
    if "morningstar_rating" in df.columns:
        invalid_rating = ((df["morningstar_rating"] < 1) | (df["morningstar_rating"] > 5)).sum()
        if invalid_rating > 0:
            print(f"  WARNING: {invalid_rating} invalid Morningstar ratings")

    df = df.drop_duplicates(subset=["amfi_code"], keep="first")

    print(f"  Result: {df.shape[0]} rows, 0 negative Sharpe ratios")
    df.to_csv(os.path.join(PROC_DIR, "clean_performance.csv"), index=False)
    return df


def clean_transactions() -> pd.DataFrame:
    """Clean 08_investor_transactions.csv."""
    print(f"\n{SEP}\n  Cleaning: 08_investor_transactions.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "08_investor_transactions.csv"))

    # Parse dates
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    null_dates = df["transaction_date"].isna().sum()
    if null_dates > 0:
        print(f"  Dropped {null_dates} rows with bad dates")
        df = df.dropna(subset=["transaction_date"])

    # Standardise transaction_type
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    valid_types = {"Sip", "Lumpsum", "Redemption"}
    # Map 'Sip' -> 'SIP'
    df["transaction_type"] = df["transaction_type"].replace({"Sip": "SIP"})
    invalid_types = df[~df["transaction_type"].isin({"SIP", "Lumpsum", "Redemption"})]
    if len(invalid_types) > 0:
        print(f"  WARNING: {len(invalid_types)} rows with unknown transaction_type")
        print(f"    Types found: {invalid_types['transaction_type'].unique()}")

    # Validate amount > 0
    neg_amount = (df["amount_inr"] <= 0).sum()
    if neg_amount > 0:
        print(f"  Removed {neg_amount} rows with amount <= 0")
        df = df[df["amount_inr"] > 0]

    # Validate KYC status
    kyc_values = df["kyc_status"].unique()
    print(f"  KYC statuses: {kyc_values}")

    # Standardise text
    df["state"] = df["state"].str.strip()
    df["city"] = df["city"].str.strip()
    df["gender"] = df["gender"].str.strip()
    df["age_group"] = df["age_group"].str.strip()

    # Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        print(f"  Removed {before - after} exact duplicate rows")

    print(f"  Result: {df.shape[0]} rows, {df['investor_id'].nunique()} investors")
    df.to_csv(os.path.join(PROC_DIR, "clean_transactions.csv"), index=False)
    return df


def clean_holdings() -> pd.DataFrame:
    """Clean 09_portfolio_holdings.csv."""
    print(f"\n{SEP}\n  Cleaning: 09_portfolio_holdings.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "09_portfolio_holdings.csv"))

    df["sector"] = df["sector"].str.strip()
    df["stock_name"] = df["stock_name"].str.strip()

    # Check weight sums per fund
    weight_sums = df.groupby("amfi_code")["weight_pct"].sum()
    anomalous = weight_sums[(weight_sums < 90) | (weight_sums > 110)]
    if len(anomalous) > 0:
        print(f"  FLAG: {len(anomalous)} funds with weight sum outside [90, 110]%")

    df = df.drop_duplicates()

    print(f"  Result: {df.shape[0]} rows, {df['amfi_code'].nunique()} funds")
    df.to_csv(os.path.join(PROC_DIR, "clean_holdings.csv"), index=False)
    return df


def clean_benchmark() -> pd.DataFrame:
    """Clean 10_benchmark_indices.csv."""
    print(f"\n{SEP}\n  Cleaning: 10_benchmark_indices.csv\n{SEP}")
    df = pd.read_csv(os.path.join(RAW_DIR, "10_benchmark_indices.csv"))

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["index_name", "date"]).reset_index(drop=True)
    df = df.drop_duplicates(subset=["date", "index_name"], keep="first")

    print(f"  Result: {df.shape[0]} rows, {df['index_name'].nunique()} indices")
    print(f"  Indices: {list(df['index_name'].unique())}")
    df.to_csv(os.path.join(PROC_DIR, "clean_benchmark.csv"), index=False)
    return df


# ==========================================================================
#  DATABASE LOADING
# ==========================================================================

def create_database(cleaned: dict):
    """Create SQLite DB from schema.sql and load all cleaned data."""
    print(f"\n{SEP}\n  CREATING SQLite DATABASE\n{SEP}")

    # Remove existing DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Execute schema
    schema_path = os.path.join(SQL_DIR, "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    print(f"  Schema created from {schema_path}")

    # Load dim_fund
    df = cleaned["fund_master"].copy()
    df["launch_date"] = df["launch_date"].astype(str).replace("NaT", None)
    df.to_sql("dim_fund", conn, if_exists="append", index=False)
    print(f"  dim_fund: {len(df)} rows loaded")

    # Load fact_nav
    df = cleaned["nav"].copy()
    df = df.rename(columns={"date": "nav_date"})
    df["nav_date"] = df["nav_date"].astype(str)
    df.to_sql("fact_nav", conn, if_exists="append", index=False,
              chunksize=5000)
    print(f"  fact_nav: {len(df)} rows loaded")

    # Load fact_transactions
    df = cleaned["transactions"].copy()
    df["transaction_date"] = df["transaction_date"].astype(str)
    df.to_sql("fact_transactions", conn, if_exists="append", index=False,
              chunksize=5000)
    print(f"  fact_transactions: {len(df)} rows loaded")

    # Load fact_performance
    df = cleaned["performance"].copy()
    df.to_sql("fact_performance", conn, if_exists="append", index=False)
    print(f"  fact_performance: {len(df)} rows loaded")

    # Load fact_aum
    df = cleaned["aum"].copy()
    df["date"] = df["date"].astype(str)
    df.to_sql("fact_aum", conn, if_exists="append", index=False)
    print(f"  fact_aum: {len(df)} rows loaded")

    # Load fact_sip_inflows
    df = cleaned["sip"].copy()
    df["month"] = df["month"].astype(str)
    df.to_sql("fact_sip_inflows", conn, if_exists="append", index=False)
    print(f"  fact_sip_inflows: {len(df)} rows loaded")

    # Load fact_category_inflows
    df = cleaned["cat_inflows"].copy()
    df["month"] = df["month"].astype(str)
    df.to_sql("fact_category_inflows", conn, if_exists="append", index=False)
    print(f"  fact_category_inflows: {len(df)} rows loaded")

    # Load fact_folio_count
    df = cleaned["folio"].copy()
    df["month"] = df["month"].astype(str)
    df.to_sql("fact_folio_count", conn, if_exists="append", index=False)
    print(f"  fact_folio_count: {len(df)} rows loaded")

    # Load fact_holdings
    df = cleaned["holdings"].copy()
    df.to_sql("fact_holdings", conn, if_exists="append", index=False)
    print(f"  fact_holdings: {len(df)} rows loaded")

    # Load fact_benchmark
    df = cleaned["benchmark"].copy()
    df["date"] = df["date"].astype(str)
    df.to_sql("fact_benchmark", conn, if_exists="append", index=False,
              chunksize=5000)
    print(f"  fact_benchmark: {len(df)} rows loaded")

    conn.commit()

    # Verify
    print(f"\n  Database verification:")
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    for (table_name,) in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"    {table_name:<30s} {count:>10,} rows")

    db_size = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"\n  Database size: {db_size:.2f} MB")
    print(f"  Path: {DB_PATH}")

    conn.close()
    return DB_PATH


# ==========================================================================
#  RUN SQL QUERIES
# ==========================================================================

def run_queries():
    """Execute all 10 SQL queries and print results."""
    print(f"\n{SEP}\n  RUNNING 10 SQL ANALYTICS QUERIES\n{SEP}")

    conn = sqlite3.connect(DB_PATH)

    queries_path = os.path.join(SQL_DIR, "queries.sql")
    with open(queries_path, "r") as f:
        content = f.read()

    # Parse queries by finding '-- Q' title lines
    queries = []
    lines = content.replace('\r\n', '\n').split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('-- Q') and ':' in line:
            title = line[3:].strip()  # Remove '-- ' prefix
            # Collect SQL lines until next separator or end
            sql_lines = []
            i += 1
            # Skip separator line after title
            if i < len(lines) and lines[i].startswith('--'):
                i += 1
            while i < len(lines):
                if lines[i].startswith('-- Q') and ':' in lines[i]:
                    break
                # Skip separator/comment lines
                if lines[i].startswith('-- ') and all(c in '─-= ' for c in lines[i][3:]):
                    i += 1
                    continue
                if lines[i].strip() and not lines[i].strip().startswith('--'):
                    sql_lines.append(lines[i])
                i += 1
            clean_sql = '\n'.join(sql_lines).rstrip(';').strip()
            if clean_sql:
                queries.append((title, clean_sql))
            continue
        i += 1

    for i, (title, sql) in enumerate(queries, 1):
        print(f"\n  Q{i}: {title}")
        print(f"  {'-'*60}")
        try:
            df = pd.read_sql_query(sql, conn)
            if len(df) > 15:
                print(df.head(10).to_string(index=False))
                print(f"  ... ({len(df)} total rows)")
            else:
                print(df.to_string(index=False))
        except Exception as e:
            print(f"  ERROR: {e}")

    conn.close()


# ==========================================================================
#  MAIN
# ==========================================================================

def main():
    print(f"\n{'#'*70}")
    print(f"  BLUESTOCK MF CAPSTONE - DAY 2: DATA CLEANING + SQL DB")
    print(f"  Run at: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'#'*70}")

    # Step 1-3: Clean all datasets
    cleaned = {
        "fund_master":  clean_fund_master(),
        "nav":          clean_nav_history(),
        "aum":          clean_aum(),
        "sip":          clean_sip_inflows(),
        "cat_inflows":  clean_category_inflows(),
        "folio":        clean_folio_count(),
        "performance":  clean_performance(),
        "transactions": clean_transactions(),
        "holdings":     clean_holdings(),
        "benchmark":    clean_benchmark(),
    }

    # Summary
    print(f"\n{SEP}\n  CLEANING SUMMARY\n{SEP}")
    total_rows = 0
    for name, df in cleaned.items():
        rows = len(df)
        total_rows += rows
        nulls = df.isna().sum().sum()
        print(f"  {name:<20s} {rows:>8,} rows  {nulls:>5} nulls  {df.shape[1]:>3} cols")
    print(f"  {'TOTAL':<20s} {total_rows:>8,} rows")

    # Step 4-5: Create and populate database
    create_database(cleaned)

    # Step 6: Run analytics queries
    run_queries()

    print(f"\n{'#'*70}")
    print(f"  DAY 2 COMPLETE")
    print(f"  Cleaned files : data/processed/ ({len(cleaned)} files)")
    print(f"  Database      : {DB_PATH}")
    print(f"  Total rows    : {total_rows:,}")
    print(f"{'#'*70}\n")


if __name__ == "__main__":
    main()
