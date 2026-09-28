"""
ETL Normalisation Module for Nifty 100 Financial Intelligence Platform.
Provides functions to normalise financial year strings and company ticker identifiers.
"""

import re
import datetime
from typing import Optional, Union, Any
import pandas as pd


MONTH_MAP = {
    'JAN': '01', 'JANUARY': '01',
    'FEB': '02', 'FEBRUARY': '02',
    'MAR': '03', 'MARCH': '03',
    'APR': '04', 'APRIL': '04',
    'MAY': '05',
    'JUN': '06', 'JUNE': '06',
    'JUL': '07', 'JULY': '07',
    'AUG': '08', 'AUGUST': '08',
    'SEP': '09', 'SEPT': '09', 'SEPTEMBER': '09',
    'OCT': '10', 'OCTOBER': '10',
    'NOV': '11', 'NOVEMBER': '11',
    'DEC': '12', 'DECEMBER': '12'
}


def normalize_year(val: Any, strict: bool = False) -> Optional[str]:
    """
    Standardises financial year representations to the 'YYYY-MM' format.

    Supported patterns:
      - 'YYYY-MM' -> 'YYYY-MM' (already normalised)
      - 'Mar-23', 'Mar 23', 'March-2023', 'Dec 2012', 'Sep 2024'
      - 'FY23', 'FY 2023', 'FY-24'
      - Integer/float year: 2023, '2023' -> '2023-03' (assumes March FY close)
      - Datetime/Timestamp objects -> 'YYYY-MM'
      - Extended strings: 'Mar 2023 15', 'Mar 2016 9m' -> '2023-03', '2016-03'

    Unparseable inputs (e.g., 'TTM', 'garbage', empty, NaN) return 'PARSE_ERROR'
    (or raise ValueError if strict=True).
    """
    if val is None or pd.isna(val):
        if strict:
            raise ValueError("Year value is None or NaN")
        return "PARSE_ERROR"

    if isinstance(val, (datetime.date, datetime.datetime, pd.Timestamp)):
        return val.strftime('%Y-%m')

    # Convert to string and clean
    raw = str(val).strip()
    if not raw:
        if strict:
            raise ValueError("Year string is empty")
        return "PARSE_ERROR"

    # Already YYYY-MM
    if re.match(r'^\d{4}-\d{2}$', raw):
        return raw

    # Explicitly reject TTM or non-date tokens
    if raw.upper() == 'TTM':
        if strict:
            raise ValueError("TTM is not an annual calendar/fiscal year")
        return "PARSE_ERROR"

    # Check for float like 2024.0 or 2024.5
    try:
        f_val = float(raw)
        if f_val.is_integer() or abs(f_val - round(f_val)) < 1e-4:
            yr = int(round(f_val))
            if 1900 <= yr <= 2100:
                return f"{yr:04d}-03"
        elif abs(f_val - (int(f_val) + 0.5)) < 1e-4:
            # 2024.5 represents semi-annual / mid-year (September close)
            return f"{int(f_val):04d}-09"
    except (ValueError, OverflowError):
        pass  # non-numeric string — continue to pattern matching

    # FY prefix: FY23, FY 2023, FY-24
    fy_match = re.match(r'^FY[\s\-]*(\d{2,4})$', raw, re.IGNORECASE)
    if fy_match:
        yr_num = int(fy_match.group(1))
        if yr_num < 100:
            yr_num = 2000 + yr_num if yr_num < 70 else 1900 + yr_num
        return f"{yr_num:04d}-03"

    # 4-digit year only: e.g. '2023'
    if re.match(r'^\d{4}$', raw):
        yr_num = int(raw)
        if 1900 <= yr_num <= 2100:
            return f"{yr_num:04d}-03"

    # Month and Year combination e.g. 'Mar-23', 'Dec 2012', 'March-2023', 'Mar 2023 15'
    # Match month token followed or preceded by year digits
    month_pattern = r'([A-Za-z]{3,9})[\s\-_/]*(\d{2,4})'
    m = re.search(month_pattern, raw)
    if m:
        month_str = m.group(1).upper()
        if month_str in MONTH_MAP:
            mm = MONTH_MAP[month_str]
            yr_num = int(m.group(2))
            if yr_num < 100:
                yr_num = 2000 + yr_num if yr_num < 70 else 1900 + yr_num
            return f"{yr_num:04d}-{mm}"

    # Year followed by month e.g. '2023-Mar', '2023 Dec'
    m_rev = re.search(r'(\d{4})[\s\-_/]*([A-Za-z]{3,9})', raw)
    if m_rev:
        month_str = m_rev.group(2).upper()
        if month_str in MONTH_MAP:
            mm = MONTH_MAP[month_str]
            yr_num = int(m_rev.group(1))
            return f"{yr_num:04d}-{mm}"

    if strict:
        raise ValueError(f"Unable to parse year string: '{val}'")
    return "PARSE_ERROR"


def normalize_ticker(val: Any, strict: bool = False) -> Optional[str]:
    """
    Normalises NSE company tickers:
      - Strips leading and trailing whitespace
      - Converts to uppercase
      - Preserves valid punctuation (hyphens e.g. 'BAJAJ-AUTO', ampersands e.g. 'M&M')
      - Validates ticker length between 2 and 12 characters

    Returns normalised ticker string, or None if invalid (or raises ValueError if strict=True).
    """
    if val is None or pd.isna(val):
        if strict:
            raise ValueError("Ticker value is None or NaN")
        return None

    ticker = str(val).strip().upper()

    if not ticker:
        if strict:
            raise ValueError("Ticker string is empty")
        return None

    # Length check: 2 to 12 characters
    if not (2 <= len(ticker) <= 12):
        if strict:
            raise ValueError(f"Ticker '{ticker}' length {len(ticker)} out of range [2, 12]")
        return None

    # Valid ticker characters: uppercase alphanumeric, hyphen, and ampersand
    if not re.match(r'^[A-Z0-9&\-]+$', ticker):
        if strict:
            raise ValueError(f"Ticker '{ticker}' contains invalid characters")
        return None
    return ticker


if __name__ == "__main__":
    print("=" * 60)
    print("NIFTY 100 ETL NORMALISER DEMO & SELF-TEST")
    print("=" * 60)
    
    sample_years = [
        "Mar-23", "Mar 23", "March-2023", 2023, "2023", "FY23", "FY 2024",
        "Dec-22", "Dec 2012", "Jun-23", "Sep 2024", "Mar 2023 15", "Mar 2016 9m",
        "2023-03", "TTM", "invalid_year"
    ]
    print("\n--- Year Normalisation Samples (normalize_year) ---")
    for yr in sample_years:
        res = normalize_year(yr)
        status = "PASSED" if res != "PARSE_ERROR" else "FLAGGED (PARSE_ERROR)"
        print(f"  {str(yr):<16} -> {res:<12} [{status}]")
        
    sample_tickers = [
        "  TCS  ", "tcs", "BAJAJ-AUTO", "M&M", "bajaj-auto", "INFY", "LT",
        "A", "VERYLONGTICKERNAME", "INVALID@TICKER"
    ]
    print("\n--- Ticker Normalisation Samples (normalize_ticker) ---")
    for tk in sample_tickers:
        res = normalize_ticker(tk)
        status = f"PASSED ({res})" if res is not None else "REJECTED (Invalid)"
        print(f"  {repr(tk):<22} -> {status}")
        
    print("\nTo run the full 35+ test suite, run:")
    print("  pytest tests/etl/test_normalise.py -v")
    print("=" * 60)
