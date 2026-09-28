"""
Data Ingestion and ETL Pipeline for Nifty 100 Financial Intelligence Platform.
Loads 12 source files, executes 16 Data Quality rules, populates nifty100.db,
and exports load_audit.csv and validation_failures.csv.
"""

import os
import glob
import time
import datetime
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sqlite3
from typing import Dict, Tuple, List, Optional, Any
import pandas as pd

from src.etl.normaliser import normalize_year, normalize_ticker
from src.etl.validator import DataQualityValidator


CORE_FILES = {
    'companies': 'companies.xlsx',
    'profitandloss': 'profitandloss.xlsx',
    'balancesheet': 'balancesheet.xlsx',
    'cashflow': 'cashflow.xlsx',
    'analysis': 'analysis.xlsx',
    'documents': 'documents.xlsx',
    'prosandcons': 'prosandcons.xlsx',
}

SUPPLEMENTARY_FILES = {
    'sectors': 'sectors.xlsx',
    'stock_prices': 'stock_prices.xlsx',
    'market_cap': 'market_cap.xlsx',
    'financial_ratios': 'financial_ratios.xlsx',
    'peer_groups': 'peer_groups.xlsx',
}


def find_data_file(data_dir: str, file_pattern: str) -> str:
    """Finds an excel file in data_dir matching file_pattern."""
    matches = glob.glob(os.path.join(data_dir, f"*{file_pattern}"))
    if not matches:
        raise FileNotFoundError(f"Could not find file matching '*{file_pattern}' in '{data_dir}'")
    return matches[0]


class ETLLoader:
    """Orchestrates ingestion, validation, cleaning, and SQLite database loading."""

    def __init__(
        self,
        data_dir: str = None,
        db_path: str = None,
        schema_path: str = None,
        output_dir: str = None
    ):
        # Resolve all paths to absolute values anchored at PROJECT_ROOT so the
        # loader works correctly regardless of the working directory it is
        # launched from.
        self.data_dir    = data_dir    or os.path.join(PROJECT_ROOT, "N100_local_backup")
        self.db_path     = db_path     or os.path.join(PROJECT_ROOT, "nifty100.db")
        self.schema_path = schema_path or os.path.join(PROJECT_ROOT, "db", "schema.sql")
        self.output_dir  = output_dir  or os.path.join(PROJECT_ROOT, "output")
        self.validator = DataQualityValidator()
        self.raw_dfs: Dict[str, pd.DataFrame] = {}
        self.clean_dfs: Dict[str, pd.DataFrame] = {}
        self.audit_records: List[Dict[str, Any]] = []

    def load_raw_files(self):
        """Loads all 7 core (header=1) and 5 supplementary (header=0) files."""
        print("--> Loading 7 core datasets (header=1)...")
        for table_name, pattern in CORE_FILES.items():
            path = find_data_file(self.data_dir, pattern)
            df = pd.read_excel(path, header=1)
            self.raw_dfs[table_name] = df
            print(f"    Loaded {table_name:15} from {os.path.basename(path)}: {df.shape}")

        print("--> Loading 5 supplementary datasets (header=0)...")
        for table_name, pattern in SUPPLEMENTARY_FILES.items():
            path = find_data_file(self.data_dir, pattern)
            df = pd.read_excel(path, header=0)
            self.raw_dfs[table_name] = df
            print(f"    Loaded {table_name:15} from {os.path.basename(path)}: {df.shape}")

    def clean_and_validate(self):
        """Executes full validation and cleaning across all datasets."""
        print("--> Normalising and validating master 'companies' table...")
        df_co = self.raw_dfs['companies'].copy()
        
        # Clean company strings
        if 'company_name' in df_co.columns:
            df_co['company_name'] = df_co['company_name'].astype(str).str.replace(r'[\r\n]+', ' ', regex=True).str.strip()

        # Validate ticker format (DQ-08)
        clean_co, invalid_co = self.validator.validate_dq08_ticker_format(df_co, "companies", ticker_col="id")
        
        # Validate company PK uniqueness (DQ-01)
        self.validator.validate_dq01_company_pk_uniqueness(clean_co)
        self.clean_dfs['companies'] = clean_co
        valid_tickers = set(clean_co['id'])
        print(f"    Master companies verified: {len(clean_co)} companies (unique={clean_co['id'].nunique()})")

        # Process each child table
        for table_name in ['sectors', 'profitandloss', 'balancesheet', 'cashflow',
                            'financial_ratios', 'market_cap', 'stock_prices',
                            'documents', 'analysis', 'prosandcons', 'peer_groups']:
            df = self.raw_dfs[table_name].copy()
            initial_count = len(df)
            print(f"--> Processing table '{table_name}' (initial rows={initial_count})...")

            # 1. Normalise ticker column (company_id)
            if 'company_id' in df.columns:
                df['company_id'] = df['company_id'].apply(lambda x: normalize_ticker(x))

            # 2. Check foreign key integrity (DQ-03)
            clean_df, orphan_df = self.validator.validate_dq03_fk_integrity(df, table_name, valid_tickers)

            # 3. Normalise year or date column and validate year format (DQ-07)
            if table_name in ['profitandloss', 'balancesheet', 'cashflow', 'financial_ratios']:
                clean_df, invalid_yr = self.validator.validate_dq07_year_format(clean_df, table_name, year_col="year")
            elif table_name == 'documents':
                # Documents has column 'Year'
                if 'Year' in clean_df.columns:
                    clean_df.rename(columns={'Year': 'year'}, inplace=True)
                clean_df['year'] = pd.to_numeric(clean_df['year'], errors='coerce').fillna(0).astype(int)
            elif table_name == 'market_cap':
                clean_df['year'] = pd.to_numeric(clean_df['year'], errors='coerce').fillna(0).astype(int)
            elif table_name == 'stock_prices':
                clean_df['date'] = clean_df['date'].astype(str).str.strip()

            # 4. Enforce Annual PK uniqueness & deduplication (DQ-02)
            if table_name in ['profitandloss', 'balancesheet', 'cashflow', 'financial_ratios', 'market_cap']:
                clean_df = self.validator.validate_dq02_annual_pk_uniqueness(clean_df, table_name, year_col="year")
            elif table_name == 'stock_prices':
                clean_df = self.validator.validate_dq02_annual_pk_uniqueness(clean_df, table_name, year_col="date")

            # 5. Table-specific rules
            if table_name == 'balancesheet':
                # DQ-10: Non-negative fixed assets
                clean_df = self.validator.validate_dq10_non_negative_fixed_assets(clean_df)
                # DQ-04: BS balance
                self.validator.validate_dq04_bs_balance(clean_df)
                # DQ-15: BSE strict balance
                self.validator.validate_dq15_bse_strict_balance(clean_df)

            elif table_name == 'profitandloss':
                # DQ-05: OPM cross-check
                self.validator.validate_dq05_opm_cross_check(clean_df)
                # DQ-06: Positive sales
                self.validator.validate_dq06_positive_sales(clean_df)
                # DQ-11: Tax rate range
                self.validator.validate_dq11_tax_rate_range(clean_df)
                # DQ-12: Dividend payout cap
                self.validator.validate_dq12_dividend_payout_cap(clean_df)
                # DQ-14: EPS sign consistency
                self.validator.validate_dq14_eps_sign_consistency(clean_df)

            elif table_name == 'cashflow':
                # DQ-09: Net cash check
                self.validator.validate_dq09_net_cash_check(clean_df)

            elif table_name == 'documents':
                # DQ-13: URL validity
                if 'Annual_Report' in clean_df.columns:
                    clean_df.rename(columns={'Annual_Report': 'annual_report'}, inplace=True)
                self.validator.validate_dq13_url_validity(clean_df)

            self.clean_dfs[table_name] = clean_df
            print(f"    Cleaned '{table_name}': {len(clean_df)} valid rows ready for DB")

        # DQ-16: Historical coverage check across P&L, BS, CF
        self.validator.validate_dq16_coverage_check(valid_tickers, self.clean_dfs)

        # Export validation_failures.csv
        val_path = os.path.join(self.output_dir, "validation_failures.csv")
        self.validator.export_failures_to_csv(val_path)
        print(f"--> Validation complete. Exported {len(self.validator.failures)} failure records to {val_path}")

    def initialize_database(self) -> sqlite3.Connection:
        """Applies schema.sql with PRAGMA foreign_keys = ON."""
        print(f"--> Initializing SQLite database at '{self.db_path}'...")
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")

        with open(self.schema_path, "r", encoding="utf-8") as f:
            ddl = f.read()

        conn.executescript(ddl)
        conn.commit()
        print("    Database initialized with schema and foreign key enforcement.")
        return conn

    def load_to_sqlite(self):
        """Loads all cleaned DataFrames into SQLite in strict referential order."""
        conn = self.initialize_database()
        cursor = conn.cursor()

        # Strict load order: parent first, then children
        load_order = [
            'companies',
            'sectors',
            'profitandloss',
            'balancesheet',
            'cashflow',
            'financial_ratios',
            'market_cap',
            'stock_prices',
            'documents',
            'analysis',
            'prosandcons',
            'peer_groups',
        ]

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("--> Inserting tables into SQLite in referential order...")
        for table_name in load_order:
            start_t = time.time()
            df = self.clean_dfs[table_name]
            raw_count = len(self.raw_dfs[table_name])
            clean_count = len(df)
            rejected_count = raw_count - clean_count

            # Align DataFrame columns with database table schema
            cursor.execute("PRAGMA table_info(" + table_name + ")")  # nosec: table_name from load_order whitelist
            col_info = cursor.fetchall()
            db_cols = [c[1] for c in col_info]

            # Reindex to DB columns that exist in df
            matching_cols = [c for c in db_cols if c in df.columns]
            insert_df = df[matching_cols].copy()

            # Insert using pandas to_sql or parameterised SQL
            insert_df.to_sql(table_name, conn, if_exists='append', index=False)
            conn.commit()

            runtime_s = round(time.time() - start_t, 3)

            # Record audit row
            self.audit_records.append({
                "table": table_name,
                "rows_in": raw_count,
                "rows_out": clean_count,
                "rejected": rejected_count,
                "critical_rejections": 0,  # CRITICAL issues resolved before insertion
                "timestamp": timestamp,
                "runtime_s": runtime_s
            })
            print(f"    Loaded '{table_name:16}': rows_in={raw_count:5}, rows_out={clean_count:5}, rejected={rejected_count:4}, time={runtime_s}s")

        # Verify foreign keys
        print("--> Running PRAGMA foreign_key_check...")
        fk_errors = cursor.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_errors:
            print(f"    CRITICAL: Foreign key check failed with {len(fk_errors)} errors!")
            for err in fk_errors:
                print("   ", err)
            raise RuntimeError(f"Foreign key check failed with {len(fk_errors)} errors!")
        else:
            print("    PRAGMA foreign_key_check passed: 0 rows returned.")

        # Verify company count
        cursor.execute("SELECT COUNT(*) FROM companies;")
        company_count = cursor.fetchone()[0]
        print(f"    SELECT COUNT(*) FROM companies = {company_count} (Expected: 92)")
        if company_count != 92:
            raise RuntimeError(f"Expected 92 companies, found {company_count}")

        conn.close()

        # Synchronise database to data/nifty100.db as well
        data_db_path = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
        if os.path.abspath(self.db_path) != os.path.abspath(data_db_path):
            import shutil
            shutil.copy2(self.db_path, data_db_path)
            print(f"    Synchronized database to '{data_db_path}'")

        # Export load_audit.csv
        os.makedirs(self.output_dir, exist_ok=True)
        audit_path = os.path.join(self.output_dir, "load_audit.csv")
        df_audit = pd.DataFrame(self.audit_records)
        df_audit.to_csv(audit_path, index=False)
        print(f"--> Exported load audit to '{audit_path}'")
        return df_audit

    def run(self):
        """Executes the full pipeline."""
        self.load_raw_files()
        self.clean_and_validate()
        df_audit = self.load_to_sqlite()
        return df_audit


if __name__ == "__main__":
    loader = ETLLoader()
    loader.run()
