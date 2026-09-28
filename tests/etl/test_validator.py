"""
Unit tests for Schema Validator and 16 Data Quality (DQ) Rules.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.etl.validator import DataQualityValidator


@pytest.fixture
def validator():
    return DataQualityValidator()


class TestDataQualityRules:
    """Validates each of the 16 DQ rules."""

    def test_dq01_company_pk_uniqueness(self, validator):
        # Unique IDs -> pass
        df_valid = pd.DataFrame({"id": ["TCS", "INFY", "HDFCBANK"]})
        assert validator.validate_dq01_company_pk_uniqueness(df_valid) is True
        assert len(validator.failures) == 0

        # Duplicate IDs -> fail & log CRITICAL
        df_invalid = pd.DataFrame({"id": ["TCS", "INFY", "TCS"]})
        assert validator.validate_dq01_company_pk_uniqueness(df_invalid) is False
        assert any(f["rule_id"] == "DQ-01" and f["severity"] == "CRITICAL" for f in validator.failures)

    def test_dq02_annual_pk_uniqueness(self, validator):
        df = pd.DataFrame({
            "company_id": ["TCS", "TCS", "INFY"],
            "year": ["2023-03", "2023-03", "2023-03"],
            "sales": [100, 200, 300]
        })
        deduped = validator.validate_dq02_annual_pk_uniqueness(df, "profitandloss")
        assert len(deduped) == 2
        # Keep last occurrence: TCS sales should be 200
        assert deduped.loc[deduped["company_id"] == "TCS", "sales"].iloc[0] == 200
        assert any(f["rule_id"] == "DQ-02" and f["severity"] == "CRITICAL" for f in validator.failures)

    def test_dq03_fk_integrity(self, validator):
        valid_cids = {"TCS", "INFY"}
        df = pd.DataFrame({
            "company_id": ["TCS", "INFY", "ORPHAN_CO"],
            "year": ["2023-03", "2023-03", "2023-03"]
        })
        clean_df, orphan_df = validator.validate_dq03_fk_integrity(df, "profitandloss", valid_cids)
        assert len(clean_df) == 2
        assert len(orphan_df) == 1
        assert orphan_df["company_id"].iloc[0] == "ORPHAN_CO"
        assert any(f["rule_id"] == "DQ-03" and f["severity"] == "CRITICAL" for f in validator.failures)

    def test_dq04_bs_balance(self, validator):
        # Mismatch > 1%
        df_bs = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "total_assets": [1000.0],
            "total_liabilities": [1020.0]
        })
        validator.validate_dq04_bs_balance(df_bs)
        assert any(f["rule_id"] == "DQ-04" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq05_opm_cross_check(self, validator):
        # Reported 15%, computed 40/200 = 20% -> diff 5% > 1%
        df_pl = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "sales": [200.0],
            "operating_profit": [40.0],
            "opm_percentage": [15.0]
        })
        validator.validate_dq05_opm_cross_check(df_pl)
        assert any(f["rule_id"] == "DQ-05" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq06_positive_sales(self, validator):
        df_pl = pd.DataFrame({
            "company_id": ["TESTCO"],
            "year": ["2023-03"],
            "sales": [0.0]
        })
        validator.validate_dq06_positive_sales(df_pl, bank_tickers=set())
        assert any(f["rule_id"] == "DQ-06" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq07_year_format(self, validator):
        df = pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["Mar-23", "TTM"]
        })
        valid_df, invalid_df = validator.validate_dq07_year_format(df, "profitandloss")
        assert len(valid_df) == 1
        assert valid_df["year"].iloc[0] == "2023-03"
        assert len(invalid_df) == 1
        assert any(f["rule_id"] == "DQ-07" and f["severity"] == "CRITICAL" for f in validator.failures)

    def test_dq08_ticker_format(self, validator):
        df = pd.DataFrame({
            "id": ["TCS", "X", "BAJAJ-AUTO"]
        })
        valid_df, invalid_df = validator.validate_dq08_ticker_format(df, "companies", ticker_col="id")
        assert len(valid_df) == 2
        assert len(invalid_df) == 1
        assert invalid_df["id"].iloc[0] == "X"
        assert any(f["rule_id"] == "DQ-08" and f["severity"] == "CRITICAL" for f in validator.failures)

    def test_dq09_net_cash_check(self, validator):
        # CFO 100, CFI -50, CFF -20 -> sum 30, reported 60 -> diff 30 > 10
        df_cf = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "operating_activity": [100.0],
            "investing_activity": [-50.0],
            "financing_activity": [-20.0],
            "net_cash_flow": [60.0]
        })
        validator.validate_dq09_net_cash_check(df_cf)
        assert any(f["rule_id"] == "DQ-09" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq10_non_negative_fixed_assets(self, validator):
        df_bs = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "fixed_assets": [-25.0]
        })
        clean_bs = validator.validate_dq10_non_negative_fixed_assets(df_bs)
        assert clean_bs["fixed_assets"].iloc[0] == 0.0
        assert any(f["rule_id"] == "DQ-10" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq11_tax_rate_range(self, validator):
        df_pl = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "tax_percentage": [75.0]
        })
        validator.validate_dq11_tax_rate_range(df_pl)
        assert any(f["rule_id"] == "DQ-11" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq12_dividend_payout_cap(self, validator):
        df_pl = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "dividend_payout": [250.0]
        })
        validator.validate_dq12_dividend_payout_cap(df_pl)
        assert any(f["rule_id"] == "DQ-12" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq13_url_validity(self, validator):
        df_doc = pd.DataFrame({
            "company_id": ["TCS"],
            "Year": [2023],
            "Annual_Report": ["ftp://broken/url.pdf"]
        })
        validator.validate_dq13_url_validity(df_doc)
        assert any(f["rule_id"] == "DQ-13" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq14_eps_sign_consistency(self, validator):
        df_pl = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "net_profit": [500.0],
            "eps": [-5.0]
        })
        validator.validate_dq14_eps_sign_consistency(df_pl)
        assert any(f["rule_id"] == "DQ-14" and f["severity"] == "WARNING" for f in validator.failures)

    def test_dq15_bse_strict_balance(self, validator):
        df_bs = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "total_assets": [1000.0],
            "total_liabilities": [1001.0]
        })
        mismatches = validator.validate_dq15_bse_strict_balance(df_bs)
        assert mismatches == 1
        assert any(f["rule_id"] == "DQ-15" and f["severity"] == "INFO" for f in validator.failures)

    def test_dq16_coverage_check(self, validator):
        valid_cids = {"TCS", "NEWCO"}
        dfs = {
            "profitandloss": pd.DataFrame({
                "company_id": ["TCS"] * 6 + ["NEWCO"] * 2,
                "year": ["2018-03", "2019-03", "2020-03", "2021-03", "2022-03", "2023-03", "2022-03", "2023-03"]
            }),
            "balancesheet": pd.DataFrame({
                "company_id": ["TCS"] * 6 + ["NEWCO"] * 2
            }),
            "cashflow": pd.DataFrame({
                "company_id": ["TCS"] * 6 + ["NEWCO"] * 2
            })
        }
        validator.validate_dq16_coverage_check(valid_cids, dfs)
        assert any(f["rule_id"] == "DQ-16" and f["company_id"] == "NEWCO" and f["severity"] == "WARNING" for f in validator.failures)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
