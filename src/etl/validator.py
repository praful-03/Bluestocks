"""
Schema Validator for Nifty 100 Financial Intelligence Platform.
Implements the 16 Data Quality (DQ) rules (DQ-01 to DQ-16) and generates validation_failures.csv.
"""

import os
import sys
import re
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.etl.normaliser import normalize_year, normalize_ticker


class DataQualityValidator:
    """
    Validates datasets against the 16 platform Data Quality (DQ) rules.
    Collects validation violations and outputs validation_failures.csv.
    """

    def __init__(self):
        self.failures: List[Dict[str, Any]] = []

    def log_failure(
        self,
        rule_id: str,
        rule_name: str,
        table: str,
        company_id: Optional[str],
        year: Optional[str],
        field: str,
        issue: str,
        severity: str
    ):
        """Records a DQ rule violation."""
        self.failures.append({
            "rule_id": rule_id,
            "rule_name": rule_name,
            "table": table,
            "company_id": str(company_id) if company_id is not None else "",
            "year": str(year) if year is not None else "",
            "field": field,
            "issue": issue,
            "severity": severity
        })

    def validate_dq01_company_pk_uniqueness(self, df_companies: pd.DataFrame) -> bool:
        """
        DQ-01: Company PK Uniqueness (CRITICAL)
        Condition: len(companies) == companies.id.nunique()
        """
        is_unique = len(df_companies) == df_companies['id'].nunique()
        if not is_unique:
            dups = df_companies[df_companies.duplicated(subset=['id'], keep=False)]
            for _, row in dups.iterrows():
                self.log_failure(
                    rule_id="DQ-01",
                    rule_name="Company PK Uniqueness",
                    table="companies",
                    company_id=row.get('id'),
                    year=None,
                    field="id",
                    issue=f"Duplicate company primary key: {row.get('id')}",
                    severity="CRITICAL"
                )
        return is_unique

    def validate_dq02_annual_pk_uniqueness(
        self,
        df: pd.DataFrame,
        table_name: str,
        year_col: str = "year"
    ) -> pd.DataFrame:
        """
        DQ-02: Annual PK Uniqueness (CRITICAL)
        Condition: No duplicate (company_id, year) in time-series tables.
        Action: Deduplicate: keep last occurrence. Log all duplicates.
        """
        if 'company_id' not in df.columns or year_col not in df.columns:
            return df

        dups_mask = df.duplicated(subset=['company_id', year_col], keep='last')
        dup_rows = df[df.duplicated(subset=['company_id', year_col], keep=False)]

        for _, row in dup_rows.iterrows():
            self.log_failure(
                rule_id="DQ-02",
                rule_name="Annual PK Uniqueness",
                table=table_name,
                company_id=row.get('company_id'),
                year=row.get(year_col),
                field=f"company_id, {year_col}",
                issue=f"Duplicate primary key composite ({row.get('company_id')}, {row.get(year_col)}) in {table_name}",
                severity="CRITICAL"
            )

        # Deduplicate: keep last occurrence
        deduped_df = df.drop_duplicates(subset=['company_id', year_col], keep='last').copy()
        return deduped_df

    def validate_dq03_fk_integrity(
        self,
        df: pd.DataFrame,
        table_name: str,
        valid_tickers: set
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        DQ-03: FK Integrity (CRITICAL)
        Condition: All company_id in child tables exist in companies.id.
        Action: Reject orphan rows. Log to validation_failures.csv.
        Returns: (clean_df, orphan_df)
        """
        if 'company_id' not in df.columns:
            return df, pd.DataFrame()

        is_valid = df['company_id'].isin(valid_tickers)
        orphan_df = df[~is_valid].copy()
        clean_df = df[is_valid].copy()

        for _, row in orphan_df.iterrows():
            self.log_failure(
                rule_id="DQ-03",
                rule_name="FK Integrity",
                table=table_name,
                company_id=row.get('company_id'),
                year=row.get('year') or row.get('Year') or row.get('date'),
                field="company_id",
                issue=f"Foreign key violation: '{row.get('company_id')}' does not exist in companies.id",
                severity="CRITICAL"
            )

        return clean_df, orphan_df

    def validate_dq04_bs_balance(self, df_bs: pd.DataFrame):
        """
        DQ-04: Balance Sheet Balance (WARNING)
        Condition: |total_assets - total_liabilities| / total_assets < 0.01
        """
        if 'total_assets' not in df_bs.columns or 'total_liabilities' not in df_bs.columns:
            return

        for _, row in df_bs.iterrows():
            assets = row.get('total_assets')
            liabs = row.get('total_liabilities')
            if pd.notna(assets) and pd.notna(liabs) and assets > 0:
                diff_pct = abs(assets - liabs) / assets
                if diff_pct >= 0.01:
                    self.log_failure(
                        rule_id="DQ-04",
                        rule_name="Balance Sheet Balance",
                        table="balancesheet",
                        company_id=row.get('company_id'),
                        year=row.get('year'),
                        field="total_assets, total_liabilities",
                        issue=f"Balance sheet mismatch: assets={assets}, liabilities={liabs}, diff={diff_pct:.2%}",
                        severity="WARNING"
                    )

    def validate_dq05_opm_cross_check(self, df_pl: pd.DataFrame):
        """
        DQ-05: OPM Cross-Check (WARNING)
        Condition: |opm_percentage - (op_profit / sales * 100)| < 1.0
        """
        required = {'opm_percentage', 'operating_profit', 'sales'}
        if not required.issubset(df_pl.columns):
            return

        for _, row in df_pl.iterrows():
            opm = row.get('opm_percentage')
            op = row.get('operating_profit')
            sales = row.get('sales')
            if pd.notna(opm) and pd.notna(op) and pd.notna(sales) and sales > 0:
                calc_opm = (op / sales) * 100.0
                if abs(opm - calc_opm) >= 1.0:
                    self.log_failure(
                        rule_id="DQ-05",
                        rule_name="OPM Cross-Check",
                        table="profitandloss",
                        company_id=row.get('company_id'),
                        year=row.get('year'),
                        field="opm_percentage",
                        issue=f"OPM mismatch: reported={opm}%, computed={calc_opm:.2f}%",
                        severity="WARNING"
                    )

    def validate_dq06_positive_sales(self, df_pl: pd.DataFrame, bank_tickers: Optional[set] = None):
        """
        DQ-06: Positive Sales (WARNING)
        Condition: sales > 0 for all non-bank companies.
        """
        if 'sales' not in df_pl.columns:
            return

        banks = bank_tickers or set()
        for _, row in df_pl.iterrows():
            cid = row.get('company_id')
            if cid in banks:
                continue
            sales = row.get('sales')
            if pd.notna(sales) and sales <= 0:
                self.log_failure(
                    rule_id="DQ-06",
                    rule_name="Positive Sales",
                    table="profitandloss",
                    company_id=cid,
                    year=row.get('year'),
                    field="sales",
                    issue=f"Non-positive sales reported for non-bank company: {sales}",
                    severity="WARNING"
                )

    def validate_dq07_year_format(self, df: pd.DataFrame, table_name: str, year_col: str = "year") -> Tuple[pd.DataFrame, pd.DataFrame]:
        r"""
        DQ-07: Year Format (CRITICAL)
        Condition: After normalize_year(), all values match r'^\d{4}-\d{2}$'
        Action: Reject row if unparseable. Log raw value.
        Returns: (valid_df, invalid_df)
        """
        if year_col not in df.columns:
            return df, pd.DataFrame()

        valid_rows = []
        invalid_rows = []

        year_pattern = re.compile(r'^\d{4}-\d{2}$')

        for idx, row in df.iterrows():
            raw_yr = row[year_col]
            norm_yr = normalize_year(raw_yr)
            if norm_yr and norm_yr != "PARSE_ERROR" and year_pattern.match(norm_yr):
                row_copy = row.copy()
                row_copy[year_col] = norm_yr
                valid_rows.append(row_copy)
            else:
                self.log_failure(
                    rule_id="DQ-07",
                    rule_name="Year Format",
                    table=table_name,
                    company_id=row.get('company_id'),
                    year=raw_yr,
                    field=year_col,
                    issue=f"Unparseable year format: '{raw_yr}' (normalised='{norm_yr}')",
                    severity="CRITICAL"
                )
                invalid_rows.append(row)

        valid_df = pd.DataFrame(valid_rows, columns=df.columns) if valid_rows else pd.DataFrame(columns=df.columns)
        invalid_df = pd.DataFrame(invalid_rows, columns=df.columns) if invalid_rows else pd.DataFrame(columns=df.columns)
        return valid_df, invalid_df

    def validate_dq08_ticker_format(self, df: pd.DataFrame, table_name: str, ticker_col: str = "id") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        DQ-08: Ticker Format (CRITICAL)
        Condition: company_id = company_id.strip().upper(). Length: 2–12 chars.
        Action: Normalise silently. If length out of range or invalid, reject.
        """
        if ticker_col not in df.columns:
            return df, pd.DataFrame()

        valid_rows = []
        invalid_rows = []

        for _, row in df.iterrows():
            raw_ticker = row[ticker_col]
            norm_ticker = normalize_ticker(raw_ticker)
            if norm_ticker is not None:
                row_copy = row.copy()
                row_copy[ticker_col] = norm_ticker
                valid_rows.append(row_copy)
            else:
                self.log_failure(
                    rule_id="DQ-08",
                    rule_name="Ticker Format",
                    table=table_name,
                    company_id=raw_ticker,
                    year=row.get('year') or row.get('Year') or row.get('date'),
                    field=ticker_col,
                    issue=f"Invalid ticker format or length out of range [2, 12]: '{raw_ticker}'",
                    severity="CRITICAL"
                )
                invalid_rows.append(row)

        valid_df = pd.DataFrame(valid_rows, columns=df.columns) if valid_rows else pd.DataFrame(columns=df.columns)
        invalid_df = pd.DataFrame(invalid_rows, columns=df.columns) if invalid_rows else pd.DataFrame(columns=df.columns)
        return valid_df, invalid_df

    def validate_dq09_net_cash_check(self, df_cf: pd.DataFrame):
        """
        DQ-09: Net Cash Check (WARNING)
        Condition: |net_cash_flow - (CFO + CFI + CFF)| <= 10 (Cr tolerance)
        """
        cols = {'operating_activity', 'investing_activity', 'financing_activity', 'net_cash_flow'}
        if not cols.issubset(df_cf.columns):
            return

        for _, row in df_cf.iterrows():
            cfo = row.get('operating_activity')
            cfi = row.get('investing_activity')
            cff = row.get('financing_activity')
            ncf = row.get('net_cash_flow')
            if all(pd.notna(x) for x in [cfo, cfi, cff, ncf]):
                sum_cf = cfo + cfi + cff
                diff = abs(ncf - sum_cf)
                if diff > 10.0:
                    self.log_failure(
                        rule_id="DQ-09",
                        rule_name="Net Cash Check",
                        table="cashflow",
                        company_id=row.get('company_id'),
                        year=row.get('year'),
                        field="net_cash_flow",
                        issue=f"Cash flow components sum mismatch: reported={ncf}, sum={sum_cf}, diff={diff:.2f}",
                        severity="WARNING"
                    )

    def validate_dq10_non_negative_fixed_assets(self, df_bs: pd.DataFrame) -> pd.DataFrame:
        """
        DQ-10: Non-Negative Fixed Assets (WARNING)
        Condition: fixed_assets >= 0
        Action: Negative fixed_assets -> coerce to 0 and log.
        """
        if 'fixed_assets' not in df_bs.columns:
            return df_bs

        df_out = df_bs.copy()
        for idx, row in df_out.iterrows():
            fa = row.get('fixed_assets')
            if pd.notna(fa) and fa < 0:
                self.log_failure(
                    rule_id="DQ-10",
                    rule_name="Non-Negative Fixed Assets",
                    table="balancesheet",
                    company_id=row.get('company_id'),
                    year=row.get('year'),
                    field="fixed_assets",
                    issue=f"Negative fixed assets coerced to 0: {fa}",
                    severity="WARNING"
                )
                df_out.at[idx, 'fixed_assets'] = 0.0

        return df_out

    def validate_dq11_tax_rate_range(self, df_pl: pd.DataFrame):
        """
        DQ-11: Tax Rate Range (WARNING)
        Condition: 0 <= tax_percentage <= 60
        """
        if 'tax_percentage' not in df_pl.columns:
            return

        for _, row in df_pl.iterrows():
            tax = row.get('tax_percentage')
            if pd.notna(tax) and (tax < 0 or tax > 60):
                self.log_failure(
                    rule_id="DQ-11",
                    rule_name="Tax Rate Range",
                    table="profitandloss",
                    company_id=row.get('company_id'),
                    year=row.get('year'),
                    field="tax_percentage",
                    issue=f"Tax rate out of standard range [0, 60]: {tax}%",
                    severity="WARNING"
                )

    def validate_dq12_dividend_payout_cap(self, df_pl: pd.DataFrame):
        """
        DQ-12: Dividend Payout Cap (WARNING)
        Condition: dividend_payout <= 200 (pct)
        """
        if 'dividend_payout' not in df_pl.columns:
            return

        for _, row in df_pl.iterrows():
            payout = row.get('dividend_payout')
            if pd.notna(payout) and payout > 200:
                self.log_failure(
                    rule_id="DQ-12",
                    rule_name="Dividend Payout Cap",
                    table="profitandloss",
                    company_id=row.get('company_id'),
                    year=row.get('year'),
                    field="dividend_payout",
                    issue=f"Dividend payout exceeds cap (>200%): {payout}%",
                    severity="WARNING"
                )

    def validate_dq13_url_validity(self, df_doc: pd.DataFrame):
        """
        DQ-13: URL Validity (documents) (WARNING)
        Condition: Annual_Report URL is well-formed.
        """
        if 'Annual_Report' not in df_doc.columns:
            return

        for _, row in df_doc.iterrows():
            url = row.get('Annual_Report')
            if pd.isna(url) or not str(url).startswith(('http://', 'https://')):
                self.log_failure(
                    rule_id="DQ-13",
                    rule_name="URL Validity",
                    table="documents",
                    company_id=row.get('company_id'),
                    year=row.get('Year') or row.get('year'),
                    field="Annual_Report",
                    issue=f"Malformed or missing Annual Report URL: {url}",
                    severity="WARNING"
                )

    def validate_dq14_eps_sign_consistency(self, df_pl: pd.DataFrame):
        """
        DQ-14: EPS Sign Consistency (WARNING)
        Condition: eps > 0 if net_profit > 0
        """
        if 'eps' not in df_pl.columns or 'net_profit' not in df_pl.columns:
            return

        for _, row in df_pl.iterrows():
            eps = row.get('eps')
            pat = row.get('net_profit')
            if pd.notna(eps) and pd.notna(pat):
                if pat > 0 and eps <= 0:
                    self.log_failure(
                        rule_id="DQ-14",
                        rule_name="EPS Sign Consistency",
                        table="profitandloss",
                        company_id=row.get('company_id'),
                        year=row.get('year'),
                        field="eps",
                        issue=f"EPS sign inconsistency: net_profit={pat} > 0 but eps={eps} <= 0",
                        severity="WARNING"
                    )

    def validate_dq15_bse_strict_balance(self, df_bs: pd.DataFrame) -> int:
        """
        DQ-15: BSE/ASE Balance (ext.) (INFO)
        Condition: total_liabilities == total_assets (strict)
        """
        if 'total_assets' not in df_bs.columns or 'total_liabilities' not in df_bs.columns:
            return 0

        mismatches = 0
        for _, row in df_bs.iterrows():
            assets = row.get('total_assets')
            liabs = row.get('total_liabilities')
            if pd.notna(assets) and pd.notna(liabs) and assets != liabs:
                mismatches += 1
                self.log_failure(
                    rule_id="DQ-15",
                    rule_name="BSE Strict Balance",
                    table="balancesheet",
                    company_id=row.get('company_id'),
                    year=row.get('year'),
                    field="total_assets, total_liabilities",
                    issue=f"Strict balance difference: assets={assets} != liabilities={liabs}",
                    severity="INFO"
                )
        return mismatches

    def validate_dq16_coverage_check(
        self,
        valid_tickers: set,
        dfs_by_table: Dict[str, pd.DataFrame]
    ):
        """
        DQ-16: Coverage Check (WARNING)
        Condition: Each company has >= 5 years of P&L, BS, CF records.
        """
        for tbl in ['profitandloss', 'balancesheet', 'cashflow']:
            df = dfs_by_table.get(tbl)
            if df is None or 'company_id' not in df.columns:
                continue

            counts = df.groupby('company_id').size()
            for ticker in valid_tickers:
                cnt = counts.get(ticker, 0)
                if cnt < 5:
                    self.log_failure(
                        rule_id="DQ-16",
                        rule_name="Coverage Check",
                        table=tbl,
                        company_id=ticker,
                        year=None,
                        field="year",
                        issue=f"Insufficient historical coverage in {tbl}: {cnt} years (minimum required: 5)",
                        severity="WARNING"
                    )

    def export_failures_to_csv(self, filepath: str = "output/validation_failures.csv"):
        """Saves all logged DQ failures to a CSV file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        cols = ["rule_id", "rule_name", "table", "company_id", "year", "field", "issue", "severity"]
        df_failures = pd.DataFrame(self.failures, columns=cols)
        df_failures.to_csv(filepath, index=False)
        return df_failures
