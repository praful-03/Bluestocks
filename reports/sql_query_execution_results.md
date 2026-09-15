# SQL Practice Queries — Execution Results Report

**Database Engine**: SQLite 3 (Standard ANSI SQL Compliant)
**Database Schema**: Normalized 3NF (Customers, Products, Orders)
**Dataset Records**: 1,200 Orders, 249 Customers, 14 Products

---

## 1. Basic SELECT: Sample Orders with Core Attributes
*Demonstrates basic SELECT and column projection.*

```sql
SELECT Order_ID, Order_Date, Customer_ID, Quantity, Sales, Profit
FROM Orders
LIMIT 5;
```

**Query Execution Result:**

| Order_ID   | Order_Date   | Customer_ID   |   Quantity |    Sales |   Profit |
|:-----------|:-------------|:--------------|-----------:|---------:|---------:|
| ORD10001   | 2025-04-13   | CUST1228      |          3 |   837.77 |    96.03 |
| ORD10002   | 2025-12-15   | CUST1114      |          3 |   406.36 |    12.34 |
| ORD10003   | 2025-09-28   | CUST1237      |          3 | 12900.6  |  1376.88 |
| ORD10004   | 2025-04-17   | CUST1141      |          1 |  4573.61 |   834.18 |
| ORD10005   | 2025-03-13   | CUST1174      |          1 |  1105.04 |    37.27 |

---

## 2. Filtering with WHERE: High-Value & Profitable Orders
*Filters for transactions where Sales > INR 25,000 and Profit > 0.*

```sql
SELECT Order_ID, Customer_ID, Sales, Profit, Payment_Mode
FROM Orders
WHERE Sales > 25000 AND Profit > 0
ORDER BY Sales DESC
LIMIT 5;
```

**Query Execution Result:**

| Order_ID   | Customer_ID   |   Sales |   Profit | Payment_Mode   |
|:-----------|:--------------|--------:|---------:|:---------------|
| ORD11153   | CUST1194      |  526293 | 44151.7  | Credit Card    |
| ORD10097   | CUST1130      |  451040 |  9020.81 | Debit Card     |
| ORD10818   | CUST1241      |  426388 | 20312.9  | UPI            |
| ORD10431   | CUST1044      |  411606 | 62237.3  | UPI            |
| ORD10065   | CUST1066      |  387913 |  7758.26 | UPI            |

---

## 3. Sorting with ORDER BY: Top 5 Highest Value Orders
*Orders transactions by descending Sales revenue.*

```sql
SELECT Order_ID, Order_Date, Customer_ID, Quantity, Sales, Profit
FROM Orders
ORDER BY Sales DESC
LIMIT 5;
```

**Query Execution Result:**

| Order_ID   | Order_Date   | Customer_ID   |   Quantity |   Sales |   Profit |
|:-----------|:-------------|:--------------|-----------:|--------:|---------:|
| ORD11153   | 2025-01-29   | CUST1194      |          8 |  526293 | 44151.7  |
| ORD10097   | 2025-11-23   | CUST1130      |          7 |  451040 |  9020.81 |
| ORD10818   | 2025-07-24   | CUST1241      |          7 |  426388 | 20312.9  |
| ORD10431   | 2025-05-27   | CUST1044      |          7 |  411606 | 62237.3  |
| ORD10065   | 2025-02-23   | CUST1066      |          7 |  387913 |  7758.26 |

---

## 4. Aggregate Functions: Overall Business Summary
*Calculates total revenue, profit, average order value, order count, and units sold.*

```sql
SELECT 
    COUNT(*) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Revenue,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(AVG(Sales), 2) AS Average_Order_Value,
    SUM(Quantity) AS Total_Units_Sold,
    ROUND(SUM(Profit) / SUM(Sales) * 100, 2) AS Overall_Profit_Margin_Pct
FROM Orders;
```

**Query Execution Result:**

|   Total_Orders |   Total_Revenue |   Total_Profit |   Average_Order_Value |   Total_Units_Sold |   Overall_Profit_Margin_Pct |
|---------------:|----------------:|---------------:|----------------------:|-------------------:|----------------------------:|
|           1200 |     3.52272e+07 |    4.43041e+06 |                 29356 |               3874 |                       12.58 |

---

## 5. GROUP BY: Revenue and Profit by Category
*Aggregates sales performance by product category.*

```sql
SELECT 
    p.Category,
    COUNT(o.Order_ID) AS Total_Orders,
    SUM(o.Quantity) AS Units_Sold,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    ROUND(SUM(o.Profit), 2) AS Profit,
    ROUND(SUM(o.Profit) / SUM(o.Sales) * 100, 2) AS Margin_Pct
FROM Orders o
JOIN Products p ON o.Product_ID = p.Product_ID
GROUP BY p.Category
ORDER BY Revenue DESC;
```

**Query Execution Result:**

| Category        |   Total_Orders |   Units_Sold |          Revenue |           Profit |   Margin_Pct |
|:----------------|---------------:|-------------:|-----------------:|-----------------:|-------------:|
| Electronics     |            332 |         1099 |      2.30184e+07 |      2.80576e+06 |        12.19 |
| Furniture       |            256 |          790 |      6.7704e+06  | 884021           |        13.06 |
| Appliances      |            271 |          851 |      5.08779e+06 | 696187           |        13.68 |
| Office Supplies |            341 |         1134 | 350600           |  44445.5         |        12.68 |

---

## 6. GROUP BY with Date: Monthly Revenue Trend
*Groups sales by Year-Month using standard ISO date extraction.*

```sql
SELECT 
    substr(Order_Date, 1, 7) AS Order_Month,
    COUNT(Order_ID) AS Orders_Count,
    ROUND(SUM(Sales), 2) AS Monthly_Revenue,
    ROUND(SUM(Profit), 2) AS Monthly_Profit
FROM Orders
GROUP BY substr(Order_Date, 1, 7)
ORDER BY Order_Month
LIMIT 6;
```

**Query Execution Result:**

| Order_Month   |   Orders_Count |   Monthly_Revenue |   Monthly_Profit |
|:--------------|---------------:|------------------:|-----------------:|
| 2025-01       |             95 |       3.00193e+06 |           344958 |
| 2025-02       |            100 |       2.39527e+06 |           322175 |
| 2025-03       |             76 |       2.14548e+06 |           230679 |
| 2025-04       |            110 |       4.20342e+06 |           580591 |
| 2025-05       |            116 |       4.07092e+06 |           535290 |
| 2025-06       |            106 |       3.2348e+06  |           406201 |

---

## 7. HAVING: High-Value Customers Generating > INR 50,000
*Applies group-level filtering to identify VIP clients.*

```sql
SELECT 
    c.Customer_ID,
    c.Customer_Name,
    c.Region,
    COUNT(o.Order_ID) AS Orders_Placed,
    ROUND(SUM(o.Sales), 2) AS Total_Spent
FROM Orders o
JOIN Customers c ON o.Customer_ID = c.Customer_ID
GROUP BY c.Customer_ID, c.Customer_Name, c.Region
HAVING SUM(o.Sales) > 50000
ORDER BY Total_Spent DESC
LIMIT 5;
```

**Query Execution Result:**

| Customer_ID   | Customer_Name   | Region   |   Orders_Placed |   Total_Spent |
|:--------------|:----------------|:---------|----------------:|--------------:|
| CUST1066      | Customer 1066   | East     |              10 |        780251 |
| CUST1051      | Customer 1051   | North    |               7 |        693356 |
| CUST1241      | Customer 1241   | South    |               5 |        647186 |
| CUST1194      | Customer 1194   | North    |               4 |        577964 |
| CUST1130      | Customer 1130   | West     |               6 |        511525 |

---

## 8. INNER JOIN: Orders Enriched with Customer & Geographic Details
*Combines orders with customer master data to inspect regional delivery.*

```sql
SELECT 
    o.Order_ID,
    o.Order_Date,
    c.Customer_Name,
    c.City,
    c.Region,
    o.Sales,
    o.Profit
FROM Orders o
INNER JOIN Customers c ON o.Customer_ID = c.Customer_ID
LIMIT 5;
```

**Query Execution Result:**

| Order_ID   | Order_Date   | Customer_Name   | City      | Region   |    Sales |   Profit |
|:-----------|:-------------|:----------------|:----------|:---------|---------:|---------:|
| ORD10001   | 2025-04-13   | Customer 1228   | Margao    | West     |   837.77 |    96.03 |
| ORD10002   | 2025-12-15   | Customer 1114   | Amritsar  | North    |   406.36 |    12.34 |
| ORD10003   | 2025-09-28   | Customer 1237   | Margao    | West     | 12900.6  |  1376.88 |
| ORD10004   | 2025-04-17   | Customer 1141   | Bengaluru | South    |  4573.61 |   834.18 |
| ORD10005   | 2025-03-13   | Customer 1174   | Kolhapur  | West     |  1105.04 |    37.27 |

---

## 9. Product Performance: Top 5 Revenue-Generating Products
*Evaluates individual product commercial success.*

```sql
SELECT 
    p.Product,
    p.Category,
    SUM(o.Quantity) AS Units_Sold,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    ROUND(SUM(o.Profit), 2) AS Profit
FROM Orders o
JOIN Products p ON o.Product_ID = p.Product_ID
GROUP BY p.Product, p.Category
ORDER BY Revenue DESC
LIMIT 5;
```

**Query Execution Result:**

| Product        | Category    |   Units_Sold |     Revenue |           Profit |
|:---------------|:------------|-------------:|------------:|-----------------:|
| AeroBook 14    | Electronics |          269 | 1.54694e+07 |      1.86036e+06 |
| Nova X5        | Electronics |          237 | 6.08021e+06 | 766475           |
| Air Purifier   | Appliances  |          240 | 3.40011e+06 | 472595           |
| Office Table   | Furniture   |          277 | 3.15645e+06 | 432330           |
| Filing Cabinet | Furniture   |          290 | 1.85113e+06 | 223745           |

---

## 10. Regional Performance: Revenue and Profit by Geographic Zone
*Aggregates financial results across geographic regions.*

```sql
SELECT 
    c.Region,
    COUNT(DISTINCT c.Customer_ID) AS Unique_Customers,
    COUNT(o.Order_ID) AS Total_Orders,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    ROUND(SUM(o.Profit), 2) AS Profit,
    ROUND(SUM(o.Profit) / SUM(o.Sales) * 100, 2) AS Profit_Margin_Pct
FROM Orders o
JOIN Customers c ON o.Customer_ID = c.Customer_ID
GROUP BY c.Region
ORDER BY Revenue DESC;
```

**Query Execution Result:**

| Region   |   Unique_Customers |   Total_Orders |     Revenue |           Profit |   Profit_Margin_Pct |
|:---------|-------------------:|---------------:|------------:|-----------------:|--------------------:|
| West     |                 85 |            449 | 1.2478e+07  |      1.58727e+06 |               12.72 |
| East     |                 59 |            271 | 9.10154e+06 |      1.17202e+06 |               12.88 |
| South    |                 58 |            261 | 7.61735e+06 | 929017           |               12.2  |
| North    |                 47 |            219 | 6.03031e+06 | 742101           |               12.31 |

---

## 11. Subquery: Customers with Lifetime Spend Above the Cohort Average
*Uses a scalar subquery in the HAVING clause to identify above-average accounts.*

```sql
SELECT 
    c.Customer_ID,
    c.Customer_Name,
    ROUND(SUM(o.Sales), 2) AS Customer_Revenue
FROM Orders o
JOIN Customers c ON o.Customer_ID = c.Customer_ID
GROUP BY c.Customer_ID, c.Customer_Name
HAVING SUM(o.Sales) > (
    SELECT AVG(Cust_Total)
    FROM (
        SELECT SUM(Sales) AS Cust_Total
        FROM Orders
        GROUP BY Customer_ID
    )
)
ORDER BY Customer_Revenue DESC
LIMIT 5;
```

**Query Execution Result:**

| Customer_ID   | Customer_Name   |   Customer_Revenue |
|:--------------|:----------------|-------------------:|
| CUST1066      | Customer 1066   |             780251 |
| CUST1051      | Customer 1051   |             693356 |
| CUST1241      | Customer 1241   |             647186 |
| CUST1194      | Customer 1194   |             577964 |
| CUST1130      | Customer 1130   |             511525 |

---

## 12. Window Function: National Product Revenue Ranking (RANK)
*Ranks every product by nationwide revenue using RANK() OVER ().*

```sql
SELECT 
    p.Product,
    p.Category,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    RANK() OVER (ORDER BY SUM(o.Sales) DESC) AS Revenue_Rank,
    DENSE_RANK() OVER (ORDER BY SUM(o.Sales) DESC) AS Dense_Rank
FROM Orders o
JOIN Products p ON o.Product_ID = p.Product_ID
GROUP BY p.Product, p.Category
LIMIT 5;
```

**Query Execution Result:**

| Product        | Category    |     Revenue |   Revenue_Rank |   Dense_Rank |
|:---------------|:------------|------------:|---------------:|-------------:|
| AeroBook 14    | Electronics | 1.54694e+07 |              1 |            1 |
| Nova X5        | Electronics | 6.08021e+06 |              2 |            2 |
| Air Purifier   | Appliances  | 3.40011e+06 |              3 |            3 |
| Office Table   | Furniture   | 3.15645e+06 |              4 |            4 |
| Filing Cabinet | Furniture   | 1.85113e+06 |              5 |            5 |

---

## 13. Window Function with PARTITION BY: Top Products within Each Region
*Ranks products partitioned by customer region.*

```sql
WITH RegionalProductSales AS (
    SELECT 
        c.Region,
        p.Product,
        ROUND(SUM(o.Sales), 2) AS Regional_Revenue,
        RANK() OVER (
            PARTITION BY c.Region 
            ORDER BY SUM(o.Sales) DESC
        ) AS Regional_Rank
    FROM Orders o
    JOIN Customers c ON o.Customer_ID = c.Customer_ID
    JOIN Products p ON o.Product_ID = p.Product_ID
    GROUP BY c.Region, p.Product
)
SELECT Region, Product, Regional_Revenue, Regional_Rank
FROM RegionalProductSales
WHERE Regional_Rank <= 2
ORDER BY Region, Regional_Rank;
```

**Query Execution Result:**

| Region   | Product     |   Regional_Revenue |   Regional_Rank |
|:---------|:------------|-------------------:|----------------:|
| East     | AeroBook 14 |        4.70681e+06 |               1 |
| East     | Nova X5     |        1.37716e+06 |               2 |
| North    | AeroBook 14 |        2.71188e+06 |               1 |
| North    | Nova X5     |   937361           |               2 |
| South    | AeroBook 14 |        3.48966e+06 |               1 |
| South    | Nova X5     |   938526           |               2 |
| West     | AeroBook 14 |        4.56103e+06 |               1 |
| West     | Nova X5     |        2.82717e+06 |               2 |

---

## 14. Window Functions: Month-over-Month (MoM) Growth Analysis (LAG)
*Computes previous month's revenue and percentage growth rate using LAG().*

```sql
WITH MonthlyTotals AS (
    SELECT 
        substr(Order_Date, 1, 7) AS Order_Month,
        ROUND(SUM(Sales), 2) AS Monthly_Revenue
    FROM Orders
    GROUP BY substr(Order_Date, 1, 7)
)
SELECT 
    Order_Month,
    Monthly_Revenue,
    LAG(Monthly_Revenue, 1) OVER (ORDER BY Order_Month) AS Prev_Month_Revenue,
    ROUND((Monthly_Revenue - LAG(Monthly_Revenue, 1) OVER (ORDER BY Order_Month)) / LAG(Monthly_Revenue, 1) OVER (ORDER BY Order_Month) * 100, 2) AS MoM_Growth_Pct
FROM MonthlyTotals
ORDER BY Order_Month
LIMIT 6;
```

**Query Execution Result:**

| Order_Month   |   Monthly_Revenue |   Prev_Month_Revenue |   MoM_Growth_Pct |
|:--------------|------------------:|---------------------:|-----------------:|
| 2025-01       |       3.00193e+06 |        nan           |           nan    |
| 2025-02       |       2.39527e+06 |          3.00193e+06 |           -20.21 |
| 2025-03       |       2.14548e+06 |          2.39527e+06 |           -10.43 |
| 2025-04       |       4.20342e+06 |          2.14548e+06 |            95.92 |
| 2025-05       |       4.07092e+06 |          4.20342e+06 |            -3.15 |
| 2025-06       |       3.2348e+06  |          4.07092e+06 |           -20.54 |

---
