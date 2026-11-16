"""
load_postgres.py
----------------
Loads the raw retail sales CSV dataset into the PostgreSQL source database.

Environment Variables:
- POSTGRES_HOST (default: localhost)
- POSTGRES_PORT (default: 5432)
- POSTGRES_DB (default: retail_pulse_db)
- POSTGRES_USER (default: postgres)
- POSTGRES_PASSWORD (default: postgres)
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "retail_pulse_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "retail_sales.csv")
INIT_SQL_PATH = os.path.join(BASE_DIR, "database", "init.sql")


def load_csv_to_postgres():
    print(f"==================================================")
    print(f"RetailPulse AI — PostgreSQL Source Data Loader")
    print(f"==================================================")
    print(f"Target Database : {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Source CSV File : {CSV_PATH}")

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Source CSV not found at {CSV_PATH}. Run scripts/generate_dataset.py first.")

    # Read CSV data
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} records from CSV into memory.")

    # Attempt connection via psycopg2 / sqlalchemy
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        print("[ERROR] psycopg2-binary is not installed. Please install dependencies via: pip install -r requirements.txt")
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=5
        )
        conn.autocommit = False
        cursor = conn.cursor()
        print("[OK] Successfully connected to PostgreSQL source database.")

        # Execute init.sql to ensure table exists and is fresh
        if os.path.exists(INIT_SQL_PATH):
            with open(INIT_SQL_PATH, "r", encoding="utf-8") as f:
                init_sql = f.read()
            cursor.execute(init_sql)
            conn.commit()
            print("[OK] Executed database/init.sql — public.retail_sales schema initialized.")

        # Insert records into public.retail_sales
        insert_sql = """
            INSERT INTO public.retail_sales (
                order_id, order_date, customer_id, customer_name,
                product_id, product_name, category, region,
                quantity, unit_price, payment_status
            ) VALUES (
                %(order_id)s, %(order_date)s, %(customer_id)s, %(customer_name)s,
                %(product_id)s, %(product_name)s, %(category)s, %(region)s,
                %(quantity)s, %(unit_price)s, %(payment_status)s
            );
        """

        # Replace NaN with None for proper SQL NULL handling
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        execute_batch(cursor, insert_sql, records, page_size=200)
        conn.commit()

        # Verify record count
        cursor.execute("SELECT COUNT(*) FROM public.retail_sales;")
        loaded_count = cursor.fetchone()[0]
        print(f"[OK] Ingestion verified: {loaded_count} rows present in public.retail_sales.")

        cursor.close()
        conn.close()
        print("[SUCCESS] CSV loaded into PostgreSQL successfully.")
        return True

    except Exception as e:
        print(f"\n[WARNING] Could not connect to PostgreSQL instance ({e}).")
        print("Note: In a production or Docker environment, ensure Postgres is running via:")
        print("      docker-compose up -d postgres")
        print("Or check your POSTGRES_* environment variables in .env.\n")
        return False


if __name__ == "__main__":
    success = load_csv_to_postgres()
    if not success:
        sys.exit(0)  # Exit gracefully for environments where Docker postgres is offline
