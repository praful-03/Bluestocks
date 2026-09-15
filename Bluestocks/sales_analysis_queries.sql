-- ============================================================
-- SALES DATA ANALYSIS — SQL PRACTICE QUERIES
-- Customer / Order / Product Performance Analysis
-- ============================================================


-- ============================================================
-- 1. DATABASE STRUCTURE
-- ============================================================

-- Customers
CREATE TABLE Customers (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    Customer_Name VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(50),
    Region VARCHAR(30)
);

-- Products
CREATE TABLE Products (
    Product_ID INT PRIMARY KEY AUTO_INCREMENT,
    Product VARCHAR(100),
    Category VARCHAR(50),
    Sub_Category VARCHAR(50),
    Unit_Price DECIMAL(12,2)
);

-- Orders
CREATE TABLE Orders (
    Order_ID VARCHAR(20) PRIMARY KEY,
    Order_Date DATE,
    Customer_ID VARCHAR(20),
    Product_ID INT,
    Quantity INT,
    Discount DECIMAL(5,2),
    Sales DECIMAL(12,2),
    Profit DECIMAL(12,2),
    Payment_Mode VARCHAR(30),

    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
    FOREIGN KEY (Product_ID) REFERENCES Products(Product_ID)
);


-- ============================================================
-- 2. SELECT
-- ============================================================

-- Retrieve all orders
SELECT *
FROM Orders;

-- Select only important columns
SELECT
    Order_ID,
    Order_Date,
    Customer_ID,
    Quantity,
    Sales,
    Profit
FROM Orders;


-- ============================================================
-- 3. WHERE
-- ============================================================

-- Find orders with sales greater than ₹10,000
SELECT *
FROM Orders
WHERE Sales > 10000;

-- Find profitable orders
SELECT *
FROM Orders
WHERE Profit > 0;

-- Find orders from a particular date
SELECT *
FROM Orders
WHERE Order_Date >= '2025-07-01';


-- ============================================================
-- 4. ORDER BY
-- ============================================================

-- Find the highest-value orders
SELECT
    Order_ID,
    Sales,
    Profit
FROM Orders
ORDER BY Sales DESC;

-- Top 10 orders
SELECT
    Order_ID,
    Sales,
    Profit
FROM Orders
ORDER BY Sales DESC
LIMIT 10;


-- ============================================================
-- 5. AGGREGATE FUNCTIONS
-- ============================================================

-- Total revenue
SELECT SUM(Sales) AS Total_Revenue
FROM Orders;

-- Total profit
SELECT SUM(Profit) AS Total_Profit
FROM Orders;

-- Average order value
SELECT AVG(Sales) AS Average_Order_Value
FROM Orders;

-- Number of orders
SELECT COUNT(*) AS Total_Orders
FROM Orders;

-- Total quantity sold
SELECT SUM(Quantity) AS Total_Quantity
FROM Orders;


-- ============================================================
-- 6. GROUP BY
-- ============================================================

-- Revenue by customer
SELECT
    Customer_ID,
    SUM(Sales) AS Total_Revenue
FROM Orders
GROUP BY Customer_ID
ORDER BY Total_Revenue DESC;

-- Revenue by product
SELECT
    Product_ID,
    SUM(Sales) AS Total_Revenue
FROM Orders
GROUP BY Product_ID
ORDER BY Total_Revenue DESC;

-- Revenue by month
SELECT
    MONTH(Order_Date) AS Month,
    SUM(Sales) AS Revenue
FROM Orders
GROUP BY MONTH(Order_Date)
ORDER BY Month;


-- ============================================================
-- 7. HAVING
-- ============================================================

-- Find customers who generated more than ₹50,000 in revenue
-- (WHERE filters individual rows, HAVING filters groups)
SELECT
    Customer_ID,
    SUM(Sales) AS Total_Revenue
FROM Orders
GROUP BY Customer_ID
HAVING SUM(Sales) > 50000
ORDER BY Total_Revenue DESC;


-- ============================================================
-- 8. JOINS
-- ============================================================

-- Customer orders (Orders + Customers)
SELECT
    o.Order_ID,
    o.Order_Date,
    c.Customer_Name,
    c.City,
    c.Region,
    o.Sales,
    o.Profit
FROM Orders o
JOIN Customers c
    ON o.Customer_ID = c.Customer_ID;


-- ============================================================
-- 9. PRODUCT PERFORMANCE
-- ============================================================

-- Join Orders and Products — which products generate the most revenue?
SELECT
    p.Product,
    p.Category,
    SUM(o.Quantity) AS Units_Sold,
    SUM(o.Sales) AS Revenue,
    SUM(o.Profit) AS Profit
FROM Orders o
JOIN Products p
    ON o.Product_ID = p.Product_ID
GROUP BY
    p.Product,
    p.Category
ORDER BY Revenue DESC;


-- ============================================================
-- 10. CATEGORY PERFORMANCE
-- ============================================================

SELECT
    p.Category,
    SUM(o.Sales) AS Revenue,
    SUM(o.Profit) AS Profit,
    SUM(o.Quantity) AS Units_Sold
FROM Orders o
JOIN Products p
    ON o.Product_ID = p.Product_ID
GROUP BY p.Category
ORDER BY Revenue DESC;


-- ============================================================
-- 11. CUSTOMER PERFORMANCE
-- ============================================================

SELECT
    c.Customer_ID,
    c.Customer_Name,
    c.Region,
    COUNT(o.Order_ID) AS Number_of_Orders,
    SUM(o.Sales) AS Total_Revenue,
    SUM(o.Profit) AS Total_Profit
FROM Customers c
JOIN Orders o
    ON c.Customer_ID = o.Customer_ID
GROUP BY
    c.Customer_ID,
    c.Customer_Name,
    c.Region
ORDER BY Total_Revenue DESC;


-- ============================================================
-- 12. SUBQUERY
-- ============================================================

-- Find customers whose revenue is above the average customer revenue
SELECT
    Customer_ID,
    SUM(Sales) AS Total_Revenue
FROM Orders
GROUP BY Customer_ID
HAVING SUM(Sales) >
(
    SELECT AVG(Customer_Revenue)
    FROM
    (
        SELECT
            Customer_ID,
            SUM(Sales) AS Customer_Revenue
        FROM Orders
        GROUP BY Customer_ID
    ) AS Customer_Sales
)
ORDER BY Total_Revenue DESC;


-- ============================================================
-- 13. WINDOW FUNCTIONS
-- ============================================================

-- Rank products by revenue
SELECT
    p.Product,
    SUM(o.Sales) AS Revenue,
    RANK() OVER (
        ORDER BY SUM(o.Sales) DESC
    ) AS Revenue_Rank
FROM Orders o
JOIN Products p
    ON o.Product_ID = p.Product_ID
GROUP BY p.Product;


-- ============================================================
-- 14. REGIONAL PRODUCT RANKING
-- ============================================================

SELECT
    c.Region,
    p.Product,
    SUM(o.Sales) AS Revenue,
    RANK() OVER (
        PARTITION BY c.Region
        ORDER BY SUM(o.Sales) DESC
    ) AS Regional_Rank
FROM Orders o
JOIN Customers c
    ON o.Customer_ID = c.Customer_ID
JOIN Products p
    ON o.Product_ID = p.Product_ID
GROUP BY
    c.Region,
    p.Product;
