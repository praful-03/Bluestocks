"""
run_sql_practice.py
-------------------
Loads cleaned sales data into a SQLite database (sales_analysis.db),
executes the full suite of Data Analyst SQL practice queries,
and formats the results into a verified execution markdown report.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = r"l:\Bluestocks\sales_analysis.db"
REPORT_PATH = r"l:\Bluestocks\reports\sql_query_execution_results.md"
SQL_FILE_PATH = r"l:\Bluestocks\sql\sales_analysis_practice_queries.sql"

def setup_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Normalized Tables
    cursor.execute("""
    CREATE TABLE Customers (
        Customer_ID TEXT PRIMARY KEY,
        Customer_Name TEXT,
        City TEXT,
        State TEXT,
        Region TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE Products (
        Product_ID INTEGER PRIMARY KEY,
        Product TEXT,
        Category TEXT,
        Sub_Category TEXT,
        Unit_Price REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE Orders (
        Order_ID TEXT PRIMARY KEY,
        Order_Date TEXT,
        Customer_ID TEXT,
        Product_ID INTEGER,
        Quantity INTEGER,
        Discount REAL,
        Sales REAL,
        Profit REAL,
        Payment_Mode TEXT,
        FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
        FOREIGN KEY (Product_ID) REFERENCES Products(Product_ID)
    );
    """)

    # Populate from Star Schema CSVs
    cust_df = pd.read_csv(r"l:\Bluestocks\data\power_bi\dim_customers.csv")
    prod_df = pd.read_csv(r"l:\Bluestocks\data\power_bi\dim_products.csv")
    sales_df = pd.read_csv(r"l:\Bluestocks\data\power_bi\fact_sales.csv")

    cust_df.to_sql('Customers', conn, if_exists='append', index=False)
    prod_df.to_sql('Products', conn, if_exists='append', index=False)
    sales_df[['Order_ID', 'Order_Date', 'Customer_ID', 'Product_ID', 'Quantity', 'Discount', 'Sales', 'Profit', 'Payment_Mode']].to_sql('Orders', conn, if_exists='append', index=False)

    conn.commit()
    print(f"Database {DB_PATH} initialized successfully.")
    print(f"  Customers: {len(cust_df)} rows")
    print(f"  Products: {len(prod_df)} rows")
    print(f"  Orders: {len(sales_df)} rows")
    return conn

def execute_queries(conn):
    queries = [
        (
            "1. Basic SELECT: Sample Orders with Core Attributes",
            "Demonstrates basic SELECT and column projection.",
            """SELECT Order_ID, Order_Date, Customer_ID, Quantity, Sales, Profit
FROM Orders
LIMIT 5;"""
        ),
        (
            "2. Filtering with WHERE: High-Value & Profitable Orders",
            "Filters for transactions where Sales > INR 25,000 and Profit > 0.",
            """SELECT Order_ID, Customer_ID, Sales, Profit, Payment_Mode
FROM Orders
WHERE Sales > 25000 AND Profit > 0
ORDER BY Sales DESC
LIMIT 5;"""
        ),
        (
            "3. Sorting with ORDER BY: Top 5 Highest Value Orders",
            "Orders transactions by descending Sales revenue.",
            """SELECT Order_ID, Order_Date, Customer_ID, Quantity, Sales, Profit
FROM Orders
ORDER BY Sales DESC
LIMIT 5;"""
        ),
        (
            "4. Aggregate Functions: Overall Business Summary",
            "Calculates total revenue, profit, average order value, order count, and units sold.",
            """SELECT 
    COUNT(*) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Revenue,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(AVG(Sales), 2) AS Average_Order_Value,
    SUM(Quantity) AS Total_Units_Sold,
    ROUND(SUM(Profit) / SUM(Sales) * 100, 2) AS Overall_Profit_Margin_Pct
FROM Orders;"""
        ),
        (
            "5. GROUP BY: Revenue and Profit by Category",
            "Aggregates sales performance by product category.",
            """SELECT 
    p.Category,
    COUNT(o.Order_ID) AS Total_Orders,
    SUM(o.Quantity) AS Units_Sold,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    ROUND(SUM(o.Profit), 2) AS Profit,
    ROUND(SUM(o.Profit) / SUM(o.Sales) * 100, 2) AS Margin_Pct
FROM Orders o
JOIN Products p ON o.Product_ID = p.Product_ID
GROUP BY p.Category
ORDER BY Revenue DESC;"""
        ),
        (
            "6. GROUP BY with Date: Monthly Revenue Trend",
            "Groups sales by Year-Month using standard ISO date extraction.",
            """SELECT 
    substr(Order_Date, 1, 7) AS Order_Month,
    COUNT(Order_ID) AS Orders_Count,
    ROUND(SUM(Sales), 2) AS Monthly_Revenue,
    ROUND(SUM(Profit), 2) AS Monthly_Profit
FROM Orders
GROUP BY substr(Order_Date, 1, 7)
ORDER BY Order_Month
LIMIT 6;"""
        ),
        (
            "7. HAVING: High-Value Customers Generating > INR 50,000",
            "Applies group-level filtering to identify VIP clients.",
            """SELECT 
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
LIMIT 5;"""
        ),
        (
            "8. INNER JOIN: Orders Enriched with Customer & Geographic Details",
            "Combines orders with customer master data to inspect regional delivery.",
            """SELECT 
    o.Order_ID,
    o.Order_Date,
    c.Customer_Name,
    c.City,
    c.Region,
    o.Sales,
    o.Profit
FROM Orders o
INNER JOIN Customers c ON o.Customer_ID = c.Customer_ID
LIMIT 5;"""
        ),
        (
            "9. Product Performance: Top 5 Revenue-Generating Products",
            "Evaluates individual product commercial success.",
            """SELECT 
    p.Product,
    p.Category,
    SUM(o.Quantity) AS Units_Sold,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    ROUND(SUM(o.Profit), 2) AS Profit
FROM Orders o
JOIN Products p ON o.Product_ID = p.Product_ID
GROUP BY p.Product, p.Category
ORDER BY Revenue DESC
LIMIT 5;"""
        ),
        (
            "10. Regional Performance: Revenue and Profit by Geographic Zone",
            "Aggregates financial results across geographic regions.",
            """SELECT 
    c.Region,
    COUNT(DISTINCT c.Customer_ID) AS Unique_Customers,
    COUNT(o.Order_ID) AS Total_Orders,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    ROUND(SUM(o.Profit), 2) AS Profit,
    ROUND(SUM(o.Profit) / SUM(o.Sales) * 100, 2) AS Profit_Margin_Pct
FROM Orders o
JOIN Customers c ON o.Customer_ID = c.Customer_ID
GROUP BY c.Region
ORDER BY Revenue DESC;"""
        ),
        (
            "11. Subquery: Customers with Lifetime Spend Above the Cohort Average",
            "Uses a scalar subquery in the HAVING clause to identify above-average accounts.",
            """SELECT 
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
LIMIT 5;"""
        ),
        (
            "12. Window Function: National Product Revenue Ranking (RANK)",
            "Ranks every product by nationwide revenue using RANK() OVER ().",
            """SELECT 
    p.Product,
    p.Category,
    ROUND(SUM(o.Sales), 2) AS Revenue,
    RANK() OVER (ORDER BY SUM(o.Sales) DESC) AS Revenue_Rank,
    DENSE_RANK() OVER (ORDER BY SUM(o.Sales) DESC) AS Dense_Rank
FROM Orders o
JOIN Products p ON o.Product_ID = p.Product_ID
GROUP BY p.Product, p.Category
LIMIT 5;"""
        ),
        (
            "13. Window Function with PARTITION BY: Top Products within Each Region",
            "Ranks products partitioned by customer region.",
            """WITH RegionalProductSales AS (
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
ORDER BY Region, Regional_Rank;"""
        ),
        (
            "14. Window Functions: Month-over-Month (MoM) Growth Analysis (LAG)",
            "Computes previous month's revenue and percentage growth rate using LAG().",
            """WITH MonthlyTotals AS (
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
LIMIT 6;"""
        )
    ]

    report_lines = [
        "# SQL Practice Queries — Execution Results Report",
        "",
        "**Database Engine**: SQLite 3 (Standard ANSI SQL Compliant)",
        "**Database Schema**: Normalized 3NF (Customers, Products, Orders)",
        "**Dataset Records**: 1,200 Orders, 249 Customers, 14 Products",
        "",
        "---",
        ""
    ]

    sql_file_lines = [
        "-- ========================================================================",
        "-- BLUESTOCKS DATA ANALYST INTERNSHIP — SQL PRACTICE SUITE",
        "-- Comprehensive Query Collection: Fundamentals to Advanced Window Functions",
        "-- Compatible with PostgreSQL, MySQL, and SQLite",
        "-- ========================================================================",
        ""
    ]

    for title, desc, query in queries:
        print(f"Executing: {title}...")
        df_result = pd.read_sql_query(query, conn)
        
        # Report formatting
        report_lines.append(f"## {title}")
        report_lines.append(f"*{desc}*")
        report_lines.append("")
        report_lines.append("```sql")
        report_lines.append(query)
        report_lines.append("```")
        report_lines.append("")
        report_lines.append("**Query Execution Result:**")
        report_lines.append("")
        report_lines.append(df_result.to_markdown(index=False))
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # SQL file formatting
        sql_file_lines.append(f"-- ========================================================================")
        sql_file_lines.append(f"-- {title}")
        sql_file_lines.append(f"-- {desc}")
        sql_file_lines.append(f"-- ========================================================================")
        sql_file_lines.append(query)
        sql_file_lines.append(";\n")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Saved execution report to {REPORT_PATH}")

    os.makedirs(os.path.dirname(SQL_FILE_PATH), exist_ok=True)
    with open(SQL_FILE_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_file_lines))
    print(f"Saved SQL script to {SQL_FILE_PATH}")

if __name__ == "__main__":
    conn = setup_database()
    execute_queries(conn)
    conn.close()
