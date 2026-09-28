"""
Integration tests for ETL Loader and SQLite Database nifty100.db.
Validates row counts, foreign key constraints, table existence, and load audit.
"""

import os
import sys
import sqlite3
import pandas as pd
import pytest

# Ensure project root is on the path regardless of how/where this file is run
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")


@pytest.fixture(scope="module")
def db_conn():
    assert os.path.exists(DB_PATH), f"Database file {DB_PATH} does not exist"
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()


class TestDatabaseIntegrity:
    """Validates Sprint 1 Definition of Done for nifty100.db."""

    def test_companies_row_count(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies;")
        count = cursor.fetchone()[0]
        assert count == 92, f"Expected exactly 92 companies, found {count}"

    def test_pragma_foreign_key_check_zero_errors(self, db_conn):
        cursor = db_conn.cursor()
        errors = cursor.execute("PRAGMA foreign_key_check;").fetchall()
        assert len(errors) == 0, f"Foreign key check returned errors: {errors}"

    def test_all_10_plus_tables_exist(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        expected_tables = {
            'companies', 'profitandloss', 'balancesheet', 'cashflow',
            'analysis', 'documents', 'prosandcons', 'sectors',
            'stock_prices', 'market_cap', 'financial_ratios', 'peer_groups'
        }
        missing = expected_tables - tables
        assert len(missing) == 0, f"Missing expected tables: {missing}"

    def test_stock_prices_row_count(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stock_prices;")
        count = cursor.fetchone()[0]
        assert count == 5520, f"Expected 5520 stock prices, found {count}"

    def test_sectors_row_count(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sectors;")
        count = cursor.fetchone()[0]
        assert count == 92, f"Expected 92 sectors rows, found {count}"

    def test_load_audit_file_exists_and_valid(self):
        audit_path = os.path.join(PROJECT_ROOT, "output", "load_audit.csv")
        assert os.path.exists(audit_path), f"Audit file {audit_path} does not exist"
        df_audit = pd.read_csv(audit_path)
        assert len(df_audit) >= 10, f"Expected at least 10 audited tables, found {len(df_audit)}"
        assert "table" in df_audit.columns
        assert "rows_in" in df_audit.columns
        assert "rows_out" in df_audit.columns
        assert "critical_rejections" in df_audit.columns
        # Zero critical rejections on DB load
        assert (df_audit["critical_rejections"] == 0).all()

    def test_validation_failures_file_exists(self):
        val_path = os.path.join(PROJECT_ROOT, "output", "validation_failures.csv")
        assert os.path.exists(val_path), f"Validation failures file {val_path} does not exist"
        df_val = pd.read_csv(val_path)
        assert len(df_val) > 0, "Expected validation failures to be logged"
        assert {"rule_id", "rule_name", "severity", "company_id"}.issubset(df_val.columns)

    def test_financial_history_coverage_order(self, db_conn):
        cursor = db_conn.cursor()
        # Verify TCS has multi-year financial statement records
        cursor.execute("SELECT COUNT(*) FROM profitandloss WHERE company_id = 'TCS';")
        count = cursor.fetchone()[0]
        assert count >= 10, f"Expected >= 10 years of P&L for TCS, found {count}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
