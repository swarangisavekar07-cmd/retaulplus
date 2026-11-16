"""
airbyte_client.py
-----------------
Enterprise REST API client for Apache Airflow & automation scripts to interact
with an Airbyte server instance (API v1).

Supports:
- Workspace discovery
- Source & Destination registration (PostgreSQL -> BigQuery)
- Connection creation & sync catalog configuration
- Job synchronization triggering and status polling
"""

import os
import time
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AirbyteClient")


class AirbyteClient:
    def __init__(self, host=None, port=None, username=None, password=None):
        self.host = host or os.getenv("AIRBYTE_HOST", "localhost")
        self.port = port or os.getenv("AIRBYTE_PORT", "8000")
        self.base_url = f"http://{self.host}:{self.port}/api/v1"
        self.auth = (
            username or os.getenv("AIRBYTE_USERNAME", "airbyte"),
            password or os.getenv("AIRBYTE_PASSWORD", "password")
        )
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> bool:
        """Check if Airbyte service is reachable and healthy."""
        try:
            url = f"{self.base_url}/health"
            res = self.session.get(url, timeout=5)
            if res.status_code == 200:
                logger.info(f"Airbyte health check passed: {res.json()}")
                return True
            logger.warning(f"Airbyte responded with status {res.status_code}: {res.text}")
            return False
        except Exception as e:
            logger.warning(f"Could not reach Airbyte at {self.base_url}: {e}")
            return False

    def get_workspace_id(self) -> str:
        """Fetch the first active workspace ID."""
        url = f"{self.base_url}/workspaces/list"
        res = self.session.post(url, json={})
        res.raise_for_status()
        data = res.json()
        workspaces = data.get("workspaces", [])
        if not workspaces:
            raise RuntimeError("No Airbyte workspaces found.")
        workspace_id = workspaces[0]["workspaceId"]
        logger.info(f"Discovered Airbyte workspace ID: {workspace_id}")
        return workspace_id

    def create_or_get_postgres_source(self, workspace_id: str, config: dict) -> str:
        """Create PostgreSQL source or find existing by name."""
        # Check existing sources
        list_url = f"{self.base_url}/sources/list"
        res = self.session.post(list_url, json={"workspaceId": workspace_id})
        res.raise_for_status()
        sources = res.json().get("sources", [])
        for s in sources:
            if s.get("name") == config.get("name"):
                logger.info(f"Found existing Airbyte source '{s.get('name')}' with ID: {s['sourceId']}")
                return s["sourceId"]

        # Create new source
        create_url = f"{self.base_url}/sources/create"
        payload = {
            "workspaceId": workspace_id,
            "name": config.get("name", "RetailPulse PostgreSQL Source"),
            "sourceDefinitionId": config.get("sourceDefinitionId", "decd338e-5647-4c0b-adf4-da0e75f5a750"),
            "connectionConfiguration": config.get("connectionConfiguration")
        }
        create_res = self.session.post(create_url, json=payload)
        create_res.raise_for_status()
        source_id = create_res.json()["sourceId"]
        logger.info(f"Created new Airbyte source: {source_id}")
        return source_id

    def create_or_get_bigquery_destination(self, workspace_id: str, config: dict) -> str:
        """Create BigQuery destination or find existing by name."""
        list_url = f"{self.base_url}/destinations/list"
        res = self.session.post(list_url, json={"workspaceId": workspace_id})
        res.raise_for_status()
        destinations = res.json().get("destinations", [])
        for d in destinations:
            if d.get("name") == config.get("name"):
                logger.info(f"Found existing Airbyte destination '{d.get('name')}' with ID: {d['destinationId']}")
                return d["destinationId"]

        create_url = f"{self.base_url}/destinations/create"
        payload = {
            "workspaceId": workspace_id,
            "name": config.get("name", "RetailPulse BigQuery Destination"),
            "destinationDefinitionId": config.get("destinationDefinitionId", "ef301139-22a6-44c2-9e2b-78893d142d79"),
            "connectionConfiguration": config.get("connectionConfiguration")
        }
        create_res = self.session.post(create_url, json=payload)
        create_res.raise_for_status()
        dest_id = create_res.json()["destinationId"]
        logger.info(f"Created new Airbyte destination: {dest_id}")
        return dest_id

    def create_or_get_connection(self, source_id: str, dest_id: str, conn_config: dict) -> str:
        """Create connection between PostgreSQL source and BigQuery destination."""
        list_url = f"{self.base_url}/connections/list"
        res = self.session.post(list_url, json={"workspaceId": conn_config.get("workspaceId")})
        if res.status_code == 200:
            for c in res.json().get("connections", []):
                if c.get("sourceId") == source_id and c.get("destinationId") == dest_id:
                    logger.info(f"Found existing Airbyte connection ID: {c['connectionId']}")
                    return c["connectionId"]

        create_url = f"{self.base_url}/connections/create"
        payload = {
            "name": conn_config.get("name", "RetailPulse_Postgres_to_BigQuery_Sync"),
            "sourceId": source_id,
            "destinationId": dest_id,
            "syncCatalog": conn_config.get("syncCatalog"),
            "namespaceDefinition": conn_config.get("namespaceDefinition", "destination"),
            "namespaceFormat": conn_config.get("namespaceFormat", "${BIGQUERY_RAW_DATASET}"),
            "status": "active"
        }
        create_res = self.session.post(create_url, json=payload)
        create_res.raise_for_status()
        conn_id = create_res.json()["connectionId"]
        logger.info(f"Created new Airbyte connection: {conn_id}")
        return conn_id

    def trigger_sync(self, connection_id: str) -> int:
        """Trigger a manual synchronization job for the specified connection."""
        url = f"{self.base_url}/connections/sync"
        payload = {"connectionId": connection_id}
        logger.info(f"Triggering Airbyte sync for connection: {connection_id}...")
        res = self.session.post(url, json=payload)
        res.raise_for_status()
        job_data = res.json().get("job", {})
        job_id = job_data.get("id")
        logger.info(f"Airbyte sync initiated successfully. Job ID: {job_id}")
        return job_id

    def get_job_status(self, job_id: int) -> dict:
        """Retrieve details and status for a sync job."""
        url = f"{self.base_url}/jobs/get"
        payload = {"id": job_id}
        res = self.session.post(url, json=payload)
        res.raise_for_status()
        job_info = res.json().get("job", {})
        status = job_info.get("status")
        return {"id": job_id, "status": status, "raw": job_info}

    def wait_for_job(self, job_id: int, timeout_sec: int = 600, poll_interval: int = 5) -> bool:
        """Poll job status until terminal state (succeeded, failed, cancelled)."""
        logger.info(f"Waiting for Airbyte job {job_id} to finish (timeout: {timeout_sec}s)...")
        elapsed = 0
        while elapsed < timeout_sec:
            info = self.get_job_status(job_id)
            status = info.get("status")
            logger.info(f"Job {job_id} status: {status} (elapsed: {elapsed}s)")

            if status == "succeeded":
                logger.info(f"[SUCCESS] Airbyte Job {job_id} succeeded.")
                return True
            elif status in ("failed", "cancelled"):
                logger.error(f"[FAILURE] Airbyte Job {job_id} ended with status: {status}")
                return False

            time.sleep(poll_interval)
            elapsed += poll_interval

        logger.error(f"[TIMEOUT] Job {job_id} exceeded maximum wait time of {timeout_sec}s")
        return False


if __name__ == "__main__":
    client = AirbyteClient()
    healthy = client.health_check()
    if healthy:
        try:
            ws_id = client.get_workspace_id()
            print(f"Airbyte Client connected! Active workspace: {ws_id}")
        except Exception as err:
            print(f"Airbyte API query failed: {err}")
    else:
        print("Airbyte is not running locally. Start it via docker-compose up -d airbyte")
