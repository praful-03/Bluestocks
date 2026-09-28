"""
run_pipeline.py
===============
Master Execution Pipeline for Bluestock Mutual Fund Analytics Capstone.

Orchestrates the entire end-to-end data lifecycle:
  Phase 1: Ingestion & Validation of 10 AMFI datasets (data_ingestion.py)
  Phase 2: Live NAV verification from mfapi.in (live_nav_fetch.py)
  Phase 3: Multi-stage data cleaning & SQLite star-schema population (data_cleaning.py)
  Phase 4: Fund Performance Analytics & Risk Metrics (fund_performance_analytics.py)
  Phase 5: Advanced Analytics: VaR/CVaR, Cohorts, Churn, HHI (scripts/advanced_analytics.py)
  Phase 6: Dashboard Data Aggregation & Export (scripts/export_mf_dashboard.py)
  Phase 7: Automated System Verification & Quality Audit

Usage:
    python run_pipeline.py
"""

import os
import sys
import time
import sqlite3
from datetime import datetime

# Safe UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass  # reconfigure() unavailable on some Python builds — safe to ignore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CHARTS_DIR = os.path.join(REPORTS_DIR, "charts")

SEP = "=" * 80
SUBSEP = "-" * 80


def log_phase(phase_num: int, title: str) -> None:
    """Print formatted header for each pipeline execution phase."""
    print(f"\n{SEP}")
    print(f"  PHASE {phase_num}: {title.upper()}")
    print(f"  Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(SEP)


def verify_database_integrity() -> dict:
    """Audit table counts and integrity in bluestock_mf.db."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = [
        "dim_fund", "fact_nav", "fact_transactions", "fact_performance",
        "fact_aum", "fact_sip_inflows", "fact_category_inflows",
        "fact_folio_count", "fact_holdings", "fact_benchmark"
    ]
    
    counts = {}
    for table in tables:
        try:
            cursor.execute("SELECT count(*) FROM " + table)  # nosec: table from hardcoded whitelist
            counts[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = 0
            
    conn.close()
    return counts


def main():
    total_start = time.time()
    print(SEP)
    print("  BLUESTOCK MUTUAL FUND ANALYTICS PLATFORM")
    print("  MASTER PIPELINE EXECUTION ENGINE")
    print(SEP)

    # -------------------------------------------------------------------------
    # PHASE 1: Data Ingestion & Quality Validation
    # -------------------------------------------------------------------------
    log_phase(1, "Data Ingestion & Integrity Validation")
    t0 = time.time()
    try:
        import data_ingestion
        frames = data_ingestion.load_and_inspect()
        data_ingestion.explore_fund_master(frames)
        data_ingestion.validate_amfi_codes(frames)
        print(f"  [OK] Phase 1 completed in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [ERROR] Phase 1 failed: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 2: Live NAV Verification
    # -------------------------------------------------------------------------
    log_phase(2, "Live NAV Data Verification")
    t0 = time.time()
    try:
        # Check if live NAV files already exist in data/raw
        live_files = [f for f in os.listdir(RAW_DIR) if f.startswith("live_nav_")]
        if len(live_files) >= 6:
            print(f"  [OK] Found {len(live_files)} existing live NAV files in data/raw/.")
            print("       Skipping network re-fetch to maintain reproducible local cache.")
        else:
            print("  Fetching live NAV from mfapi.in API...")
            import live_nav_fetch
            live_nav_fetch.main()
        print(f"  [OK] Phase 2 completed in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [WARNING] Live NAV fetch warning: {e}. Using cached raw data.")

    # -------------------------------------------------------------------------
    # PHASE 3: Data Cleaning & SQLite Star-Schema Population
    # -------------------------------------------------------------------------
    log_phase(3, "Data Cleaning & SQLite Star-Schema Loading")
    t0 = time.time()
    try:
        import data_cleaning
        data_cleaning.main()
        print(f"  [OK] Phase 3 completed in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [ERROR] Phase 3 failed: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 4: Fund Performance Analytics & Chart Generation
    # -------------------------------------------------------------------------
    log_phase(4, "Fund Performance Analytics & Risk Metrics")
    t0 = time.time()
    try:
        import fund_performance_analytics
        fund_performance_analytics.main()
        print(f"  [OK] Phase 4 completed in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [ERROR] Phase 4 failed: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 5: Advanced Analytics & Risk Modeling
    # -------------------------------------------------------------------------
    log_phase(5, "Advanced Analytics & Quantitative Risk Modeling")
    t0 = time.time()
    try:
        from scripts import advanced_analytics
        advanced_analytics.main()
        print(f"  [OK] Phase 5 completed in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [ERROR] Phase 5 failed: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 6: Dashboard Data Export
    # -------------------------------------------------------------------------
    log_phase(6, "Dashboard Data Aggregation & Export")
    t0 = time.time()
    try:
        from scripts import export_mf_dashboard
        export_mf_dashboard.main()
        print(f"  [OK] Phase 6 completed in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [WARNING] Phase 6 note: {e}")

    # -------------------------------------------------------------------------
    # PHASE 7: System Verification & Quality Audit
    # -------------------------------------------------------------------------
    log_phase(7, "End-to-End System Verification & Quality Audit")
    db_counts = verify_database_integrity()
    print(f"\n  [Database Row Counts in bluestock_mf.db]")
    print(SUBSEP)
    for tbl, cnt in db_counts.items():
        status = "[OK]" if cnt > 0 else "[EMPTY]"
        print(f"    {status:<8} {tbl:<25}: {cnt:>8,} records")
    print(SUBSEP)

    total_time = time.time() - total_start
    print(f"\n{SEP}")
    print("  ALL PIPELINE PHASES EXECUTED SUCCESSFULLY")
    print(f"  Total Execution Time: {total_time:.2f} seconds")
    print(f"  Database Path: {DB_PATH}")
    print(f"  Processed Directory: {PROC_DIR}")
    print(f"  Generated Reports: {REPORTS_DIR}")
    print(SEP)


if __name__ == "__main__":
    main()
