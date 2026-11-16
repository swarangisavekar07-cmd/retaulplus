"""
setup_airbyte.py
----------------
Automates configuration of Airbyte PostgreSQL source, BigQuery destination,
and connection sync for RetailPulse AI.
"""

import os
import sys
import json
from dotenv import load_dotenv
from airbyte_client import AirbyteClient

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")


def substitute_env(obj):
    """Recursively replace ${VAR_NAME} placeholders with environment variables."""
    if isinstance(obj, dict):
        return {k: substitute_env(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env(elem) for elem in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        val = os.getenv(var_name, "")
        if not val:
            print(f"[WARN] Environment variable '{var_name}' is unset or empty.")
        return val
    return obj


def setup_airbyte_pipeline():
    print("=" * 60)
    print("RetailPulse AI — Airbyte Ingestion Setup")
    print("=" * 60)

    client = AirbyteClient()
    if not client.health_check():
        print("[ERROR] Airbyte server is unreachable at http://localhost:8000.")
        print("Please start Airbyte via: docker-compose up -d airbyte")
        return False

    workspace_id = client.get_workspace_id()

    # 1. Configure PostgreSQL Source
    pg_config_file = os.path.join(CONFIG_DIR, "airbyte_postgres_source.json")
    with open(pg_config_file, "r") as f:
        pg_config = substitute_env(json.load(f))
    source_id = client.create_or_get_postgres_source(workspace_id, pg_config)

    # 2. Configure BigQuery Destination
    bq_config_file = os.path.join(CONFIG_DIR, "airbyte_bigquery_destination.json")
    with open(bq_config_file, "r") as f:
        bq_config = substitute_env(json.load(f))
    dest_id = client.create_or_get_bigquery_destination(workspace_id, bq_config)

    # 3. Configure Connection
    conn_config_file = os.path.join(CONFIG_DIR, "airbyte_connection.json")
    with open(conn_config_file, "r") as f:
        conn_config = substitute_env(json.load(f))
    conn_config["workspaceId"] = workspace_id
    connection_id = client.create_or_get_connection(source_id, dest_id, conn_config)

    print("\n[SUCCESS] Airbyte setup completed successfully!")
    print(f"PostgreSQL Source ID     : {source_id}")
    print(f"BigQuery Destination ID  : {dest_id}")
    print(f"Sync Connection ID       : {connection_id}")
    print(f"\nSave this Connection ID to .env as AIRBYTE_CONNECTION_ID={connection_id}")
    return True


if __name__ == "__main__":
    setup_airbyte_pipeline()
