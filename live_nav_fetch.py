"""
live_nav_fetch.py
=================
Fetches live NAV data from mfapi.in for selected mutual fund schemes.
Saves each scheme's historical NAV as a CSV in data/raw/.

Schemes fetched:
  - HDFC Top 100 Direct (125497)
  - SBI Bluechip (119551)
  - ICICI Bluechip (120503)
  - Nippon Large Cap (118632)
  - Axis Bluechip (119092)
  - Kotak Bluechip (120841)
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_URL = "https://api.mfapi.in/mf/{code}"
RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")

SCHEMES = {
    125497: "HDFC_Top_100_Direct",
    119551: "SBI_Bluechip",
    120503: "ICICI_Bluechip",
    118632: "Nippon_Large_Cap",
    119092: "Axis_Bluechip",
    120841: "Kotak_Bluechip",
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def fetch_nav(scheme_code: int, scheme_name: str) -> pd.DataFrame | None:
    """Fetch NAV history for a single scheme from mfapi.in."""
    url = BASE_URL.format(code=scheme_code)
    print(f"\n{'─'*60}")
    print(f"  Fetching: {scheme_name} (AMFI {scheme_code})")
    print(f"  URL     : {url}")

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  ✗ Request failed: {exc}")
        return None

    payload = resp.json()

    # Extract meta info
    meta = payload.get("meta", {})
    print(f"  Fund    : {meta.get('fund_house', 'N/A')}")
    print(f"  Scheme  : {meta.get('scheme_name', 'N/A')}")
    print(f"  Type    : {meta.get('scheme_type', 'N/A')} / {meta.get('scheme_category', 'N/A')}")

    # Parse NAV data
    nav_data = payload.get("data", [])
    if not nav_data:
        print("  ✗ No NAV data returned")
        return None

    df = pd.DataFrame(nav_data)
    df.columns = ["date", "nav"]

    # Clean types
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["date", "nav"]).sort_values("date").reset_index(drop=True)
    df["amfi_code"] = scheme_code
    df["scheme_name"] = meta.get("scheme_name", scheme_name)

    print(f"  ✓ {len(df):,} NAV records  |  {df['date'].min():%Y-%m-%d} → {df['date'].max():%Y-%m-%d}")
    print(f"  Latest NAV: ₹{df['nav'].iloc[-1]:,.4f}")

    return df


def save_csv(df: pd.DataFrame, scheme_code: int, scheme_name: str) -> str:
    """Save a DataFrame to data/raw/ and return the file path."""
    os.makedirs(RAW_DIR, exist_ok=True)
    filename = f"live_nav_{scheme_code}_{scheme_name}.csv"
    path = os.path.join(RAW_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  💾 Saved → {path}")
    return path


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  LIVE NAV FETCHER — mfapi.in")
    print(f"  Run at: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 60)

    all_frames = []
    failed = []

    for code, name in SCHEMES.items():
        df = fetch_nav(code, name)
        if df is not None:
            save_csv(df, code, name)
            all_frames.append(df)
        else:
            failed.append((code, name))
        time.sleep(0.5)  # polite rate limiting

    # Combined output
    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combo_path = os.path.join(RAW_DIR, "live_nav_all_schemes.csv")
        combined.to_csv(combo_path, index=False)
        print(f"\n{'─'*60}")
        print(f"  Combined file: {combo_path}")
        print(f"  Total records : {len(combined):,}")
        print(f"  Schemes       : {combined['amfi_code'].nunique()}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  ✓ Fetched : {len(all_frames)}/{len(SCHEMES)} schemes")
    if failed:
        print(f"  ✗ Failed  : {', '.join(f'{n} ({c})' for c, n in failed)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
