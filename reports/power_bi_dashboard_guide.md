# Power BI Business Performance Dashboard — Architecture & DAX Implementation Guide

**Program**: Data Analyst Internship — Week 1 Deliverable  
**Author**: Praful Birajdar  
**Domain**: Fintech | Analytics & Insights  
**Status**: Ready for Power BI Desktop & Interactive Web Deployment  

---

## 1. Data Model Architecture (Star Schema)

The dashboard is built on an enterprise-grade **Star Schema** optimized for high-performance in-memory tabular querying in Power BI's VertiPaq engine.

```
       +-----------------------+              +-----------------------+
       |     dim_customers     |              |     dim_products      |
       +-----------------------+              +-----------------------+
       | Customer_ID (PK) <----+              +---> Product_ID (PK)   |
       | Customer_Name         |              |     Product           |
       | City                  |              |     Category          |
       | State                 |              |     Sub_Category      |
       | Region                |              |     Unit_Price        |
       +-----------------------+              +-----------------------+
                   |                                      |
                   | 1                                    | 1
                   |                                      |
                   | *                                    | *
       +--------------------------------------------------------------+
       |                          fact_sales                          |
       +--------------------------------------------------------------+
       | Order_ID (PK)                                                |
       | Order_Date (FK) --------+                                    |
       | Customer_ID (FK)        |                                    |
       | Product_ID (FK)         |                                    |
       | Quantity                |                                    |
       | Unit_Price              |                                    |
       | Discount                |                                    |
       | Sales                   |                                    |
       | Profit                  |                                    |
       | Profit_Margin_Pct       |                                    |
       | Payment_Mode            |                                    |
       +-------------------------|------------------------------------+
                                 | *
                                 |
                                 | 1
                      +-----------------------+
                      |       dim_date        |
                      +-----------------------+
                      | Date (PK) <-----------+
                      | Date_Key              |
                      | Year                  |
                      | Quarter               |
                      | Month                 |
                      | Month_Name            |
                      | Day_of_Week           |
                      +-----------------------+
```

### Relationship Configuration in Power BI:
1. `dim_customers[Customer_ID]` **1 : \*** `fact_sales[Customer_ID]` (Single Cross-filter direction)
2. `dim_products[Product_ID]` **1 : \*** `fact_sales[Product_ID]` (Single Cross-filter direction)
3. `dim_date[Date]` **1 : \*** `fact_sales[Order_Date]` (Single Cross-filter direction, marked as Date Table)

---

## 2. Complete DAX Formula Library

Create a dedicated table named `_Measures` in Power BI and paste the following production-grade DAX measures:

### A. Core Operational KPIs
```dax
-- Total Revenue
Total Sales = 
SUM(fact_sales[Sales])

-- Total Operating Profit
Total Profit = 
SUM(fact_sales[Profit])

-- Gross Profit Margin Percentage
Profit Margin % = 
DIVIDE([Total Profit], [Total Sales], 0)

-- Total Order Transactions Count
Total Orders = 
DISTINCTCOUNT(fact_sales[Order_ID])

-- Total Physical Units Sold
Total Units Sold = 
SUM(fact_sales[Quantity])

-- Average Order Value (AOV)
Average Order Value = 
DIVIDE([Total Sales], [Total Orders], 0)

-- Average Discount Given
Average Discount % = 
AVERAGE(fact_sales[Discount])
```

### B. Time Intelligence & Growth Measures
```dax
-- Year-to-Date (YTD) Cumulative Sales
Sales YTD = 
TOTALYTD([Total Sales], dim_date[Date])

-- Prior Year Sales (Same Period Last Year)
Sales Prior Year = 
CALCULATE([Total Sales], SAMEPERIODLASTYEAR(dim_date[Date]))

-- Year-over-Year (YoY) Sales Growth %
YoY Sales Growth % = 
VAR PrevYear = [Sales Prior Year]
VAR CurrYear = [Total Sales]
RETURN
    IF(
        ISBLANK(PrevYear), 
        BLANK(), 
        DIVIDE(CurrYear - PrevYear, PrevYear, 0)
    )

-- 3-Month Trailing Rolling Average Revenue
Sales 3M Moving Avg = 
AVERAGEX(
    DATESINPERIOD(dim_date[Date], LASTDATE(dim_date[Date]), -3, MONTH),
    [Total Sales]
)
```

### C. Advanced Business Logic & Segmentation
```dax
-- Dynamic Top 5 Products by Sales Revenue
Top 5 Products Sales = 
CALCULATE(
    [Total Sales],
    KEEPFILTERS(
        TOPN(5, ALLSELECTED(dim_products[Product]), [Total Sales], DESC)
    )
)

-- Margin Health Indicator (Conditional Formatting Badge)
Margin Health Status = 
SWITCH(
    TRUE(),
    [Profit Margin %] >= 0.20, "High Margin (>20%)",
    [Profit Margin %] >= 0.10, "Target Margin (10-20%)",
    [Profit Margin %] >= 0.00, "Low Margin (0-10%)",
    "Negative Margin (Loss)"
)
```

---

## 3. Power BI Canvas Layout & Visual Hierarchy

### Screen Specification: 16:9 Canvas (1280 x 720 px)
- **Primary Color Palette**:
  - Primary Corporate Navy: `#1E3A8A`
  - Accent Success Emerald: `#10B981`
  - Warning Amber: `#F59E0B`
  - Alert Crimson: `#EF4444`
  - Canvas Background: `#F8FAFC`

### Visual Layout Zones:
1. **Header Banner (Top, Full Width, Height 70px)**:
   - Title: `Enterprise Sales & Margin Performance Dashboard`
   - Subtitle: `Fintech Analytics Division — Executive Monitoring Suite`
   - Corporate Logo / Avatar & Refresh Date stamp
2. **Interactive Slicers Bar (Below Header, Height 55px)**:
   - Slicer 1: `dim_date[Year]` (Dropdown)
   - Slicer 2: `dim_customers[Region]` (Horizontal tile pill buttons)
   - Slicer 3: `dim_products[Category]` (Dropdown)
3. **KPI Scorecard Strip (Width 100%, 5 Cards)**:
   - Card 1: `Total Sales` (Formatted as Currency `₹21.05M`)
   - Card 2: `Total Profit` (Formatted as Currency `₹3.06M`)
   - Card 3: `Profit Margin %` (Formatted as `14.54%` with conditional text color)
   - Card 4: `Total Orders` (Formatted as Integer `1,200`)
   - Card 5: `Average Order Value` (Formatted as Currency `₹17,545`)
4. **Main Analytics Visuals (2 x 2 Grid)**:
   - **Top-Left (Visual 1)**: Line and Clustered Column Chart
     - Shared Axis: `dim_date[Month_Name]`
     - Column Values: `Total Sales`
     - Line Values: `Profit Margin %`
   - **Top-Right (Visual 2)**: Donut / Treemap Chart
     - Category: `dim_customers[Region]`
     - Values: `Total Sales`
     - Detail labels: Data value and percent of total
   - **Bottom-Left (Visual 3)**: Clustered Bar Chart
     - Y-Axis: `dim_products[Product]`
     - X-Axis: `Total Sales`
     - Tooltip: `Total Profit`, `Profit Margin %`
   - **Bottom-Right (Visual 4)**: Matrix Table
     - Rows: `dim_products[Category]`, `dim_products[Sub_Category]`
     - Values: `Total Orders`, `Total Units Sold`, `Total Sales`, `Total Profit`, `Profit Margin %`
     - Conditional Formatting: Background color data bars on Sales and font color on Margin %.

---

## 4. 10-Minute Step-by-Step Power BI Desktop Build Guide

1. **Launch Power BI Desktop** -> Click **Get Data** -> Select **Text/CSV**.
2. Navigate to `l:\Bluestocks\data\power_bi\` and load:
   - `dim_customers.csv`
   - `dim_products.csv`
   - `dim_date.csv`
   - `fact_sales.csv`
3. Click **Transform Data** (Power Query):
   - Confirm header promotion for all 4 tables.
   - Set `Order_Date` in `fact_sales` and `Date` in `dim_date` to `Date` type.
   - Click **Close & Apply**.
4. Switch to **Model View**:
   - Drag `dim_customers[Customer_ID]` to `fact_sales[Customer_ID]`.
   - Drag `dim_products[Product_ID]` to `fact_sales[Product_ID]`.
   - Drag `dim_date[Date]` to `fact_sales[Order_Date]`.
5. Switch to **Report View**:
   - Create a New Table named `_Measures`.
   - Copy-paste the DAX formulas from Section 2 above.
   - Place cards and charts according to the visual layout in Section 3.
6. Click **File** -> **Save As** -> Save as `Sales_Performance_Dashboard.pbix`.
