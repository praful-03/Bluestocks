"""
recommender.py
==============
Bluestock Mutual Fund Analytics — Intelligent Fund Recommendation Engine.

Provides rule-based and quantitative risk-profile matching to recommend top
mutual fund schemes based on investor risk tolerance, historical Sharpe ratio,
Sortino ratio, and expense ratio optimization.

Usage:
    python recommender.py --risk Moderate
    python recommender.py --risk High --top 5
"""

import os
import sys
import argparse
import sqlite3
from typing import Optional, Dict, Any
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")

# Risk Category Mapping
RISK_MAP = {
    "low": ["Low", "Moderate"],
    "moderate": ["Moderate", "Moderately High"],
    "high": ["High", "Moderately High"],
    "very high": ["Very High", "High"],
}

# Recommended Asset Allocation by Risk Profile
ALLOCATION_MAP = {
    "low": {"Equity (%)": 10, "Debt/Gilt (%)": 60, "Liquid/Cash (%)": 30},
    "moderate": {"Equity (%)": 50, "Debt/Gilt (%)": 35, "Liquid/Cash (%)": 15},
    "high": {"Equity (%)": 75, "Debt/Gilt (%)": 20, "Liquid/Cash (%)": 5},
    "very high": {"Equity (%)": 90, "Debt/Gilt (%)": 10, "Liquid/Cash (%)": 0},
}


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create and return a read-only SQLite database connection."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}. Please run run_pipeline.py first.")
    return sqlite3.connect(db_path)


def recommend_funds(
    risk_profile: str = "Moderate",
    top_n: int = 3,
    db_path: str = DB_PATH,
) -> pd.DataFrame:
    """Recommend top N funds for a given investor risk profile.

    Parameters
    ----------
    risk_profile : str
        Investor risk appetite: 'Low', 'Moderate', 'High', or 'Very High'.
    top_n : int, default=3
        Number of recommended funds to return.
    db_path : str
        Path to SQLite database.

    Returns
    -------
    pd.DataFrame
        Ranked mutual fund recommendations with key risk-adjusted metrics.
    """
    key = risk_profile.strip().lower()
    allowed_categories = RISK_MAP.get(key, ["Moderate", "Moderately High"])

    conn = get_connection(db_path)
    try:
        query = """
            SELECT 
                f.amfi_code,
                f.scheme_name,
                f.fund_house,
                f.category,
                f.sub_category,
                f.risk_category,
                f.expense_ratio_pct,
                p.return_1yr_pct,
                p.return_3yr_pct,
                p.sharpe_ratio,
                p.sortino_ratio,
                p.alpha,
                p.max_drawdown_pct
            FROM dim_fund f
            INNER JOIN fact_performance p ON f.amfi_code = p.amfi_code
            ORDER BY p.sharpe_ratio DESC, p.return_3yr_pct DESC
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    # Filter by risk profile matching
    filtered = df[df["risk_category"].isin(allowed_categories)].copy()

    if filtered.empty:
        filtered = df.copy()

    # Sort primarily by Sharpe ratio descending, then Sortino, then expense ratio ascending
    recommended = filtered.sort_values(
        by=["sharpe_ratio", "sortino_ratio", "expense_ratio_pct"],
        ascending=[False, False, True],
    ).head(top_n).reset_index(drop=True)

    recommended["rank"] = range(1, len(recommended) + 1)
    return recommended


def print_recommendation_report(risk_profile: str = "Moderate", top_n: int = 3) -> None:
    """Print formatted terminal recommendation report including asset allocation."""
    norm_key = risk_profile.strip().lower()
    if norm_key not in RISK_MAP:
        print(f"Warning: '{risk_profile}' unrecognized. Defaulting to 'Moderate'.")
        norm_key = "moderate"
        risk_profile = "Moderate"

    recs = recommend_funds(risk_profile=risk_profile, top_n=top_n)
    alloc = ALLOCATION_MAP.get(norm_key, ALLOCATION_MAP["moderate"])

    print("=" * 85)
    print(f"  BLUESTOCK MUTUAL FUND RECOMMENDER -- RISK PROFILE: {risk_profile.upper()}")
    print("=" * 85)
    print("\n[Target Portfolio Asset Allocation Model]")
    for asset, pct in alloc.items():
        bar = "#" * (pct // 4)
        print(f"  {asset:<18}: {pct:>3}%  {bar}")

    print(f"\n[Top {top_n} Recommended Funds (Ranked by Risk-Adjusted Sharpe)]")
    print("-" * 85)
    header = f"{'#':<3} {'Scheme Name':<42} {'Category':<14} {'Sharpe':<8} {'3Y CAGR':<9} {'TER %':<6}"
    print(header)
    print("-" * 85)
    for _, row in recs.iterrows():
        name = str(row['scheme_name'])[:40]
        cat = str(row['sub_category'])[:13]
        sharpe = f"{row['sharpe_ratio']:.2f}"
        cagr = f"{row['return_3yr_pct']:.2f}%"
        ter = f"{row['expense_ratio_pct']:.2f}%"
        print(f"{row['rank']:<3} {name:<42} {cat:<14} {sharpe:<8} {cagr:<9} {ter:<6}")
    print("=" * 85)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bluestock MF Fund Recommender")
    parser.add_argument(
        "--risk",
        type=str,
        default="Moderate",
        choices=["Low", "Moderate", "High", "Very High", "low", "moderate", "high", "very high"],
        help="Investor risk profile (Low, Moderate, High, Very High)",
    )
    parser.add_argument("--top", type=int, default=3, help="Number of top funds to return")
    args = parser.parse_args()

    print_recommendation_report(risk_profile=args.risk, top_n=args.top)
