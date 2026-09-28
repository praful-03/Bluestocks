# Sprint 1 Retrospective & Sign-Off Report

**Sprint**: Sprint 1 · Data Foundation & Engineering  
**Epic**: Epic 01 · Data Ingestion & ETL  
**Story Points**: 34 SP  
**Date**: September 2026  
**Status**: **COMPLETED & SIGNED OFF**  
**Database**: `nifty100.db` (and synchronized to `data/nifty100.db`)

---

## 1. Sprint Goal & Objectives

> **Sprint Goal**: By end of Sprint 1, the team must have a fully loaded and validated SQLite database (`nifty100.db`) containing all 10+ tables from 12 source files. All 16 data quality rules must have been run and any CRITICAL failures resolved. The foundation for all subsequent modules must be in place.

### Outcome
**GOAL ACHIEVED 100%**. All 12 source files (7 core + 5 supplementary) have been ingested, normalised, validated through 16 DQ rules, and successfully loaded into `nifty100.db` with strict foreign key constraints enabled.

---

## 2. Definition of Done (DoD) & Acceptance Criteria

| Criteria / Acceptance Gate | Target | Actual Result | Status |
|---|---|---|---|
| Master Company Count | `SELECT COUNT(*) FROM companies = 92` | Exactly **92** companies | **PASSED** |
| Foreign Key Integrity Check | `PRAGMA foreign_key_check;` → 0 rows | **0 rows returned** (Zero FK violations) | **PASSED** |
| Critical Rejections on Load | `critical_rejections = 0` | **0** critical rejections on DB load | **PASSED** |
| 16 DQ Rules Implementation | DQ-01 to DQ-16 implemented | All **16 rules** active & verified | **PASSED** |
| Unit Test Suite | 35+ unit tests passing | **64 unit tests** passing (100% green) | **PASSED** |
| Normaliser Year Tests | ≥ 20 unit tests | **23 test cases** passing | **PASSED** |
| Normaliser Ticker Tests | ≥ 15 unit tests | **17 test cases** passing | **PASSED** |
| Validator Rule Tests | 16 test cases | **16 test cases** passing | **PASSED** |
| Database Integration Tests | 8 test cases | **8 test cases** passing | **PASSED** |
| Manual Review | 5 sample companies audited | ABB, TCS, HDFCBANK, RELIANCE, SUNPHARMA verified | **PASSED** |
| Exploratory Queries | 10 queries in `notebooks/` | 10 production SQL queries executed | **PASSED** |

---

## 3. Database Inventory & Table Row Counts

All 12 datasets were processed and loaded into `nifty100.db`:

| # | Table Name | Source File | Category | Ingested Rows | Rejected Rows | DB Primary Key |
|---|---|---|---|---|---|---|
| 1 | `companies` | `companies.xlsx` (header=1) | Core Master | **92** | 0 | `id` |
| 2 | `sectors` | `sectors.xlsx` (header=0) | Supplementary | **92** | 0 | `company_id` |
| 3 | `profitandloss` | `profitandloss.xlsx` (header=1) | Core Statement | **1,073** | 203 (Orphans & TTM) | `(company_id, year)` |
| 4 | `balancesheet` | `balancesheet.xlsx` (header=1) | Core Statement | **1,140** | 172 (Orphans & 2024.5) | `(company_id, year)` |
| 5 | `cashflow` | `cashflow.xlsx` (header=1) | Core Statement | **1,056** | 131 (Orphans & Dups) | `(company_id, year)` |
| 6 | `financial_ratios` | `financial_ratios.xlsx` (header=0) | Supplementary | **1,041** | 143 (Orphans & Dups) | `(company_id, year)` |
| 7 | `market_cap` | `market_cap.xlsx` (header=0) | Supplementary | **552** | 0 | `(company_id, year)` |
| 8 | `stock_prices` | `stock_prices.xlsx` (header=0) | Supplementary | **5,520** | 0 | `(company_id, date)` |
| 9 | `documents` | `documents.xlsx` (header=1) | Core Repository | **1,457** | 128 (Orphans) | `id` |
| 10 | `analysis` | `analysis.xlsx` (header=1) | Core Pre-computed | **16** | 4 (Orphans) | `id` |
| 11 | `prosandcons` | `prosandcons.xlsx` (header=1) | Core Qualitative | **14** | 2 (Orphans) | `id` |
| 12 | `peer_groups` | `peer_groups.xlsx` (header=0) | Supplementary | **56** | 0 | `id` |

---

## 4. 16 Data Quality (DQ) Rules Summary

| Rule ID | Rule Name | Severity | Condition & Implementation | Action Taken |
|---|---|---|---|---|
| **DQ-01** | Company PK Uniqueness | CRITICAL | `len(companies) == companies.id.nunique()` | Verified unique 92 companies |
| **DQ-02** | Annual PK Uniqueness | CRITICAL | Unique `(company_id, year)` | Deduplicated keeping last occurrence |
| **DQ-03** | FK Integrity | CRITICAL | All child `company_id` in `companies.id` | Orphan rows rejected and logged |
| **DQ-04** | Balance Sheet Balance | WARNING | `abs(total_assets - total_liabilities) / total_assets < 0.01` | Flagged for review; clean in DB |
| **DQ-05** | OPM Cross-Check | WARNING | `abs(opm - (op_profit/sales*100)) < 1.0` | Flagged differences; logged to CSV |
| **DQ-06** | Positive Sales | WARNING | `sales > 0` for non-banks | Flagged 1 period (`ADANIENSOL` FY14) |
| **DQ-07** | Year Format | CRITICAL | After `normalize_year()`, matches `^\d{4}-\d{2}$` | Normalised; non-annual TTM rejected |
| **DQ-08** | Ticker Format | CRITICAL | Length 2–12, uppercase stripped | All tickers normalised |
| **DQ-09** | Net Cash Check | WARNING | `abs(net_cash_flow - sum(components)) <= 10` | Discrepancies logged |
| **DQ-10** | Non-Negative Fixed Assets | WARNING | `fixed_assets >= 0` | Coerced negatives to 0 and logged |
| **DQ-11** | Tax Rate Range | WARNING | `0 <= tax_percentage <= 60` | Anomalies logged |
| **DQ-12** | Dividend Payout Cap | WARNING | `dividend_payout <= 200` | Payouts >200% flagged |
| **DQ-13** | URL Validity | WARNING | `Annual_Report` URL well-formed | Checked and flagged broken URLs |
| **DQ-14** | EPS Sign Consistency | WARNING | `eps > 0` if `net_profit > 0` | Inconsistencies flagged |
| **DQ-15** | BSE Strict Balance | INFO | `total_assets == total_liabilities` | Strict equality monitored |
| **DQ-16** | Coverage Check | WARNING | Each company has ≥ 5 years of data | Flagged 3 companies (`JIOFIN`, `ATGL`, `SBIN`) |

---

## 5. Key Deliverables Generated

1. **`nifty100.db`** (and `data/nifty100.db`): Full SQLite 3 database containing 12 relational tables.
2. **`output/load_audit.csv`**: Full per-table audit log detailing input records, inserted records, rejected rows, and load runtimes.
3. **`output/validation_failures.csv`**: Comprehensive failure log documenting every DQ issue flagged with rule ID, company, year, and severity.
4. **`src/etl/loader.py`**: Automated ingestion pipeline supporting `header=1` and `header=0` Excel parsing.
5. **`src/etl/normaliser.py`**: Production functions `normalize_year()` and `normalize_ticker()`.
6. **`src/etl/validator.py`**: Production engine for all 16 DQ rules.
7. **`db/schema.sql`**: SQLite DDL defining tables, primary keys, foreign keys, and indexes.
8. **`tests/etl/`**: 64 unit and integration tests passing.
9. **`notebooks/exploratory_queries.sql`**: 10 analytical SQL queries.
10. **`reports/day6_manual_dq_review.md`**: Deep-dive audit report on 5 sample companies and DQ-16 coverage.
11. **`Makefile`**: Automation targets (`load`, `ratios`, `test`, `report`, `dashboard`, `api`, `clean`).

---

## 6. Sprint Retrospective Notes

### What Went Well
- Pipeline ingestion order cleanly satisfies strict SQLite foreign key constraints (`PRAGMA foreign_keys = ON;`).
- Pre-insertion deduplication (DQ-02) and orphan isolation (DQ-03) ensured zero integrity errors during database loading.
- Test coverage exceeded targets: 64 automated tests covering normalisers, validation rules, and schema assertions.
- 10 exploratory queries confirmed expected business realities (e.g. top revenue large caps: Reliance, LIC, IOC, ONGC).

### Key Insights & Data Gaps Identified
- **JIOFIN** has only 2–3 years of data due to its 2023 demerger from Reliance.
- **ATGL** has no cash flow records in the raw extract; P&L and BS are intact.
- **SBIN** raw balance sheet was omitted from the non-bank format; P&L and CF have 12 years of continuous data.
- Downstream Ratio Engine (Sprint 2) will handle these edge cases cleanly via sector-relative fallbacks and turnaround flags.

### Handoff to Sprint 2
The data foundation is **100% complete and validated**. The team is ready to begin **Sprint 2: Financial Ratio Engine (Days 08–14)** to compute 50+ financial ratios, CAGR metrics, cash flow quality scores, and capital allocation patterns.
