"""
validate_data.py
----------------
Validates data quality, schema integrity, and distribution metrics for RetailPulse AI.
Can validate raw CSV, PostgreSQL source table, or BigQuery/local warehouse tables.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "retail_sales.csv")

REQUIRED_COLUMNS = [
    "order_id", "order_date", "customer_id", "customer_name",
    "product_id", "product_name", "category", "region",
    "quantity", "unit_price", "payment_status"
]


def validate_csv_source():
    print("=" * 60)
    print("RetailPulse AI — Source Dataset Validation Suite")
    print("=" * 60)

    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Source file not found: {CSV_PATH}")
        return False

    df = pd.read_csv(CSV_PATH)
    print(f"File Path        : {os.path.relpath(CSV_PATH, BASE_DIR)}")
    print(f"Total Rows       : {len(df)}")
    print(f"Total Columns    : {len(df.columns)}")

    # 1. Column Presence Check
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        print(f"[FAIL] Missing required columns: {missing_cols}")
        return False
    print("[PASS] All 11 mandatory schema columns are present.")

    # 2. Data Type & Business Logic Checks
    errors = []

    # Quantity check
    if not pd.api.types.is_numeric_dtype(df["quantity"]):
        errors.append("Column 'quantity' is not numeric")
    elif (df["quantity"] < 0).any():
        errors.append("Negative values found in 'quantity'")

    # Unit price check
    if not pd.api.types.is_numeric_dtype(df["unit_price"]):
        errors.append("Column 'unit_price' is not numeric")
    elif (df["unit_price"] < 0).any():
        errors.append("Negative values found in 'unit_price'")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return False
    print("[PASS] Data integrity assertions passed (quantity >= 0, unit_price >= 0).")

    # 3. Data Quality Edge Cases Audit (Deliberate nulls and duplicates)
    dup_orders = df["order_id"].duplicated().sum()
    null_cust = df["customer_name"].isna().sum()
    null_status = df["payment_status"].isna().sum()

    print("\n--- Data Quality Edge Cases (for dbt testing & deduplication) ---")
    print(f"Duplicate order_ids injected : {dup_orders} (will be deduplicated in dbt staging)")
    print(f"Null customer_name count     : {null_cust} (will be handled as 'Guest Customer' in dbt)")
    print(f"Null payment_status count    : {null_status} (will be defaulted to 'Pending' in dbt)")

    # 4. Metric summary
    total_revenue = (df["quantity"] * df["unit_price"]).sum()
    print(f"\n--- Raw Business Metrics ---")
    print(f"Raw Gross Revenue: ${total_revenue:,.2f}")
    print(f"Date Range       : {df['order_date'].min()} to {df['order_date'].max()}")
    print(f"Unique Customers : {df['customer_id'].nunique()}")
    print(f"Unique Products  : {df['product_id'].nunique()}")
    print(f"Regions Covered  : {', '.join(sorted(df['region'].unique()))}")
    print(f"Categories       : {', '.join(sorted(df['category'].unique()))}")
    print("=" * 60)
    print("[SUCCESS] Dataset validation completed successfully.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = validate_csv_source()
    sys.exit(0 if success else 1)
