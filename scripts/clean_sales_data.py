"""
clean_sales_data.py
-------------------
Systematic data cleaning and validation pipeline for the Sales Analysis dataset.
Produces:
1. data/processed/sales_analysis_cleaned.csv
2. data/processed/cleaning_audit_log.json
3. Star schema tables for SQL and Power BI (Customers, Products, Orders, Dates)
"""

import os
import json
import numpy as np
import pandas as pd

def clean_dataset(raw_csv_path: str, output_csv_path: str):
    print(f"Loading raw dataset from {raw_csv_path}...")
    df_raw = pd.read_csv(raw_csv_path)
    initial_shape = df_raw.shape
    print(f"Initial shape: {initial_shape}")

    audit = {
        "initial_rows": initial_shape[0],
        "initial_cols": initial_shape[1],
        "null_counts_before": df_raw.isnull().sum().to_dict(),
        "duplicate_rows_removed": 0,
        "nulls_resolved": {},
        "outliers_detected": {},
        "final_rows": 0,
        "final_cols": 0
    }

    df = df_raw.copy()

    # 1. Duplicate Removal
    # An exact duplicate across all or core business keys (Order_ID)
    dups_count = int(df.duplicated(subset=['Order_ID']).sum())
    df = df.drop_duplicates(subset=['Order_ID'], keep='first').reset_index(drop=True)
    audit["duplicate_rows_removed"] = dups_count
    print(f"Removed {dups_count} duplicate rows. New shape: {df.shape}")

    # 2. String Cleaning & Trimming
    string_cols = ['Customer_Name', 'Region', 'State', 'City', 'Category', 'Sub_Category', 'Product', 'Payment_Mode']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', np.nan)

    # 3. Missing Value Resolution
    # Customer_Name: If missing, check if Customer_ID has other orders with a known name
    cust_id_name_map = df.dropna(subset=['Customer_Name']).groupby('Customer_ID')['Customer_Name'].first().to_dict()
    df['Customer_Name'] = df['Customer_Name'].fillna(df['Customer_ID'].map(cust_id_name_map))
    # If still missing, fill with "Unknown Customer"
    df['Customer_Name'] = df['Customer_Name'].fillna('Unknown Customer')

    # City: If missing, check State or fill by most frequent City in that State
    for state in df['State'].unique():
        state_cities = df[df['State'] == state]['City'].dropna()
        if not state_cities.empty:
            mode_city = state_cities.mode()[0]
            df.loc[(df['State'] == state) & (df['City'].isna()), 'City'] = mode_city
    df['City'] = df['City'].fillna('Unknown City')

    # Payment_Mode: Impute mode
    mode_pm = df['Payment_Mode'].dropna().mode()[0]
    df['Payment_Mode'] = df['Payment_Mode'].fillna(mode_pm)

    audit["null_counts_after"] = df.isnull().sum().to_dict()

    # 4. Data Type Conversions & Standardizations
    df['Order_Date'] = pd.to_datetime(df['Order_Date']).dt.strftime('%Y-%m-%d')
    df['Quantity'] = df['Quantity'].astype(int)
    df['Unit_Price'] = df['Unit_Price'].astype(float).round(2)
    df['Discount'] = df['Discount'].astype(float).round(2)
    df['Sales'] = df['Sales'].astype(float).round(2)
    df['Profit'] = df['Profit'].astype(float).round(2)

    # 5. Arithmetic Consistency Check
    # Expected Sales = Quantity * Unit_Price * (1 - Discount)
    expected_sales = (df['Quantity'] * df['Unit_Price'] * (1 - df['Discount'])).round(2)
    discrepancy = (df['Sales'] - expected_sales).abs()
    large_disc = (discrepancy > 1.0).sum()
    print(f"Sales arithmetic discrepancies (> INR 1.00): {large_disc}")
    # Align sales to precise rounded arithmetic
    df['Calculated_Sales'] = expected_sales
    # Profit Margin %
    df['Profit_Margin_Pct'] = np.where(df['Sales'] > 0, (df['Profit'] / df['Sales'] * 100).round(2), 0.0)

    # 6. Outlier Detection (IQR Method)
    for col in ['Sales', 'Quantity', 'Profit']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
        audit["outliers_detected"][col] = {
            "Q1": round(float(Q1), 2),
            "Q3": round(float(Q3), 2),
            "IQR": round(float(IQR), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
            "outlier_count": int(outliers)
        }
        print(f"Outliers in {col}: {outliers} rows outside [{lower_bound:.2f}, {upper_bound:.2f}]")

    audit["final_rows"] = df.shape[0]
    audit["final_cols"] = df.shape[1]

    # 7. Save Cleaned Dataset
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    print(f"Saved cleaned dataset to {output_csv_path} ({df.shape})")

    audit_path = os.path.join(os.path.dirname(output_csv_path), "cleaning_audit_log.json")
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)
    print(f"Saved cleaning audit log to {audit_path}")

    # 8. Export Star Schema tables for SQL & Power BI
    export_star_schema(df)

    return df

def export_star_schema(df: pd.DataFrame):
    power_bi_dir = r"l:\Bluestocks\data\power_bi"
    os.makedirs(power_bi_dir, exist_ok=True)

    # Dim_Customer
    dim_customer = df[['Customer_ID', 'Customer_Name', 'City', 'State', 'Region']].drop_duplicates(subset=['Customer_ID']).reset_index(drop=True)
    dim_customer.to_csv(os.path.join(power_bi_dir, "dim_customers.csv"), index=False)

    # Dim_Product
    # Derive unique product ID mapping
    dim_product = df[['Product', 'Category', 'Sub_Category', 'Unit_Price']].drop_duplicates(subset=['Product']).reset_index(drop=True)
    dim_product['Product_ID'] = range(1, len(dim_product) + 1)
    # Reorder columns
    dim_product = dim_product[['Product_ID', 'Product', 'Category', 'Sub_Category', 'Unit_Price']]
    dim_product.to_csv(os.path.join(power_bi_dir, "dim_products.csv"), index=False)

    # Map Product_ID back to df
    prod_map = dict(zip(dim_product['Product'], dim_product['Product_ID']))
    df['Product_ID'] = df['Product'].map(prod_map)

    # Dim_Date
    dates = pd.to_datetime(df['Order_Date'].unique())
    date_df = pd.DataFrame({'Date': dates}).sort_values('Date').reset_index(drop=True)
    date_df['Date_Key'] = date_df['Date'].dt.strftime('%Y%m%d').astype(int)
    date_df['Year'] = date_df['Date'].dt.year
    date_df['Quarter'] = 'Q' + date_df['Date'].dt.quarter.astype(str)
    date_df['Month'] = date_df['Date'].dt.month
    date_df['Month_Name'] = date_df['Date'].dt.strftime('%B')
    date_df['Month_Year'] = date_df['Date'].dt.strftime('%b %Y')
    date_df['Day'] = date_df['Date'].dt.day
    date_df['Day_of_Week'] = date_df['Date'].dt.strftime('%A')
    date_df['Date'] = date_df['Date'].dt.strftime('%Y-%m-%d')
    date_df.to_csv(os.path.join(power_bi_dir, "dim_date.csv"), index=False)

    # Fact_Sales
    fact_sales = df[['Order_ID', 'Order_Date', 'Customer_ID', 'Product_ID', 'Quantity', 'Unit_Price', 'Discount', 'Sales', 'Profit', 'Profit_Margin_Pct', 'Payment_Mode']]
    fact_sales.to_csv(os.path.join(power_bi_dir, "fact_sales.csv"), index=False)

    print(f"Exported Star Schema tables to {power_bi_dir}:")
    print(f"  dim_customers.csv: {dim_customer.shape}")
    print(f"  dim_products.csv: {dim_product.shape}")
    print(f"  dim_date.csv: {date_df.shape}")
    print(f"  fact_sales.csv: {fact_sales.shape}")

if __name__ == "__main__":
    raw_path = r"l:\Bluestocks\Sales_Analysis_Raw_Dataset.csv"
    out_path = r"l:\Bluestocks\data\processed\sales_analysis_cleaned.csv"
    clean_dataset(raw_path, out_path)
