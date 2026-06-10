import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================================
# Advanced E-Commerce Database Generator
# Creates: ecommerce_data.db
# Period: Jan 2023 - Dec 2025 (3 Years)
# ==========================================================

np.random.seed(42)

DB_NAME = "ecommerce_data.db"

# ==========================================================
# CONFIGURATION
# ==========================================================

NUM_CUSTOMERS = 5000
NUM_PRODUCTS = 120
MIN_TRANSACTIONS = 50000

# ==========================================================
# CUSTOMERS TABLE
# ==========================================================

countries = [
    "USA", "Canada", "UK", "Germany", "France",
    "India", "Australia", "Brazil", "Japan", "Mexico"
]

acquisition_channels = [
    "Organic Search",
    "Paid Search",
    "Social Media",
    "Email",
    "Referral",
    "Affiliate"
]

customers_df = pd.DataFrame({
    "customer_id": np.arange(1, NUM_CUSTOMERS + 1),
    "country": np.random.choice(
        countries,
        NUM_CUSTOMERS,
        p=[0.25, 0.08, 0.12, 0.08, 0.07, 0.15, 0.06, 0.08, 0.06, 0.05]
    ),
    "acquisition_channel": np.random.choice(
        acquisition_channels,
        NUM_CUSTOMERS
    )
})

# ==========================================================
# PRODUCTS TABLE
# ==========================================================

categories = {
    "Electronics": [
        "Laptop", "Smartphone", "Tablet", "Monitor",
        "Headphones", "Keyboard", "Mouse", "Camera"
    ],
    "Home & Kitchen": [
        "Blender", "Coffee Maker", "Cookware Set",
        "Air Fryer", "Vacuum Cleaner"
    ],
    "Fashion": [
        "T-Shirt", "Jeans", "Sneakers",
        "Jacket", "Backpack"
    ],
    "Sports": [
        "Yoga Mat", "Dumbbells", "Football",
        "Tennis Racket", "Running Shoes"
    ],
    "Beauty": [
        "Face Cream", "Shampoo",
        "Perfume", "Lipstick"
    ],
    "Books": [
        "Business Book", "Novel",
        "Data Science Book", "Cookbook"
    ]
}

products = []

for pid in range(1, NUM_PRODUCTS + 1):
    category = np.random.choice(list(categories.keys()))
    product_name = (
        np.random.choice(categories[category])
        + f" Model {pid}"
    )

    unit_cost = round(np.random.uniform(5, 500), 2)
    margin = np.random.uniform(1.25, 2.2)
    unit_price = round(unit_cost * margin, 2)

    products.append([
        pid,
        product_name,
        category,
        unit_cost,
        unit_price
    ])

products_df = pd.DataFrame(
    products,
    columns=[
        "product_id",
        "product_name",
        "category",
        "unit_cost",
        "unit_price"
    ]
)

# ==========================================================
# INVENTORY TABLE
# ==========================================================

inventory_df = pd.DataFrame({
    "product_id": products_df["product_id"],
    "current_stock_level": np.random.randint(
        50, 5000, size=NUM_PRODUCTS
    ),
    "lead_time_days": np.random.randint(
        2, 31, size=NUM_PRODUCTS
    )
})

# ==========================================================
# DATE RANGE (2023-2025)
# ==========================================================

dates = pd.date_range(
    start="2023-01-01",
    end="2025-12-31",
    freq="D"
)

# ==========================================================
# OUT-OF-STOCK EVENTS
# Product unavailable for 7 days
# ==========================================================

out_of_stock_events = {}

affected_products = np.random.choice(
    products_df["product_id"],
    size=15,
    replace=False
)

for product_id in affected_products:
    start_day = np.random.choice(dates[:-7])

    blocked_dates = pd.date_range(
        start=start_day,
        periods=7,
        freq="D"
    )

    out_of_stock_events[product_id] = set(blocked_dates)

# ==========================================================
# SEASONAL TRANSACTION GENERATION
# ==========================================================

transactions = []
order_id = 1

for current_date in dates:

    month = current_date.month

    # Base demand
    daily_orders = np.random.poisson(45)

    # Holiday spike (+40%)
    if month in [11, 12]:
        daily_orders = int(daily_orders * 1.40)

    # Jan-Feb dip (-20%)
    elif month in [1, 2]:
        daily_orders = int(daily_orders * 0.80)

    for _ in range(daily_orders):

        product_id = np.random.choice(
            products_df["product_id"]
        )

        # Skip transactions if product is out-of-stock
        if (
            product_id in out_of_stock_events and
            current_date in out_of_stock_events[product_id]
        ):
            continue

        customer_id = np.random.randint(
            1,
            NUM_CUSTOMERS + 1
        )

        quantity = np.random.randint(1, 6)

        promotion = np.random.choice(
            [0, 1],
            p=[0.70, 0.30]
        )

        transactions.append([
            order_id,
            current_date.date(),
            customer_id,
            product_id,
            quantity,
            promotion
        ])

        order_id += 1

# ==========================================================
# ENSURE > 50K ROWS
# ==========================================================

sales_df = pd.DataFrame(
    transactions,
    columns=[
        "order_id",
        "date",
        "customer_id",
        "product_id",
        "quantity",
        "promotion_applied"
    ]
)

if len(sales_df) < MIN_TRANSACTIONS:
    raise ValueError(
        f"Generated only {len(sales_df)} rows."
    )

# ==========================================================
# BULK ORDER OUTLIERS
# Massive quantities
# ==========================================================

num_outliers = int(len(sales_df) * 0.003)

outlier_idx = np.random.choice(
    sales_df.index,
    size=num_outliers,
    replace=False
)

sales_df.loc[outlier_idx, "quantity"] = np.random.randint(
    100,
    1000,
    size=num_outliers
)

# ==========================================================
# MISSING VALUES (~2%)
# customer_id OR quantity
# ==========================================================

num_missing = int(len(sales_df) * 0.02)

missing_rows = np.random.choice(
    sales_df.index,
    size=num_missing,
    replace=False
)

half = len(missing_rows) // 2

sales_df.loc[
    missing_rows[:half],
    "customer_id"
] = np.nan

sales_df.loc[
    missing_rows[half:],
    "quantity"
] = np.nan

# ==========================================================
# SQLITE EXPORT
# ==========================================================

conn = sqlite3.connect(DB_NAME)

customers_df.to_sql(
    "customers",
    conn,
    if_exists="replace",
    index=False
)

products_df.to_sql(
    "products",
    conn,
    if_exists="replace",
    index=False
)

sales_df.to_sql(
    "sales_transactions",
    conn,
    if_exists="replace",
    index=False
)

inventory_df.to_sql(
    "inventory_status",
    conn,
    if_exists="replace",
    index=False
)

conn.commit()
conn.close()

print("=" * 60)
print("Database successfully created!")
print(f"File: {DB_NAME}")
print(f"Transactions: {len(sales_df):,}")
print(f"Customers: {len(customers_df):,}")
print(f"Products: {len(products_df):,}")
print("=" * 60)