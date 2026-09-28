"""
Unit tests for ETL normalisation module (normalize_year and normalize_ticker).
Requires at least 20 test cases for normalize_year and 15 test cases for normalize_ticker.
"""

import sys
import os
import pytest
import datetime
import pandas as pd

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)



from src.etl.normaliser import normalize_year, normalize_ticker


# ============================================================================
# 20+ Unit Tests for normalize_year()
# ============================================================================

class TestNormalizeYear:
    """Comprehensive test suite covering 20+ scenarios for normalize_year."""

    def test_01_mar_dash_2digit(self):
        assert normalize_year("Mar-23") == "2023-03"

    def test_02_mar_space_2digit(self):
        assert normalize_year("Mar 23") == "2023-03"

    def test_03_full_month_name(self):
        assert normalize_year("March-2023") == "2023-03"

    def test_04_integer_year(self):
        assert normalize_year(2023) == "2023-03"

    def test_05_string_integer_year(self):
        assert normalize_year("2023") == "2023-03"

    def test_06_fy_short_prefix(self):
        assert normalize_year("FY23") == "2023-03"

    def test_07_fy_spaced_prefix(self):
        assert normalize_year("FY 2023") == "2023-03"

    def test_08_dec_dash_year(self):
        assert normalize_year("Dec-22") == "2022-12"

    def test_09_dec_space_4digit(self):
        assert normalize_year("Dec 2012") == "2012-12"

    def test_10_jun_dash_year(self):
        assert normalize_year("Jun-23") == "2023-06"

    def test_11_already_normalized(self):
        assert normalize_year("2023-03") == "2023-03"

    def test_12_sep_space_year(self):
        assert normalize_year("Sep 2024") == "2024-09"

    def test_13_mar_space_4digit(self):
        assert normalize_year("Mar 2014") == "2014-03"

    def test_14_mar_with_period_number(self):
        assert normalize_year("Mar 2023 15") == "2023-03"

    def test_15_mar_with_interim_indicator(self):
        assert normalize_year("Mar 2016 9m") == "2016-03"

    def test_16_sep_dash_2digit(self):
        assert normalize_year("Sep-11") == "2011-09"

    def test_17_datetime_object(self):
        dt = datetime.date(2021, 3, 31)
        assert normalize_year(dt) == "2021-03"

    def test_18_pandas_timestamp(self):
        ts = pd.Timestamp("2020-12-31")
        assert normalize_year(ts) == "2020-12"

    def test_19_ttm_returns_parse_error(self):
        assert normalize_year("TTM") == "PARSE_ERROR"

    def test_20_garbage_string_returns_parse_error(self):
        assert normalize_year("invalid_year_string") == "PARSE_ERROR"

    def test_21_none_and_na_return_parse_error(self):
        assert normalize_year(None) == "PARSE_ERROR"
        assert normalize_year(pd.NA) == "PARSE_ERROR"

    def test_22_empty_string_returns_parse_error(self):
        assert normalize_year("   ") == "PARSE_ERROR"

    def test_23_strict_mode_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_year("TTM", strict=True)
        with pytest.raises(ValueError):
            normalize_year("random_text", strict=True)


# ============================================================================
# 15+ Unit Tests for normalize_ticker()
# ============================================================================

class TestNormalizeTicker:
    """Comprehensive test suite covering 15+ scenarios for normalize_ticker."""

    def test_01_whitespace_stripping(self):
        assert normalize_ticker("  TCS  ") == "TCS"

    def test_02_lowercase_to_uppercase(self):
        assert normalize_ticker("tcs") == "TCS"

    def test_03_hyphen_preservation(self):
        assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

    def test_04_ampersand_preservation(self):
        assert normalize_ticker("M&M") == "M&M"

    def test_05_mixed_case_with_hyphen(self):
        assert normalize_ticker("  bajaj-auto  ") == "BAJAJ-AUTO"

    def test_06_standard_ticker(self):
        assert normalize_ticker("INFY") == "INFY"

    def test_07_bank_ticker(self):
        assert normalize_ticker("hdfcbank") == "HDFCBANK"

    def test_08_minimum_valid_length_2_chars(self):
        assert normalize_ticker("LT") == "LT"

    def test_09_conglomerate_ticker(self):
        assert normalize_ticker("RELIANCE") == "RELIANCE"

    def test_10_maximum_valid_length_12_chars(self):
        assert normalize_ticker("ABCDEFGHIJKL") == "ABCDEFGHIJKL"

    def test_11_too_short_length_1(self):
        assert normalize_ticker("A") is None

    def test_12_too_long_length_gt_12(self):
        assert normalize_ticker("LONGERTHAN12CHARS") is None

    def test_13_empty_string(self):
        assert normalize_ticker("") is None

    def test_14_whitespace_only(self):
        assert normalize_ticker("    ") is None

    def test_15_none_value(self):
        assert normalize_ticker(None) is None

    def test_16_invalid_characters_dollar_and_at(self):
        assert normalize_ticker("TCS$") is None
        assert normalize_ticker("INFY@1") is None

    def test_17_strict_mode_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_ticker("A", strict=True)
        with pytest.raises(ValueError):
            normalize_ticker("INVALID@TICKER", strict=True)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
