"""
Day 06 Manual Review Script.
Performs verification on 5 random companies and identifies companies with < 5 years of financial history.
"""

import os
import sys
import sqlite3
import pandas as pd

# Resolve paths relative to this script regardless of cwd
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")

def run_review():
    conn = sqlite3.connect(DB_PATH)
    sample_companies = ['ABB', 'TCS', 'HDFCBANK', 'RELIANCE', 'SUNPHARMA']
    
    print("==================================================================")
    print("DAY 06 DATA QUALITY MANUAL REVIEW: 5 SAMPLE COMPANIES")
    print("==================================================================")
    
    results = {}
    for c in sample_companies:
        df_c = pd.read_sql(f"SELECT id, company_name, face_value, book_value FROM companies WHERE id='{c}'", conn)
        pl = pd.read_sql(f"SELECT year, sales, operating_profit, net_profit FROM profitandloss WHERE company_id='{c}' ORDER BY year", conn)
        bs = pd.read_sql(f"SELECT year, total_assets, total_liabilities FROM balancesheet WHERE company_id='{c}' ORDER BY year", conn)
        cf = pd.read_sql(f"SELECT year, operating_activity, investing_activity, financing_activity, net_cash_flow FROM cashflow WHERE company_id='{c}' ORDER BY year", conn)
        sp = pd.read_sql(f"SELECT COUNT(*) as price_count, MIN(date) as min_date, MAX(date) as max_date FROM stock_prices WHERE company_id='{c}'", conn)
        
        bs['diff'] = (bs['total_assets'] - bs['total_liabilities']).abs()
        max_bs_diff = bs['diff'].max() if len(bs) > 0 else 0
        
        print(f"\nCompany: {c} ({df_c['company_name'].iloc[0]})")
        print(f"  P&L records: {len(pl)} (Years: {pl['year'].min()} to {pl['year'].max()})")
        print(f"  BS records:  {len(bs)} (Years: {bs['year'].min()} to {bs['year'].max()}), Max Asset-Liab Diff: {max_bs_diff}")
        print(f"  CF records:  {len(cf)} (Years: {cf['year'].min()} to {cf['year'].max()})")
        print(f"  Prices:      {sp['price_count'].iloc[0]} monthly points ({sp['min_date'].iloc[0]} to {sp['max_date'].iloc[0]})")
        
        results[c] = {
            "name": df_c['company_name'].iloc[0],
            "pl_count": len(pl),
            "bs_count": len(bs),
            "cf_count": len(cf),
            "prices_count": sp['price_count'].iloc[0],
            "bs_balanced": bool(max_bs_diff <= 1.0)
        }

    # Identify companies with < 5 years of history
    query = """
    SELECT c.id, c.company_name,
           COUNT(DISTINCT p.year) as pl_years,
           COUNT(DISTINCT b.year) as bs_years,
           COUNT(DISTINCT f.year) as cf_years
    FROM companies c
    LEFT JOIN profitandloss p ON c.id = p.company_id
    LEFT JOIN balancesheet b ON c.id = b.company_id
    LEFT JOIN cashflow f ON c.id = f.company_id
    GROUP BY c.id, c.company_name
    HAVING pl_years < 5 OR bs_years < 5 OR cf_years < 5
    ORDER BY pl_years ASC;
    """
    df_under5 = pd.read_sql(query, conn)
    print("\n==================================================================")
    print(f"COMPANIES WITH < 5 YEARS COVERAGE (DQ-16 Flag): {len(df_under5)}")
    print("==================================================================")
    print(df_under5.to_string(index=False))
    
    conn.close()
    return results, df_under5

if __name__ == "__main__":
    run_review()
