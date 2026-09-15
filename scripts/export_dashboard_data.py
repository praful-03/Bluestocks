"""
export_dashboard_data.py
------------------------
Generates a structured JSON data file for the executive web dashboard (dashboard/data.js)
from the cleaned dataset.
"""

import json
import pandas as pd

def generate_dashboard_data():
    df = pd.read_csv(r"l:\Bluestocks\data\processed\sales_analysis_cleaned.csv")
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    df['Month'] = df['Order_Date'].dt.strftime('%Y-%m')
    df['Year'] = df['Order_Date'].dt.year

    data = {
        "summary": {
            "total_sales": round(float(df['Sales'].sum()), 2),
            "total_profit": round(float(df['Profit'].sum()), 2),
            "margin_pct": round(float(df['Profit'].sum() / df['Sales'].sum() * 100), 2),
            "total_orders": int(len(df)),
            "unique_customers": int(df['Customer_ID'].nunique()),
            "aov": round(float(df['Sales'].sum() / len(df)), 2),
            "units_sold": int(df['Quantity'].sum())
        },
        "monthly": [],
        "categories": [],
        "regions": [],
        "top_products": [],
        "payment_modes": [],
        "transactions": []
    }

    # Monthly Trend
    monthly = df.groupby('Month').agg(
        sales=('Sales', 'sum'),
        profit=('Profit', 'sum'),
        orders=('Order_ID', 'count')
    ).reset_index().sort_values('Month')
    for _, row in monthly.iterrows():
        data["monthly"].append({
            "month": row['Month'],
            "sales": round(float(row['sales']), 2),
            "profit": round(float(row['profit']), 2),
            "orders": int(row['orders']),
            "margin_pct": round(float(row['profit'] / row['sales'] * 100), 2)
        })

    # Categories
    cat = df.groupby('Category').agg(
        sales=('Sales', 'sum'),
        profit=('Profit', 'sum'),
        orders=('Order_ID', 'count'),
        units=('Quantity', 'sum')
    ).reset_index().sort_values('sales', ascending=False)
    for _, row in cat.iterrows():
        data["categories"].append({
            "category": row['Category'],
            "sales": round(float(row['sales']), 2),
            "profit": round(float(row['profit']), 2),
            "orders": int(row['orders']),
            "units": int(row['units']),
            "margin_pct": round(float(row['profit'] / row['sales'] * 100), 2)
        })

    # Regions
    reg = df.groupby('Region').agg(
        sales=('Sales', 'sum'),
        profit=('Profit', 'sum'),
        orders=('Order_ID', 'count'),
        customers=('Customer_ID', 'nunique')
    ).reset_index().sort_values('sales', ascending=False)
    for _, row in reg.iterrows():
        data["regions"].append({
            "region": row['Region'],
            "sales": round(float(row['sales']), 2),
            "profit": round(float(row['profit']), 2),
            "orders": int(row['orders']),
            "customers": int(row['customers']),
            "margin_pct": round(float(row['profit'] / row['sales'] * 100), 2)
        })

    # Top Products
    top_p = df.groupby(['Product', 'Category']).agg(
        sales=('Sales', 'sum'),
        profit=('Profit', 'sum'),
        units=('Quantity', 'sum')
    ).reset_index().sort_values('sales', ascending=False)
    for _, row in top_p.iterrows():
        data["top_products"].append({
            "product": row['Product'],
            "category": row['Category'],
            "sales": round(float(row['sales']), 2),
            "profit": round(float(row['profit']), 2),
            "units": int(row['units']),
            "margin_pct": round(float(row['profit'] / row['sales'] * 100), 2)
        })

    # Payment Modes
    pm = df.groupby('Payment_Mode').agg(
        sales=('Sales', 'sum'),
        orders=('Order_ID', 'count')
    ).reset_index().sort_values('sales', ascending=False)
    for _, row in pm.iterrows():
        data["payment_modes"].append({
            "mode": row['Payment_Mode'],
            "sales": round(float(row['sales']), 2),
            "orders": int(row['orders'])
        })

    # Sample Transactions for interactive table (latest 150)
    recent = df.sort_values('Order_Date', ascending=False).head(150)
    for _, row in recent.iterrows():
        data["transactions"].append({
            "order_id": str(row['Order_ID']),
            "date": str(row['Order_Date'].strftime('%Y-%m-%d')),
            "customer": str(row['Customer_Name']),
            "region": str(row['Region']),
            "category": str(row['Category']),
            "product": str(row['Product']),
            "qty": int(row['Quantity']),
            "sales": round(float(row['Sales']), 2),
            "profit": round(float(row['Profit']), 2),
            "margin_pct": round(float(row['Profit_Margin_Pct']), 2),
            "payment": str(row['Payment_Mode'])
        })

    js_content = f"const DASHBOARD_DATA = {json.dumps(data, indent=2)};\n"
    out_path = r"l:\Bluestocks\dashboard\data.js"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Generated {out_path} ({len(js_content):,} bytes)")

if __name__ == "__main__":
    generate_dashboard_data()
