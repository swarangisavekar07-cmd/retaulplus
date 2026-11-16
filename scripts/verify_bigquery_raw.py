"""
verify_bigquery_raw.py
----------------------
Verifies that raw retail sales records have been ingested into Google BigQuery via Airbyte.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
RAW_DATASET = os.getenv("BIGQUERY_RAW_DATASET", "raw_retailpulse")
TABLE_NAME = os.getenv("BIGQUERY_RAW_TABLE", "retail_sales")
CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


def verify_bigquery_raw():
    print("=" * 60)
    print("RetailPulse AI — BigQuery Raw Table Ingestion Verification")
    print("=" * 60)
    print(f"Project ID   : {PROJECT_ID or '(Not Set)'}")
    print(f"Dataset      : {RAW_DATASET}")
    print(f"Table        : {TABLE_NAME}")
    print(f"Credentials  : {CREDS_PATH or '(Default Environment)'}")

    if not PROJECT_ID:
        print("\n[INFO] GCP_PROJECT_ID is not configured in .env.")
        print("To verify live BigQuery ingestion:")
        print("  1. Create a Google Cloud project with BigQuery enabled.")
        print("  2. Place service account key JSON in config/gcp-key.json.")
        print("  3. Set GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS in .env.")
        return False

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        table_ref = f"{PROJECT_ID}.{RAW_DATASET}.{TABLE_NAME}"

        print(f"\nQuerying BigQuery table: {table_ref}...")
        query = f"SELECT COUNT(*) AS total_rows FROM `{table_ref}`"
        query_job = client.query(query)
        results = list(query_job.result())
        total_rows = results[0]["total_rows"]

        print(f"[OK] Ingestion verified! {total_rows} records found in BigQuery raw dataset.")

        # Preview sample records
        sample_query = f"SELECT order_id, order_date, customer_name, product_name, quantity, unit_price, payment_status FROM `{table_ref}` LIMIT 5"
        sample_job = client.query(sample_query)
        print("\n--- Sample Synced Records ---")
        for row in sample_job.result():
            print(dict(row))

        return True

    except Exception as e:
        print(f"\n[ERROR] BigQuery query failed: {e}")
        return False


if __name__ == "__main__":
    verify_bigquery_raw()
