"""
build_capstone_notebooks.py
===========================
Generates and executes the complete suite of 5 Capstone Jupyter Notebooks:
  1. notebooks/01_data_ingestion.ipynb
  2. notebooks/02_data_cleaning.ipynb
  3. notebooks/03_eda_analysis.ipynb
  4. notebooks/04_performance_analytics.ipynb
  5. notebooks/05_advanced_analytics.ipynb
"""

import os
import nbformat as nbf
from nbclient import NotebookClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOKS_DIR = os.path.join(BASE_DIR, "notebooks")
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)


def build_01_ingestion():
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell("# Day 1: Mutual Fund Data Ingestion & API Pipelines\n**Author:** Praful Birajdar | **Platform:** Bluestock Fintech Analytics\n\nIngests 10 core AMFI CSV datasets and connects to the mfapi.in REST API."),
        nbf.v4.new_code_cell("""import os, sys, requests, pandas as pd, numpy as np
import matplotlib.pyplot as plt

raw_dir = os.path.join('..', 'data', 'raw')
print(f"Loading raw datasets from: {raw_dir}")
"""),
        nbf.v4.new_markdown_cell("## 1. Load and Inspect Fund Master"),
        nbf.v4.new_code_cell("""fund_master = pd.read_csv(os.path.join(raw_dir, '01_fund_master.csv'))
print(f"Fund Master: {fund_master.shape[0]} schemes, {fund_master.shape[1]} columns")
fund_master.head(5)"""),
        nbf.v4.new_markdown_cell("## 2. AMC & Category Breakdown"),
        nbf.v4.new_code_cell("""print("Unique AMCs:", fund_master['fund_house'].nunique())
print("Categories:", fund_master['category'].value_counts().to_dict())
print("Sub-categories:", fund_master['sub_category'].value_counts().to_dict())"""),
        nbf.v4.new_markdown_cell("## 3. Live NAV API Check (mfapi.in)"),
        nbf.v4.new_code_cell("""# Live NAV sample for HDFC Top 100 (AMFI 125497)
url = 'https://api.mfapi.in/mf/125497'
try:
    resp = requests.get(url, timeout=10)
    data = resp.json()
    print("API Status:", data.get('status'))
    print("Fund House:", data.get('meta', {}).get('fund_house'))
    print("Latest NAV:", data.get('data', [])[0] if data.get('data') else 'N/A')
except Exception as e:
    print("API offline/timeout:", e)
""")
    ]
    nb.cells = cells
    out_path = os.path.join(NOTEBOOKS_DIR, "01_data_ingestion.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created: {out_path}")


def build_02_cleaning():
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell("# Day 2: Data Cleaning & Relational SQLite Architecture\n**Author:** Praful Birajdar | **Platform:** Bluestock Fintech Analytics\n\nCleans 10 raw datasets, resolves missing dates with forward-fill, and populates the SQLite Star Schema database."),
        nbf.v4.new_code_cell("""import os, sqlite3, pandas as pd, numpy as np

db_path = os.path.join('..', 'bluestock_mf.db')
conn = sqlite3.connect(db_path)
print("Connected to SQLite Database:", db_path)
"""),
        nbf.v4.new_markdown_cell("## 1. Verify Star Schema Tables"),
        nbf.v4.new_code_cell("""tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
for t in tables['name']:
    cnt = pd.read_sql(f"SELECT count(*) as c FROM {t}", conn)['c'][0]
    print(f"{t:<25}: {cnt:>8,} rows")"""),
        nbf.v4.new_markdown_cell("## 2. Core SQL Analytical Queries"),
        nbf.v4.new_code_cell("""# Top 5 funds by 3Y CAGR
top_funds = pd.read_sql('''
    SELECT scheme_name, fund_house, sub_category, return_3yr_pct, sharpe_ratio, alpha
    FROM fact_performance
    ORDER BY return_3yr_pct DESC
    LIMIT 5
''', conn)
top_funds"""),
        nbf.v4.new_code_cell("conn.close()")
    ]
    nb.cells = cells
    out_path = os.path.join(NOTEBOOKS_DIR, "02_data_cleaning.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created: {out_path}")


def build_03_eda():
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell("# Day 3: Exploratory Data Analysis (EDA) & Macro Industry Dynamics\n**Author:** Praful Birajdar | **Platform:** Bluestock Fintech Analytics\n\nComprehensive exploration of Indian Mutual Fund macro metrics, AUM expansion, SIP trajectories, and investor demographics."),
        nbf.v4.new_code_cell("""import os, sqlite3, pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns

conn = sqlite3.connect(os.path.join('..', 'bluestock_mf.db'))
"""),
        nbf.v4.new_markdown_cell("## 1. Top AMCs by Market Share"),
        nbf.v4.new_code_cell("""aum = pd.read_sql('''
    SELECT fund_house, MAX(aum_lakh_crore) as aum_lakh_cr
    FROM fact_aum
    GROUP BY fund_house
    ORDER BY aum_lakh_cr DESC
''', conn)
print(aum)
"""),
        nbf.v4.new_markdown_cell("## 2. Monthly SIP Inflow Milestone"),
        nbf.v4.new_code_cell("""sip = pd.read_sql("SELECT month, sip_inflow_crore, active_sip_accounts_crore FROM fact_sip_inflows ORDER BY month", conn)
print("Latest SIP Inflow (Dec 2025):", sip['sip_inflow_crore'].iloc[-1], "Cr")
print("Total Active SIP Accounts:", sip['active_sip_accounts_crore'].iloc[-1], "Cr")
"""),
        nbf.v4.new_markdown_cell("## 3. Investor Demographics & T30/B30 Split"),
        nbf.v4.new_code_cell("""tier = pd.read_sql("SELECT city_tier, COUNT(*) as tx_count, SUM(amount_inr)/1e7 as total_cr FROM fact_transactions GROUP BY city_tier", conn)
print(tier)
conn.close()""")
    ]
    nb.cells = cells
    out_path = os.path.join(NOTEBOOKS_DIR, "03_eda_analysis.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created: {out_path}")


def build_04_performance():
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell("# Day 4: Fund Performance Analytics & Risk-Adjusted Scoring\n**Author:** Praful Birajdar | **Platform:** Bluestock Fintech Analytics\n\nComputation of CAGR (1Y, 3Y, 5Y), Sharpe Ratio, Sortino Ratio, Alpha, Beta, and Maximum Drawdown across 40 schemes."),
        nbf.v4.new_code_cell("""import os, sqlite3, pandas as pd, numpy as np

conn = sqlite3.connect(os.path.join('..', 'bluestock_mf.db'))
perf = pd.read_sql('''
    SELECT scheme_name, sub_category, return_1yr_pct, return_3yr_pct, sharpe_ratio, sortino_ratio, alpha, beta, max_drawdown_pct
    FROM fact_performance
    ORDER BY sharpe_ratio DESC
''', conn)
print("Top 10 Funds by Sharpe Ratio:")
perf.head(10)
"""),
        nbf.v4.new_markdown_cell("## Category Averages"),
        nbf.v4.new_code_cell("""cat_avg = perf.groupby('sub_category').agg({
    'return_1yr_pct': 'mean',
    'return_3yr_pct': 'mean',
    'sharpe_ratio': 'mean',
    'alpha': 'mean',
    'max_drawdown_pct': 'mean'
}).round(2)
cat_avg"""),
        nbf.v4.new_code_cell("conn.close()")
    ]
    nb.cells = cells
    out_path = os.path.join(NOTEBOOKS_DIR, "04_performance_analytics.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created: {out_path}")


def build_05_advanced():
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell("# Day 6: Advanced Analytics & Quantitative Risk Modeling\n**Author:** Praful Birajdar | **Platform:** Bluestock Fintech Analytics\n\nValue at Risk (VaR 95%), Conditional VaR (CVaR), Investor Cohort Retention, SIP Churn Risk, and Sector HHI."),
        nbf.v4.new_code_cell("""import os, pandas as pd, numpy as np

proc_dir = os.path.join('..', 'data', 'processed')
var_df = pd.read_csv(os.path.join(proc_dir, 'var_cvar_report.csv'))
print("VaR/CVaR Head:")
var_df.head(5)
"""),
        nbf.v4.new_markdown_cell("## 1. Investor Cohorts"),
        nbf.v4.new_code_cell("""cohort_df = pd.read_csv(os.path.join(proc_dir, 'cohort_analysis.csv'))
cohort_df"""),
        nbf.v4.new_markdown_cell("## 2. Sector Concentration (HHI)"),
        nbf.v4.new_code_cell("""hhi_df = pd.read_csv(os.path.join(proc_dir, 'sector_hhi.csv'))
print("HHI Concentration Grades:")
print(hhi_df['concentration_grade'].value_counts())
hhi_df.head(5)"""),
        nbf.v4.new_markdown_cell("## 3. Fund Recommendation Engine Demo"),
        nbf.v4.new_code_cell("""import sys
sys.path.append('..')
import recommender

recs = recommender.recommend_funds(risk_profile='Moderate', top_n=3)
recs[['rank', 'scheme_name', 'sub_category', 'sharpe_ratio', 'return_3yr_pct']]""")
    ]
    nb.cells = cells
    out_path = os.path.join(NOTEBOOKS_DIR, "05_advanced_analytics.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created: {out_path}")


def main():
    print("=" * 60)
    print("  BUILDING CAPSTONE JUPYTER NOTEBOOKS")
    print("=" * 60)
    build_01_ingestion()
    build_02_cleaning()
    build_03_eda()
    build_04_performance()
    build_05_advanced()
    print("  All 5 capstone notebooks built successfully.")


if __name__ == "__main__":
    main()
