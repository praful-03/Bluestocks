"""
data_ingestion.py
=================
Day 1 — Data Ingestion & Exploration for the Bluestock Mutual Fund Capstone.

This script:
  1. Loads all 10 provided CSV datasets from data/raw/
  2. Prints .shape, .dtypes, .head() for each — flags anomalies
  3. Explores fund_master: unique fund houses, categories, sub-categories, risk grades
  4. Validates AMFI code integrity between fund_master and nav_history
  5. Outputs a data quality summary report to reports/
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── Dataset manifest ──────────────────────────────────────────────────────────
DATASETS = [
    ("01_fund_master.csv",           "Fund Master — scheme metadata"),
    ("02_nav_history.csv",           "NAV History — daily NAV values"),
    ("03_aum_by_fund_house.csv",     "AUM by Fund House — quarterly"),
    ("04_monthly_sip_inflows.csv",   "Monthly SIP Inflows — industry level"),
    ("05_category_inflows.csv",      "Category-wise Net Inflows"),
    ("06_industry_folio_count.csv",  "Industry Folio Count — monthly"),
    ("07_scheme_performance.csv",    "Scheme Performance — return metrics"),
    ("08_investor_transactions.csv", "Investor Transactions — buy/sell/SIP"),
    ("09_portfolio_holdings.csv",    "Portfolio Holdings — stock weights"),
    ("10_benchmark_indices.csv",     "Benchmark Indices — daily close"),
]

# Separator for console output
SEP = "═" * 80


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Load & Inspect All 10 Datasets
# ══════════════════════════════════════════════════════════════════════════════
def load_and_inspect() -> dict[str, pd.DataFrame]:
    """Load every CSV and print shape / dtypes / head. Return dict of DataFrames."""
    frames: dict[str, pd.DataFrame] = {}
    anomalies: list[str] = []

    print(f"\n{SEP}")
    print("  STEP 1 — LOADING & INSPECTING ALL 10 DATASETS")
    print(SEP)

    for filename, description in DATASETS:
        path = os.path.join(RAW_DIR, filename)
        print(f"\n{'─'*80}")
        print(f"  📄 {filename}")
        print(f"     {description}")
        print(f"{'─'*80}")

        if not os.path.exists(path):
            msg = f"  ✗ FILE NOT FOUND: {path}"
            print(msg)
            anomalies.append(msg)
            continue

        df = pd.read_csv(path)
        key = filename.replace(".csv", "")
        frames[key] = df

        # Shape
        print(f"\n  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

        # Dtypes
        print(f"\n  Dtypes:")
        for col, dtype in df.dtypes.items():
            null_count = df[col].isna().sum()
            null_pct = null_count / len(df) * 100
            flag = f"  ⚠ {null_count} nulls ({null_pct:.1f}%)" if null_count > 0 else ""
            print(f"    {col:<30s} {str(dtype):<12s}{flag}")
            if null_pct > 5:
                anomalies.append(f"{filename}: column '{col}' has {null_pct:.1f}% missing values")

        # Head
        print(f"\n  Head (first 5 rows):")
        print(df.head().to_string(index=True, max_colwidth=50))

        # Anomaly checks
        # Check for duplicate rows
        dups = df.duplicated().sum()
        if dups > 0:
            msg = f"{filename}: {dups} duplicate rows found"
            print(f"\n  ⚠ ANOMALY: {msg}")
            anomalies.append(msg)

        # Check for columns that look like dates but aren't parsed
        for col in df.columns:
            if "date" in col.lower() and df[col].dtype == "object":
                msg = f"{filename}: column '{col}' appears to be a date but stored as string (object)"
                print(f"  ⚠ ANOMALY: {msg}")
                anomalies.append(msg)

        # Check for negative values in numeric columns that shouldn't be negative
        for col in df.select_dtypes(include=[np.number]).columns:
            if "nav" in col.lower() or "aum" in col.lower() or "amount" in col.lower():
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    msg = f"{filename}: column '{col}' has {neg_count} negative values"
                    print(f"  ⚠ ANOMALY: {msg}")
                    anomalies.append(msg)

    # Anomaly summary
    print(f"\n{'─'*80}")
    print(f"  ANOMALY SUMMARY: {len(anomalies)} issues found")
    for i, a in enumerate(anomalies, 1):
        print(f"    {i}. {a}")
    print(f"{'─'*80}")

    return frames


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Explore Fund Master
# ══════════════════════════════════════════════════════════════════════════════
def explore_fund_master(frames: dict[str, pd.DataFrame]):
    """Print unique fund houses, categories, sub-categories, risk grades, AMFI codes."""
    print(f"\n{SEP}")
    print("  STEP 2 — FUND MASTER EXPLORATION")
    print(SEP)

    fm = frames.get("01_fund_master")
    if fm is None:
        print("  ✗ fund_master not loaded, skipping exploration")
        return

    # Unique fund houses
    print(f"\n  ┌── Unique Fund Houses ({fm['fund_house'].nunique()}) ──")
    for fh in sorted(fm["fund_house"].unique()):
        count = (fm["fund_house"] == fh).sum()
        print(f"  │   {fh} ({count} schemes)")

    # Categories
    print(f"\n  ├── Categories ({fm['category'].nunique()}) ──")
    for cat in sorted(fm["category"].unique()):
        print(f"  │   • {cat}")

    # Sub-categories
    print(f"\n  ├── Sub-Categories ({fm['sub_category'].nunique()}) ──")
    for sub in sorted(fm["sub_category"].unique()):
        count = (fm["sub_category"] == sub).sum()
        print(f"  │   • {sub} ({count} schemes)")

    # Risk grades
    print(f"\n  ├── Risk Categories ({fm['risk_category'].nunique()}) ──")
    for risk in sorted(fm["risk_category"].unique()):
        count = (fm["risk_category"] == risk).sum()
        print(f"  │   • {risk} ({count} schemes)")

    # AMFI code structure
    print(f"\n  └── AMFI Scheme Code Structure ──")
    codes = fm["amfi_code"].astype(str)
    print(f"      Total codes       : {len(codes)}")
    print(f"      Unique codes      : {codes.nunique()}")
    print(f"      Code length range : {codes.str.len().min()} – {codes.str.len().max()} digits")
    print(f"      Code range        : {fm['amfi_code'].min()} – {fm['amfi_code'].max()}")
    print(f"      All numeric?      : {codes.str.isnumeric().all()}")
    print(f"      Sample codes      : {list(fm['amfi_code'].head(5))}")

    # SEBI category codes
    if "sebi_category_code" in fm.columns:
        print(f"\n      SEBI Category Codes ({fm['sebi_category_code'].nunique()}):")
        for sc in sorted(fm["sebi_category_code"].unique()):
            schemes = fm[fm["sebi_category_code"] == sc]["sub_category"].unique()
            print(f"        {sc} → {', '.join(schemes)}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Validate AMFI Codes
# ══════════════════════════════════════════════════════════════════════════════
def validate_amfi_codes(frames: dict[str, pd.DataFrame]) -> str:
    """Cross-validate AMFI codes between fund_master and nav_history.
    Returns a quality summary string.
    """
    print(f"\n{SEP}")
    print("  STEP 3 — AMFI CODE VALIDATION")
    print(SEP)

    fm = frames.get("01_fund_master")
    nh = frames.get("02_nav_history")

    if fm is None or nh is None:
        msg = "  ✗ Cannot validate — fund_master or nav_history not loaded"
        print(msg)
        return msg

    master_codes = set(fm["amfi_code"].unique())
    nav_codes = set(nh["amfi_code"].unique())

    in_master_not_nav = master_codes - nav_codes
    in_nav_not_master = nav_codes - master_codes
    common = master_codes & nav_codes

    print(f"\n  Fund Master AMFI codes : {len(master_codes)}")
    print(f"  NAV History AMFI codes : {len(nav_codes)}")
    print(f"  Common (matched)       : {len(common)}")
    print(f"  In Master, not in NAV  : {len(in_master_not_nav)}")
    print(f"  In NAV, not in Master  : {len(in_nav_not_master)}")

    if in_master_not_nav:
        print(f"\n  ⚠ Codes in fund_master but MISSING from nav_history:")
        for code in sorted(in_master_not_nav):
            name = fm[fm["amfi_code"] == code]["scheme_name"].values[0]
            print(f"      {code} — {name}")

    if in_nav_not_master:
        print(f"\n  ⚠ Codes in nav_history but MISSING from fund_master:")
        for code in sorted(in_nav_not_master):
            print(f"      {code}")

    # NAV coverage per scheme
    print(f"\n  NAV Coverage per Matched Scheme:")
    for code in sorted(common):
        nav_rows = nh[nh["amfi_code"] == code]
        name = fm[fm["amfi_code"] == code]["scheme_name"].values[0]
        date_range = f"{nav_rows['date'].min()} → {nav_rows['date'].max()}"
        print(f"    {code}  {nav_rows.shape[0]:>6,} records  {date_range}  {name[:50]}")

    # Build quality summary
    match_rate = len(common) / len(master_codes) * 100 if master_codes else 0
    summary_lines = [
        "=" * 60,
        "  DATA QUALITY SUMMARY — Day 1 Ingestion",
        f"  Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "=" * 60,
        "",
        f"  Datasets Loaded           : 10 / 10",
        f"  Total Records (all files) : (see per-file details below)",
        "",
        "  AMFI Code Integrity:",
        f"    Master codes             : {len(master_codes)}",
        f"    NAV history codes        : {len(nav_codes)}",
        f"    Match rate               : {match_rate:.1f}%",
        f"    Unmatched (master→NAV)   : {len(in_master_not_nav)}",
        f"    Unmatched (NAV→master)   : {len(in_nav_not_master)}",
        "",
    ]

    if match_rate == 100 and not in_nav_not_master:
        summary_lines.append("  ✓ RESULT: All AMFI codes are consistent. Data integrity is GOOD.")
    elif match_rate >= 90:
        summary_lines.append("  ⚠ RESULT: Minor mismatches found. Data integrity is ACCEPTABLE.")
    else:
        summary_lines.append("  ✗ RESULT: Significant mismatches. Data integrity needs ATTENTION.")

    summary_lines.append("")
    summary_lines.append("=" * 60)

    summary = "\n".join(summary_lines)
    print(f"\n{summary}")

    return summary


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Generate Report
# ══════════════════════════════════════════════════════════════════════════════
def write_report(frames: dict[str, pd.DataFrame], quality_summary: str):
    """Write a complete data quality report to reports/."""
    report_path = os.path.join(REPORTS_DIR, "day1_data_quality_report.txt")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("BLUESTOCK MF CAPSTONE — DAY 1 DATA QUALITY REPORT\n")
        f.write(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write("=" * 60 + "\n\n")

        # Per-dataset summary
        f.write("PER-DATASET SUMMARY\n")
        f.write("-" * 60 + "\n")
        for key, df in frames.items():
            f.write(f"\n{key}.csv\n")
            f.write(f"  Rows    : {df.shape[0]:,}\n")
            f.write(f"  Columns : {df.shape[1]}\n")
            f.write(f"  Nulls   : {df.isna().sum().sum()}\n")
            f.write(f"  Dupes   : {df.duplicated().sum()}\n")
            mem = df.memory_usage(deep=True).sum() / 1024 / 1024
            f.write(f"  Memory  : {mem:.2f} MB\n")

        f.write("\n\n")
        f.write(quality_summary)

    print(f"\n  📝 Report saved → {report_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{'█'*80}")
    print(f"  BLUESTOCK MF CAPSTONE — DAY 1: DATA INGESTION")
    print(f"  Run at: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'█'*80}")

    # Step 1: Load & inspect
    frames = load_and_inspect()

    if not frames:
        print("\n  ✗ No datasets loaded. Check data/raw/ directory.")
        sys.exit(1)

    # Step 2: Explore fund master
    explore_fund_master(frames)

    # Step 3: Validate AMFI codes
    quality_summary = validate_amfi_codes(frames)

    # Step 4: Write report
    write_report(frames, quality_summary)

    print(f"\n{'█'*80}")
    print(f"  ✓ DAY 1 DATA INGESTION COMPLETE")
    print(f"  Datasets loaded  : {len(frames)}")
    print(f"  Total records    : {sum(df.shape[0] for df in frames.values()):,}")
    print(f"{'█'*80}\n")


if __name__ == "__main__":
    main()
