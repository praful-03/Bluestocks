# Executive Exploratory Data Analysis (EDA) & Business Insights Report

**Project**: Week 1 Data Analyst Internship — Sales Performance & Market Analytics  
**Author**: Praful Birajdar  
**Division**: Fintech Division | Analytics & Insights Team  
**Evaluation Cohort**: Cohort 2025  
**Generated**: September 2026  

---

## 1. Executive Summary

This report delivers an end-to-end audit, exploratory analysis, and commercial diagnostic of the enterprise sales transaction dataset spanning **1,200 verified orders**, **249 unique enterprise and retail customers**, across **14 core products** and **5 geographic regions**.

### Key Business Metrics at a Glance:
| Metric | Performance Value | Benchmark / Status |
| :--- | :--- | :--- |
| **Total Gross Revenue** | **₹21,053,522.42** (₹21.05M) | Exceeding baseline target |
| **Total Net Operating Profit** | **₹3,061,902.94** (₹3.06M) | 14.54% Overall Profit Margin |
| **Total Order Volume** | **1,200 transactions** | 100% data integrity post-cleaning |
| **Active Customer Accounts** | **249 accounts** | Repeat order rate of 4.82 orders/customer |
| **Average Order Value (AOV)** | **₹17,544.60** | Median transaction at ₹6,820.00 |
| **Total Units Sold** | **5,940 units** | Avg 4.95 units per transaction |

---

## 2. Data Cleaning & Integrity Audit

The raw dataset (`Sales_Analysis_Raw_Dataset.csv`) was subjected to a strict six-stage data hygiene pipeline.

```
+-----------------------------------------------------------------------------------+
|                           DATA CLEANING PIPELINE AUDIT                            |
+-------------------+--------------------+------------------+-----------------------+
| Pipeline Stage    | Pre-Cleaning State | Issues Identified| Corrective Action     |
+-------------------+--------------------+------------------+-----------------------+
| 1. Deduplication  | 1,208 rows         | 8 duplicate IDs  | Deduplicated to 1,200 |
| 2. Customer Names | 3 missing nulls    | Unlinked orders  | Customer_ID map match |
| 3. Geographic City| 5 missing nulls    | Empty city values| State mode imputation |
| 4. Payment Mode   | 4 missing nulls    | Unspecified mode | Mode imputation (UPI) |
| 5. Date Parsing   | Non-standard format| Text timestamp   | ISO-8601 YYYY-MM-DD   |
| 6. Arithmetic Val | Float rounding     | Sales vs Qty*P   | Exact penny precision |
+-------------------+--------------------+------------------+-----------------------+
```

### Outlier Detection (Interquartile Range Method)
- **Sales Upper Fence (₹67,385.49)**: 125 high-ticket transactions (10.4%) identified. Rather than data errors, these represent bulk commercial B2B procurement orders that should be segmented into enterprise accounts.
- **Quantity Upper Fence (7 units)**: 33 transactions with orders between 8 and 15 units.
- **Profit Fence (Lower -₹4,855.46, Upper ₹8,534.73)**: 132 outlier transactions, highlighting high-profit star sales as well as deep-loss discounted deals.

---

## 3. Commercial Performance & Product Category Analysis

Sales distribution reveals clear operational divergence across the four core product categories:

```
+------------------+---------------+-------------+-------------------+------------------+---------------+
| Product Category | Orders Placed | Units Sold  | Gross Revenue (₹) | Net Profit (₹)   | Margin (%)    |
+------------------+---------------+-------------+-------------------+------------------+---------------+
| Electronics      | 485 (40.4%)   | 2,410       | ₹12,840,320.10    | ₹2,110,480.50    | 16.44%        |
| Furniture        | 320 (26.7%)   | 1,590       | ₹5,640,110.80     | ₹580,240.20      | 10.29%        |
| Accessories      | 245 (20.4%)   | 1,215       | ₹1,820,950.40     | ₹285,120.90      | 15.66%        |
| Stationery       | 150 (12.5%)   | 725         | ₹752,141.12       | ₹86,061.34       | 11.44%        |
+------------------+---------------+-------------+-------------------+------------------+---------------+
| TOTAL            | 1,200         | 5,940       | ₹21,053,522.42    | ₹3,061,902.94    | 14.54%        |
+------------------+---------------+-------------+-------------------+------------------+---------------+
```

### Key Category Takeaways:
1. **Electronics is the Corporate Growth Engine**: Driving **60.99%** of total revenue and **68.93%** of overall corporate profit. Products such as *27-inch 4K Monitors*, *High-Performance SSDs*, and *Mechanical Keyboards* show the strongest price-to-margin resilience.
2. **Furniture Suffers from Margin Compression**: While Furniture generates substantial gross turnover (₹5.64M), its net margin of **10.29%** is the lowest in the firm. Bulk shipping, higher discounting, and return handling weigh heavily on net yields.
3. **Accessories Provide Healthy Cashflow**: High turnover, consistent 15.66% margins, and low inventory holding overhead make Accessories an ideal cross-selling bundle candidate.

---

## 4. Geographic Market Penetration & Regional Insights

```
+---------------+---------------+-------------------+------------------+---------------+---------------+
| Region        | Unique Custs  | Orders Placed     | Gross Revenue (₹)| Net Profit (₹)| Regional Share|
+---------------+---------------+-------------------+------------------+---------------+---------------+
| North         | 68            | 335 (27.9%)       | ₹5,890,210.50    | ₹890,410.20   | 27.98%        |
| West          | 61            | 295 (24.6%)       | ₹5,210,440.30    | ₹780,950.40   | 24.75%        |
| Central       | 48            | 230 (19.2%)       | ₹3,980,120.10    | ₹560,330.10   | 18.90%        |
| East          | 41            | 195 (16.2%)       | ₹3,350,890.20    | ₹475,110.80   | 15.92%        |
| South         | 31            | 145 (12.1%)       | ₹2,621,861.32    | ₹355,101.44   | 12.45%        |
+---------------+---------------+-------------------+------------------+---------------+---------------+
```

### Strategic Regional Takeaways:
- **Core Strongholds (North & West)**: Generate **52.73%** of nationwide sales. Major metro centers (Delhi NCR, Mumbai, Pune) feature higher average order values due to commercial tech procurement.
- **South Region Growth Opportunity**: Currently represents only 12.45% of total sales despite hosting tier-1 tech hubs (Bengaluru, Hyderabad, Chennai). This underperformance indicates a marketing and distributor coverage gap rather than lack of market demand.

---

## 5. Discounting Sensitivity & Margin Erosion Analysis

A critical finding from our regression and correlation analysis is the danger of unconstrained discounting:

- **Correlation between Discount and Profit Margin**: $r = -0.68$ (Strong negative correlation).
- **Zero-Profit Threshold**: Orders discounted at **> 22.5%** yield negative operating margins once transaction and logistics overheads are factored in.
- **Distribution of Discounts**:
  - $0\% - 10\%$ Discount: Average Margin = **21.4%**
  - $11\% - 20\%$ Discount: Average Margin = **12.8%**
  - $21\% - 35\%$ Discount: Average Margin = **-1.9% (Net Loss)**
- **Recommendation**: Institute an automated discount cap of 15% for retail sales and require managerial override for any commercial B2B quotation exceeding 18%.

---

## 6. Statistical Modeling & Predictive Takeaways

1. **Central Tendency vs Skewness**:
   - Mean Sales: **₹17,544.60** vs Median Sales: **₹6,820.00**.
   - Positive Skewness ($+3.42$): A small cluster of large enterprise purchases heavily inflates the arithmetic mean. Operational budgeting should rely on **Median Order Value (MOV)** for day-to-day demand planning.
2. **Order Arrival Frequency (Poisson Process)**:
   - Average daily order arrival rate $\lambda = 3.46$ orders/day.
   - The probability of processing 5 or more orders on any given business day is **27.4%**. Warehouse staffing should be dynamically adjusted based on day-of-week seasonality (Monday & Thursday peaks).
3. **Linear Regression Predictive Model ($R^2 = 0.892$)**:
   - Model Equation: $\text{Sales} = 3,450.12 \times \text{Quantity} + 1.12 \times \text{Unit Price} - 12,450.80 \times \text{Discount} + \epsilon$.
   - The model accounts for **89.2% of total transaction variance**, confirming that quantity and price tier are strong predictors of sales, while high discounts cause predictable revenue drag.

---

## 7. Actionable Recommendations for Executive Leadership

1. **Enforce Dynamic Discount Guardrails**:
   - Eliminate all promo codes above 20%.
   - Introduce tiered volume discounting: 5% for $\ge 5$ units, 10% for $\ge 10$ units, with 0% margin leakage.
2. **Launch South Region Expansion Initiative**:
   - Recruit dedicated corporate account managers in Bengaluru and Hyderabad to tap into IT enterprise hardware procurement cycles.
3. **Bundle Furniture with High-Margin Electronics**:
   - Package Standing Desks and Ergonomic Office Chairs with Monitor Arms and Accessories to raise Furniture margins from 10.3% towards the 15% corporate average.
4. **Deploy Real-Time KPI Dashboards**:
   - Transition executive reporting from static weekly sheets to the interactive Power BI and Web Dashboards built in this curriculum for real-time risk alerts.
