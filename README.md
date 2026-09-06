# Bluestock Mutual Fund Analytics — Capstone Project

A data-driven analytics platform for Indian mutual fund performance analysis, investor behavior insights, and portfolio optimization.

## Project Structure

```
Bluestocks/
├── data/
│   ├── raw/              # Original CSV datasets + live NAV fetches
│   └── processed/        # Cleaned & transformed data
├── notebooks/            # Jupyter analysis notebooks
├── sql/                  # SQL queries for structured analysis
├── dashboard/            # Interactive dashboards
├── reports/              # Generated reports
├── data_ingestion.py     # Day 1: Load, inspect, validate all datasets
├── live_nav_fetch.py     # Fetch live NAV from mfapi.in
├── requirements.txt      # Python dependencies
└── .gitignore
```

## Datasets (10 CSVs)

| # | File | Records | Description |
|---|------|---------|-------------|
| 01 | fund_master | 40 | Scheme metadata (fund house, category, risk) |
| 02 | nav_history | 46,000 | Daily NAV values (Jan 2022 – May 2026) |
| 03 | aum_by_fund_house | 90 | Quarterly AUM by fund house |
| 04 | monthly_sip_inflows | 48 | Industry-level SIP trends |
| 05 | category_inflows | 144 | Category-wise net inflows |
| 06 | industry_folio_count | 21 | Monthly folio count breakdown |
| 07 | scheme_performance | 40 | Return metrics (1yr, 3yr, 5yr) |
| 08 | investor_transactions | 32,778 | Buy/sell/SIP transactions |
| 09 | portfolio_holdings | 322 | Stock-level portfolio weights |
| 10 | benchmark_indices | 8,050 | Daily index close values |

## Quick Start

```bash
pip install -r requirements.txt
python data_ingestion.py      # Load & validate all datasets
python live_nav_fetch.py      # Fetch live NAV from mfapi.in
```

## Tech Stack

Python · Pandas · NumPy · Matplotlib · Seaborn · Plotly · SQLAlchemy · Jupyter
