"""
db_connector.py
---------------
Secure warehouse connector providing dual-mode access:
  1. Google BigQuery (Cloud Data Warehouse) when GCP credentials are provided.
  2. Local Analytical Marts (DuckDB Warehouse Replica) for offline academic demonstrations.

Enforces strict read-only execution guardrails and query sanitation.
"""

import os
import re
import logging
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("db_connector")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL_DB_PATH = os.path.join(BASE_DIR, "data", "retailpulse_warehouse.duckdb")

GCP_PROJECT = os.getenv("GCP_PROJECT_ID")
GCP_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BQ_DATASET = os.getenv("BIGQUERY_ANALYTICS_DATASET", "analytics_retailpulse")

# Prohibited destructive SQL keywords
FORBIDDEN_KEYWORDS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b",
    r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bGRANT\b",
    r"\bREVOKE\b", r"\bEXEC\b", r"\bMERGE\b"
]


class WarehouseConnector:
    def __init__(self):
        self.backend = "DuckDB"
        self.is_cloud = False
        self._init_connection()

    def _init_connection(self):
        """Determine whether to use BigQuery or Local DuckDB."""
        if GCP_PROJECT and GCP_CREDS and os.path.exists(GCP_CREDS):
            try:
                from google.cloud import bigquery
                self.bq_client = bigquery.Client(project=GCP_PROJECT)
                self.backend = "BigQuery"
                self.is_cloud = True
                logger.info("Connected to Cloud Warehouse: Google BigQuery.")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize BigQuery client ({e}). Falling back to local warehouse.")

        self.backend = "DuckDB"
        self.is_cloud = False
        logger.info(f"Connected to Local Warehouse Replica at {LOCAL_DB_PATH}.")

    def validate_query_safety(self, sql: str) -> bool:
        """Enforces that incoming queries are strictly read-only."""
        cleaned_sql = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.MULTILINE).strip().upper()
        
        # Query must begin with SELECT or WITH
        if not (cleaned_sql.startswith("SELECT") or cleaned_sql.startswith("WITH")):
            raise PermissionError("Security Policy Violation: Only SELECT and WITH analytical queries are permitted.")

        for kw_pattern in FORBIDDEN_KEYWORDS:
            if re.search(kw_pattern, cleaned_sql):
                raise PermissionError(f"Security Policy Violation: Query contains prohibited keyword ({kw_pattern}).")

        return True

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Executes a validated read-only SQL query against the active warehouse backend.
        """
        self.validate_query_safety(sql)

        if self.is_cloud:
            # Adapt schema references for BigQuery if necessary
            # e.g., analytics.mart_sales_summary -> `GCP_PROJECT.analytics_retailpulse.mart_sales_summary`
            bq_sql = sql
            bq_sql = re.sub(
                r"\banalytics\.(\w+)",
                f"`{GCP_PROJECT}.{BQ_DATASET}.\\1`",
                bq_sql,
                flags=re.IGNORECASE
            )
            bq_sql = re.sub(
                r"\bstaging\.(\w+)",
                f"`{GCP_PROJECT}.staging.\\1`",
                bq_sql,
                flags=re.IGNORECASE
            )
            query_job = self.bq_client.query(bq_sql)
            return query_job.to_dataframe()

        else:
            # Query local DuckDB warehouse
            import duckdb
            if not os.path.exists(LOCAL_DB_PATH):
                raise FileNotFoundError(
                    f"Local warehouse mart database not found at {LOCAL_DB_PATH}. "
                    "Run 'python scripts/run_dbt_transformations.py' to generate warehouse tables."
                )
            
            con = duckdb.connect(LOCAL_DB_PATH, read_only=True)
            try:
                df = con.execute(sql).df()
            finally:
                con.close()
            return df

    def get_status(self) -> dict:
        """Returns connection diagnostic status for UI display."""
        return {
            "backend": self.backend,
            "is_cloud": self.is_cloud,
            "project_id": GCP_PROJECT if self.is_cloud else "local_instance",
            "dataset": BQ_DATASET if self.is_cloud else "analytics",
            "database_path": LOCAL_DB_PATH if not self.is_cloud else None
        }


# Singleton instance
warehouse_connector = WarehouseConnector()
