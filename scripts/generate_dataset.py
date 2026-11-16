"""
generate_dataset.py
-------------------
Generates a realistic synthetic retail sales dataset for RetailPulse AI.
Dataset contains ~850 records across 12 months with realistic distributions,
intentional duplicate rows, and controlled missing values to test dbt data quality rules.

Schema:
- order_id: Unique order identifier (e.g., ORD-2024-001)
- order_date: Date of order (YYYY-MM-DD)
- customer_id: Customer identifier (e.g., CUST-1042)
- customer_name: Full name of customer
- product_id: Product identifier (e.g., PROD-101)
- product_name: Descriptive product name
- category: Product category (Electronics, Office Supplies, Home & Living, Fitness & Health)
- region: Geographic region (North, South, East, West, Central)
- quantity: Units purchased (integer >= 1)
- unit_price: Price per unit (decimal > 0.0)
- payment_status: Completed, Pending, Cancelled, Refunded
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set fixed seed for reproducibility across pipeline runs
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

PRODUCTS = [
    # (product_id, product_name, category, typical_price)
    ("PROD-101", "Ultra Wireless Noise-Cancelling Headphones", "Electronics", 149.99),
    ("PROD-102", "Smart Fitness Tracker Band V4", "Fitness & Health", 79.50),
    ("PROD-103", "Ergonomic Mesh Office Chair", "Office Supplies", 229.00),
    ("PROD-104", "Mechanical Gaming Keyboard RGB", "Electronics", 119.99),
    ("PROD-105", "4K Ultra HD 27-inch IPS Monitor", "Electronics", 349.50),
    ("PROD-106", "Organic Arabica Whole Bean Coffee 1kg", "Home & Living", 24.99),
    ("PROD-107", "Stainless Steel Insulated Water Bottle 1L", "Home & Living", 29.95),
    ("PROD-108", "Compact HEPA Air Purifier", "Home & Living", 129.00),
    ("PROD-109", "USB-C Multiport Docking Station 100W", "Electronics", 69.99),
    ("PROD-110", "Adjustable Height Laptop Stand", "Office Supplies", 45.00),
    ("PROD-111", "Yoga Mat Non-Slip Eco Rubber", "Fitness & Health", 39.99),
    ("PROD-112", "Smart Home LED Ambient Light Bar", "Electronics", 54.95),
    ("PROD-113", "Executive Leather Notebook & Pen Set", "Office Supplies", 32.50),
    ("PROD-114", "Deep Tissue Percussion Muscle Massage Gun", "Fitness & Health", 99.00),
    ("PROD-115", "Cast Iron Dutch Oven 5.5 Quart", "Home & Living", 89.95),
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Arjun", "Priya", "Carlos", "Elena", "Wei", "Aisha", "Kenji", "Fatima"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Patel",
    "Sharma", "Tanaka", "Chen", "Kim", "Nakamura", "Al-Mansoor", "Kowalski"
]

REGIONS = ["North", "South", "East", "West", "Central"]
REGION_WEIGHTS = [0.28, 0.22, 0.24, 0.18, 0.08]

PAYMENT_STATUSES = ["Completed", "Pending", "Cancelled", "Refunded"]
STATUS_WEIGHTS = [0.85, 0.07, 0.05, 0.03]  # ~85% completed orders

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days


def generate_customers(num_customers=220):
    customers = []
    for i in range(1, num_customers + 1):
        cid = f"CUST-{1000 + i}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customers.append((cid, name))
    return customers


def generate_retail_sales(target_records=800):
    customers = generate_customers(220)
    records = []

    for i in range(1, target_records + 1):
        order_id = f"ORD-2024-{1000 + i}"
        
        # Realistic seasonal sales curve (higher around Q4 holidays)
        day_offset = random.randint(0, DATE_RANGE_DAYS)
        # boost November/December likelihood
        if random.random() < 0.25:
            day_offset = random.randint(DATE_RANGE_DAYS - 60, DATE_RANGE_DAYS)
        order_date = (START_DATE + timedelta(days=day_offset)).strftime("%Y-%m-%d")

        cust_id, cust_name = random.choice(customers)
        prod_id, prod_name, category, base_price = random.choice(PRODUCTS)
        
        # Slight unit price variation (promotional discounts / bulk pricing)
        price_multiplier = random.choice([0.90, 0.95, 1.0, 1.0, 1.0, 1.05])
        unit_price = round(base_price * price_multiplier, 2)
        
        # Quantity distribution: mostly 1-3, occasionally up to 8
        quantity = random.choices([1, 2, 3, 4, 5, 8], weights=[0.55, 0.25, 0.10, 0.05, 0.03, 0.02])[0]
        
        region = random.choices(REGIONS, weights=REGION_WEIGHTS)[0]
        payment_status = random.choices(PAYMENT_STATUSES, weights=STATUS_WEIGHTS)[0]

        records.append({
            "order_id": order_id,
            "order_date": order_date,
            "customer_id": cust_id,
            "customer_name": cust_name,
            "product_id": prod_id,
            "product_name": prod_name,
            "category": category,
            "region": region,
            "quantity": quantity,
            "unit_price": unit_price,
            "payment_status": payment_status
        })

    df = pd.DataFrame(records)

    # 1. Inject deliberate duplicate cases for dbt deduplication testing (approx 10 rows)
    duplicates = df.sample(n=10, random_state=RANDOM_SEED).copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    # 2. Inject deliberate missing values in non-primary key columns for dbt cleaning tests
    # 5 rows with missing customer_name
    null_cust_indices = df.sample(n=5, random_state=RANDOM_SEED + 1).index
    df.loc[null_cust_indices, "customer_name"] = np.nan

    # 4 rows with missing payment_status (to test dbt fallback to 'Pending' or 'Unknown')
    null_status_indices = df.sample(n=4, random_state=RANDOM_SEED + 2).index
    df.loc[null_status_indices, "payment_status"] = np.nan

    # Sort deterministically by order_date and order_id
    df = df.sort_values(by=["order_date", "order_id"]).reset_index(drop=True)

    return df


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "retail_sales.csv")

    print(f"Generating synthetic retail sales dataset...")
    df = generate_retail_sales(target_records=800)
    df.to_csv(output_path, index=False)
    
    print(f"[OK] Generated {len(df)} total records (including intentional duplicates and nulls).")
    print(f"Saved dataset to: {os.path.abspath(output_path)}")
    print(f"Dataset columns: {list(df.columns)}")
    print(f"Null customer_name count: {df['customer_name'].isna().sum()}")
    print(f"Null payment_status count: {df['payment_status'].isna().sum()}")
    print(f"Duplicate order_id count: {df['order_id'].duplicated().sum()}")
