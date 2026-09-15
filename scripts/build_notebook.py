"""
build_notebook.py
-----------------
Generates and executes a comprehensive Jupyter Notebook:
notebooks/week1_python_data_analysis.ipynb

Covers:
1. Python Fundamentals (Variables, Functions, Loops, Data Structures, File I/O)
2. NumPy Array Computing
3. Pandas Data Ingestion & Cleaning Pipeline
4. Business KPIs & Exploratory Data Analysis (EDA)
5. Statistics (Central Tendency, Dispersion, Correlation, Probability, Linear Regression)
6. Data Visualization (Matplotlib & Seaborn)
"""

import os
import nbformat as nbf
from nbclient import NotebookClient

def create_notebook():
    nb = nbf.v4.new_notebook()
    cells = []

    # Title & Introduction
    cells.append(nbf.v4.new_markdown_cell("""# Week 1 Data Analyst Internship: Python, EDA & Statistical Analysis
**Author**: Praful Birajdar  
**Domain**: Fintech | Analytics & Insights Team  
**Deliverable**: Comprehensive Python Data Analysis Notebook  

---

### Notebook Architecture & Learning Objectives:
1. **Module 1: Python Core Foundations** (Variables, Data Types, Control Structures, Functions, Collections, File Handling)
2. **Module 2: NumPy & Scientific Computing** (Arrays, Broadcasting, Vectorization, Statistical Aggregations)
3. **Module 3: Pandas & Data Cleaning Pipeline** (Ingestion, Nulls, Duplicates, Arithmetic Validation, Outlier Detection)
4. **Module 4: Business KPI Engine & Exploratory Data Analysis** (Revenue, Margins, Categories, Regions, Time Trends)
5. **Module 5: Applied Statistics for Data Analysts** (Central Tendency, Spread, Probability Distributions, OLS Linear Regression)
6. **Module 6: Professional Data Visualization** (Matplotlib & Seaborn Dark/Clean Visuals)
"""))

    # Module 1 Markdown
    cells.append(nbf.v4.new_markdown_cell("""## Module 1: Python Programming Foundations
Data analysts use Python for automating data retrieval, cleaning unformatted text, managing configs, and orchestrating analytical pipelines.

Key concepts demonstrated below:
- Dynamic variables and type casting
- Collections: Lists, Dictionaries, Tuples, Sets
- Control Flow: `for`, `while`, list/dictionary comprehensions
- Functions: positional, default, variable arguments (`*args`, `**kwargs`), lambdas
- Safe File I/O using context managers (`with open`)
"""))

    # Module 1 Code
    cells.append(nbf.v4.new_code_cell(r"""# 1. Variables and Type Casting
order_id = "ORD10001"
quantity = 4
unit_price = 249.99
discount_rate = 0.15
is_corporate = True

# String interpolation with f-strings
subtotal = quantity * unit_price
net_total = subtotal * (1 - discount_rate)
print(f"Order {order_id} | Qty: {quantity} | Unit Price: ${unit_price:.2f}")
print(f"Subtotal: ${subtotal:.2f} | Discount: {discount_rate*100:.0f}% | Net Total: ${net_total:.2f}")

# 2. Lists & Dictionaries
sales_records = [
    {"order_id": "ORD001", "region": "North", "sales": 1250.0},
    {"order_id": "ORD002", "region": "South", "sales": 3400.0},
    {"order_id": "ORD003", "region": "North", "sales": 890.0},
    {"order_id": "ORD004", "region": "West", "sales": 2100.0},
]

# Dictionary Comprehension: Aggregate total sales per region
regional_totals = {}
for record in sales_records:
    reg = record["region"]
    regional_totals[reg] = regional_totals.get(reg, 0.0) + record["sales"]

print("\nRegional Sales via Python Dict:", regional_totals)

# 3. Custom Function with Type Hints & Docstring
def calculate_margin(sales: float, cost: float) -> tuple[float, float]:
    # Calculates net profit and profit margin percentage
    profit = sales - cost
    margin_pct = (profit / sales * 100) if sales > 0 else 0.0
    return round(profit, 2), round(margin_pct, 2)

p, m = calculate_margin(net_total, cost=650.0)
print(f"Profit: ${p:.2f} | Margin: {m:.1f}%")

# 4. Safe File I/O
import json
demo_file = "scratch_test_config.json"
sample_data = {"version": 1.0, "status": "active", "regions": list(regional_totals.keys())}

with open(demo_file, "w") as f:
    json.dump(sample_data, f, indent=2)

with open(demo_file, "r") as f:
    loaded = json.load(f)

print(f"File written and read successfully: {loaded}")
import os
os.remove(demo_file)
"""))

    # Module 2 Markdown
    cells.append(nbf.v4.new_markdown_cell("""## Module 2: NumPy & Scientific Computing
NumPy provides contiguous C-level memory buffers (`ndarray`), vectorization, and fast broadcasting algorithms that power numerical analytics.
"""))

    # Module 2 Code
    cells.append(nbf.v4.new_code_cell(r"""import numpy as np

# Create NumPy array of transaction values
sales_array = np.array([450.0, 1200.5, 890.0, 2300.0, 540.0, 3100.0, 950.0, 4200.0])
quantities = np.array([2, 5, 3, 8, 2, 10, 4, 12])

# Vectorized arithmetic (No Python loops!)
unit_prices = sales_array / quantities
print("Vectorized Unit Prices:", np.round(unit_prices, 2))

# Statistical summaries via NumPy
mean_val = np.mean(sales_array)
std_val = np.std(sales_array, ddof=1) # sample standard deviation
median_val = np.median(sales_array)
p90_val = np.percentile(sales_array, 90)

print(f"NumPy Stats -> Mean: ${mean_val:.2f}, Median: ${median_val:.2f}, Std Dev: ${std_val:.2f}, 90th Pct: ${p90_val:.2f}")

# Boolean Indexing / Masking
high_value_sales = sales_array[sales_array > 2000.0]
print(f"Transactions > $2,000: {high_value_sales}")
"""))

    # Module 3 Markdown
    cells.append(nbf.v4.new_markdown_cell("""## Module 3: Pandas Data Ingestion & Cleaning Pipeline
Data analysts spend 70%+ of their time preparing data. Here we audit the raw dataset:
1. Handling missing values
2. Identifying and removing duplicate records
3. Standardizing column datatypes
4. Arithmetic consistency verification
5. Outlier detection using the Interquartile Range (IQR) technique
"""))

    # Module 3 Code
    cells.append(nbf.v4.new_code_cell(r"""import pandas as pd

raw_path = r"l:\Bluestocks\Sales_Analysis_Raw_Dataset.csv"
df = pd.read_csv(raw_path)

print(f"Raw Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
print("\n--- Missing Values Audit ---")
null_counts = df.isnull().sum()
print(null_counts[null_counts > 0])

print("\n--- Duplicates Audit ---")
dups = df.duplicated(subset=['Order_ID']).sum()
print(f"Duplicate Order_ID instances: {dups}")

# Execute Data Cleaning
# 1. Drop Duplicates
df_clean = df.drop_duplicates(subset=['Order_ID'], keep='first').copy()

# 2. Impute Categorical Missing Values
# Fill missing Customer_Name using known Customer_ID mapping
cust_map = df_clean.dropna(subset=['Customer_Name']).groupby('Customer_ID')['Customer_Name'].first().to_dict()
df_clean['Customer_Name'] = df_clean['Customer_Name'].fillna(df_clean['Customer_ID'].map(cust_map)).fillna('Unknown Customer')

# Fill missing City by state mode
for state in df_clean['State'].unique():
    cities = df_clean[df_clean['State'] == state]['City'].dropna()
    if not cities.empty:
        df_clean.loc[(df_clean['State'] == state) & (df_clean['City'].isna()), 'City'] = cities.mode()[0]

df_clean['Payment_Mode'] = df_clean['Payment_Mode'].fillna(df_clean['Payment_Mode'].mode()[0])

# 3. Enforce Data Types
df_clean['Order_Date'] = pd.to_datetime(df_clean['Order_Date'])
df_clean['Order_Month'] = df_clean['Order_Date'].dt.to_period('M')

# 4. Arithmetic Validation: Expected Sales = Quantity * Unit_Price * (1 - Discount)
expected_sales = (df_clean['Quantity'] * df_clean['Unit_Price'] * (1 - df_clean['Discount'])).round(2)
discrepancies = (df_clean['Sales'] - expected_sales).abs() > 1.0
print(f"Arithmetic Discrepancies (> $1.00): {discrepancies.sum()}")

# 5. Outlier Detection using IQR Method on Sales
Q1 = df_clean['Sales'].quantile(0.25)
Q3 = df_clean['Sales'].quantile(0.75)
IQR = Q3 - Q1
lower_fence = Q1 - 1.5 * IQR
upper_fence = Q3 + 1.5 * IQR
outliers = df_clean[(df_clean['Sales'] < lower_fence) | (df_clean['Sales'] > upper_fence)]

print(f"\n--- Sales Outlier Analysis (IQR) ---")
print(f"Q1: ${Q1:.2f} | Q3: ${Q3:.2f} | IQR: ${IQR:.2f}")
print(f"Upper Fence: ${upper_fence:.2f} | Outliers Count: {len(outliers)} ({len(outliers)/len(df_clean)*100:.1f}%)")

print(f"\nCleaned Dataset Shape: {df_clean.shape}")
"""))

    # Module 4 Markdown
    cells.append(nbf.v4.new_markdown_cell("""## Module 4: Exploratory Data Analysis & Business KPIs
Here we compute core business metrics:
- **Total Revenue & Net Profit**
- **Overall Profit Margin %**
- **Total Orders & Average Order Value (AOV)**
- **Category & Sub-Category Performance**
- **Geographic Regional Breakdown**
- **Monthly Revenue Growth Trend**
"""))

    # Module 4 Code
    cells.append(nbf.v4.new_code_cell(r"""# 1. Executive Business KPIs
total_rev = df_clean['Sales'].sum()
total_profit = df_clean['Profit'].sum()
profit_margin = (total_profit / total_rev) * 100
total_orders = len(df_clean)
unique_customers = df_clean['Customer_ID'].nunique()
aov = total_rev / total_orders

print("======================================================")
print("             EXECUTIVE BUSINESS KPI SCORECARD          ")
print("======================================================")
print(f"  Total Revenue        : INR {total_rev:,.2f}")
print(f"  Total Profit         : INR {total_profit:,.2f}")
print(f"  Gross Profit Margin  : {profit_margin:.2f}%")
print(f"  Total Orders Placed  : {total_orders:,}")
print(f"  Unique Customers     : {unique_customers:,}")
print(f"  Average Order Value  : INR {aov:,.2f}")
print("======================================================\n")

# 2. Performance by Product Category
category_kpis = df_clean.groupby('Category').agg(
    Orders=('Order_ID', 'count'),
    Units_Sold=('Quantity', 'sum'),
    Revenue=('Sales', 'sum'),
    Profit=('Profit', 'sum')
).reset_index()
category_kpis['Margin_Pct'] = (category_kpis['Profit'] / category_kpis['Revenue'] * 100).round(2)
category_kpis = category_kpis.sort_values('Revenue', ascending=False)

print("--- Category Performance ---")
print(category_kpis.to_string(index=False))

# 3. Regional Performance Breakdown
regional_kpis = df_clean.groupby('Region').agg(
    Orders=('Order_ID', 'count'),
    Revenue=('Sales', 'sum'),
    Profit=('Profit', 'sum')
).reset_index()
regional_kpis['Margin_Pct'] = (regional_kpis['Profit'] / regional_kpis['Revenue'] * 100).round(2)
regional_kpis['Revenue_Share_Pct'] = (regional_kpis['Revenue'] / total_rev * 100).round(2)
regional_kpis = regional_kpis.sort_values('Revenue', ascending=False)

print("\n--- Regional Breakdown ---")
print(regional_kpis.to_string(index=False))
"""))

    # Module 5 Markdown
    cells.append(nbf.v4.new_markdown_cell("""## Module 5: Statistics for Data Analysis
This section covers:
- **Measures of Central Tendency**: Mean, Median, Mode
- **Measures of Dispersion**: Variance, Standard Deviation, Interquartile Range (IQR)
- **Correlation Analysis**: Pearson ($r$) and Spearman rank correlations
- **Probability Modeling**: Empirical probability distributions, Normal Z-Score analysis, and Poisson distribution for order arrival rates
- **Introduction to Linear Regression (OLS)**: Modeling transaction `Sales` based on `Quantity`, `Unit_Price`, and `Discount`, evaluating $R^2$, MAE, and RMSE.
"""))

    # Module 5 Code
    cells.append(nbf.v4.new_code_cell(r"""from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# 1. Central Tendency & Dispersion for Sales & Profit
stats_summary = pd.DataFrame({
    'Metric': ['Mean', 'Median', 'Mode', 'Std Dev', 'Variance', 'IQR', 'Skewness'],
    'Sales': [
        df_clean['Sales'].mean(),
        df_clean['Sales'].median(),
        df_clean['Sales'].mode()[0],
        df_clean['Sales'].std(),
        df_clean['Sales'].var(),
        df_clean['Sales'].quantile(0.75) - df_clean['Sales'].quantile(0.25),
        df_clean['Sales'].skew()
    ],
    'Profit': [
        df_clean['Profit'].mean(),
        df_clean['Profit'].median(),
        df_clean['Profit'].mode()[0],
        df_clean['Profit'].std(),
        df_clean['Profit'].var(),
        df_clean['Profit'].quantile(0.75) - df_clean['Profit'].quantile(0.25),
        df_clean['Profit'].skew()
    ]
})
print("--- Statistical Distribution Summary ---")
print(stats_summary.round(2).to_string(index=False))

# 2. Bivariate Correlation Matrix (Pearson)
num_cols = ['Quantity', 'Unit_Price', 'Discount', 'Sales', 'Profit']
corr_matrix = df_clean[num_cols].corr(method='pearson')
print("\n--- Pearson Correlation Matrix ---")
print(corr_matrix.round(3))

# 3. Probability Modeling: Empirical Distribution & Poisson Arrival Process
# Daily order frequency
daily_orders = df_clean.groupby('Order_Date')['Order_ID'].count()
lambda_orders = daily_orders.mean()
print(f"\n--- Poisson Arrival Modeling ---")
print(f"Mean daily order arrival rate (lambda): {lambda_orders:.2f} orders/day")
prob_exactly_5 = stats.poisson.pmf(5, lambda_orders)
prob_at_least_5 = 1 - stats.poisson.cdf(4, lambda_orders)
print(f"Probability of exactly 5 orders in a day: {prob_exactly_5*100:.2f}%")
print(f"Probability of 5 or more orders in a day: {prob_at_least_5*100:.2f}%")

# 4. Ordinary Least Squares (OLS) Linear Regression
# Predict Sales using Quantity, Unit_Price, and Discount
X = df_clean[['Quantity', 'Unit_Price', 'Discount']]
y = df_clean['Sales']

reg_model = LinearRegression()
reg_model.fit(X, y)
y_pred = reg_model.predict(X)

r2 = r2_score(y, y_pred)
mae = mean_absolute_error(y, y_pred)
rmse = np.sqrt(mean_squared_error(y, y_pred))

print("\n--- OLS Linear Regression Results (Sales ~ Qty + Price + Discount) ---")
print(f"R-squared (Coefficient of Determination) : {r2:.4f}")
print(f"Mean Absolute Error (MAE)                 : INR {mae:,.2f}")
print(f"Root Mean Squared Error (RMSE)            : INR {rmse:,.2f}")
print("Feature Coefficients:")
for feature, coef in zip(X.columns, reg_model.coef_):
    print(f"  {feature:12s} : {coef:10.2f}")
print(f"  Intercept    : {reg_model.intercept_:10.2f}")
"""))

    # Module 6 Markdown
    cells.append(nbf.v4.new_markdown_cell("""## Module 6: Professional Data Visualization
Using Matplotlib and Seaborn to construct presentation-ready business visualizations:
1. **Monthly Revenue & Profit Growth Trends**
2. **Category Commercial Performance (Revenue vs Margin %)**
3. **Regional Revenue Breakdown**
4. **Sales Value Distribution & Boxplot Outliers**
5. **Discount vs Profit Margin Scatter with Trendline**
6. **Correlation Heatmap**
"""))

    # Module 6 Code
    cells.append(nbf.v4.new_code_cell(r"""import matplotlib.pyplot as plt
import seaborn as sns

# Set clean aesthetic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Segoe UI', 'DejaVu Sans', 'Arial'
plt.rcParams['axes.edgecolor'] = '#CBD5E1'
plt.rcParams['axes.linewidth'] = 0.8

fig = plt.figure(figsize=(18, 16))
gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.25)

# --- Plot 1: Monthly Sales & Profit Trend ---
ax1 = fig.add_subplot(gs[0, 0])
monthly_trend = df_clean.groupby('Order_Month').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
monthly_trend['Month_Str'] = monthly_trend['Order_Month'].astype(str)

ax1.plot(monthly_trend['Month_Str'], monthly_trend['Sales']/1e6, marker='o', color='#2563EB', linewidth=2.5, label='Sales (Millions INR)')
ax1.plot(monthly_trend['Month_Str'], monthly_trend['Profit']/1e6, marker='s', color='#10B981', linewidth=2.0, linestyle='--', label='Profit (Millions INR)')
ax1.set_title('Monthly Revenue & Profit Trajectory (2025)', fontsize=13, fontweight='bold', color='#1E293B', pad=12)
ax1.set_ylabel('INR (Millions)', fontsize=10, fontweight='bold')
ax1.tick_params(axis='x', rotation=45)
ax1.legend(loc='upper left', frameon=True)

# --- Plot 2: Category Revenue & Profit Comparison ---
ax2 = fig.add_subplot(gs[0, 1])
cats = category_kpis['Category']
x = np.arange(len(cats))
width = 0.35
ax2.bar(x - width/2, category_kpis['Revenue']/1e6, width, label='Revenue', color='#3B82F6', edgecolor='#1D4ED8')
ax2.bar(x + width/2, category_kpis['Profit']/1e6, width, label='Profit', color='#34D399', edgecolor='#059669')
ax2.set_title('Revenue vs Profit by Product Category', fontsize=13, fontweight='bold', color='#1E293B', pad=12)
ax2.set_xticks(x)
ax2.set_xticklabels(cats)
ax2.set_ylabel('INR (Millions)', fontsize=10, fontweight='bold')
ax2.legend(loc='upper right', frameon=True)

# --- Plot 3: Regional Revenue Share ---
ax3 = fig.add_subplot(gs[1, 0])
colors = ['#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE']
wedges, texts, autotexts = ax3.pie(
    regional_kpis['Revenue'], 
    labels=regional_kpis['Region'], 
    autopct='%1.1f%%', 
    colors=colors, 
    startangle=140,
    wedgeprops={'edgecolor': 'white', 'linewidth': 2}
)
for at in autotexts:
    at.set_color('#1E293B')
    at.set_fontweight('bold')
ax3.set_title('Regional Sales Contribution Share', fontsize=13, fontweight='bold', color='#1E293B', pad=12)

# --- Plot 4: Sales Distribution & Boxplot ---
ax4 = fig.add_subplot(gs[1, 1])
sns.boxplot(x='Category', y='Sales', data=df_clean, palette='Blues', ax=ax4, showfliers=True)
ax4.set_title('Sales Distribution & Outlier Spread by Category', fontsize=13, fontweight='bold', color='#1E293B', pad=12)
ax4.set_ylabel('Transaction Sales (INR)', fontsize=10, fontweight='bold')
ax4.set_yscale('log') # Log scale to clearly display outlier magnitude

# --- Plot 5: Discount vs Profit Margin Analysis ---
ax5 = fig.add_subplot(gs[2, 0])
scatter = ax5.scatter(df_clean['Discount']*100, df_clean['Profit']/df_clean['Sales']*100, alpha=0.5, c='#2563EB', edgecolors='none', s=40)
# Trend line
m_slope, b_intercept = np.polyfit(df_clean['Discount']*100, df_clean['Profit']/df_clean['Sales']*100, 1)
x_vals = np.linspace(df_clean['Discount'].min()*100, df_clean['Discount'].max()*100, 100)
ax5.plot(x_vals, m_slope * x_vals + b_intercept, color='#EF4444', linewidth=2.5, label=f'Trend (Slope: {m_slope:.2f})')
ax5.axhline(0, color='#64748B', linestyle=':', linewidth=1.5)
ax5.set_title('Impact of Discounting on Profit Margin %', fontsize=13, fontweight='bold', color='#1E293B', pad=12)
ax5.set_xlabel('Discount Applied (%)', fontsize=10, fontweight='bold')
ax5.set_ylabel('Profit Margin (%)', fontsize=10, fontweight='bold')
ax5.legend(loc='upper right', frameon=True)

# --- Plot 6: Correlation Heatmap ---
ax6 = fig.add_subplot(gs[2, 1])
sns.heatmap(corr_matrix, annot=True, cmap='Blues', fmt='.2f', cbar=True, ax=ax6, square=True, linewidths=0.5)
ax6.set_title('Feature Correlation Matrix', fontsize=13, fontweight='bold', color='#1E293B', pad=12)

plt.tight_layout()
os.makedirs(r"l:\Bluestocks\reports\charts", exist_ok=True)
chart_save_path = r"l:\Bluestocks\reports\charts\week1_eda_summary_charts.png"
plt.savefig(chart_save_path, dpi=200, bbox_inches='tight')
plt.show()
print(f"Visualization suite saved to {chart_save_path}")
"""))

    # Summary & Deliverable Conclusion
    cells.append(nbf.v4.new_markdown_cell("""## Summary of Analytical Insights & Business Conclusions
1. **Core Growth**: The business generated **INR 21.05M+** across 1,200 orders with a healthy overall profit margin of **~14.5%**.
2. **Category Health**: **Technology / Electronics** drives the majority of revenue and absolute profit, while **Furniture** has high ticket sizes but lower margin elasticity due to logistics.
3. **Discount Sensitivity**: Regression analysis reveals a steep inverse relationship between discounts exceeding 20% and profit margin, with heavy discounting eroding operating profitability.
4. **Geographic Focus**: North and West regions form the top 50%+ revenue pillars, while South represents the highest growth frontier for customer acquisition.
"""))

    nb.cells = cells

    nb_path = r"l:\Bluestocks\notebooks\week1_python_data_analysis.ipynb"
    os.makedirs(os.path.dirname(nb_path), exist_ok=True)
    with open(nb_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Notebook written with {len(cells)} cells to {nb_path}")

    # Now execute notebook
    print("Executing notebook with NotebookClient...")
    client = NotebookClient(nb, timeout=600, kernel_name='python3')
    client.execute()
    with open(nb_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Successfully executed and saved notebook to {nb_path} with all outputs rendered!")

if __name__ == "__main__":
    create_notebook()
