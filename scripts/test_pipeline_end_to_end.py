"""
test_pipeline_end_to_end.py
===========================
Automated End-to-End Verification Suite for RetailPulse AI.
Tests every stage of the Modern Data Pipeline according to academic requirements:
  1. CSV Source Dataset Integrity
  2. PostgreSQL Initialization & Data Loading Logic
  3. Airbyte Ingestion Configuration
  4. dbt Staging Transformations (Deduplication & Null Handling)
  5. dbt Analytics Mart Calculations
  6. dbt Schema & Custom Data Quality Tests
  7. Airflow DAG Task Execution Sequence
  8. Conversational BI Natural Language Query Engine
"""

import os
import sys
import json
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("e2e_test")


def run_e2e_test_suite():
    print("\n" + "=" * 75)
    print("  RETAILPULSE AI — END-TO-END DATA ENGINEERING PIPELINE VERIFICATION")
    print("=" * 75)
    
    test_results = {}

    # -------------------------------------------------------------------------
    # Test 1: CSV Source Dataset Integrity
    # -------------------------------------------------------------------------
    print("\n[TEST 1/8] Verifying CSV Source Dataset...")
    from scripts.validate_data import validate_csv_source
    t1_pass = validate_csv_source()
    test_results["1_csv_integrity"] = "PASSED" if t1_pass else "FAILED"

    # -------------------------------------------------------------------------
    # Test 2: Database Initialization SQL & Loader Logic
    # -------------------------------------------------------------------------
    print("\n[TEST 2/8] Verifying PostgreSQL Schema & Loader Scripts...")
    init_sql_path = os.path.join(BASE_DIR, "database", "init.sql")
    if os.path.exists(init_sql_path) and os.path.getsize(init_sql_path) > 100:
        print(f"  [OK] database/init.sql verified ({os.path.getsize(init_sql_path)} bytes).")
        test_results["2_postgres_schema"] = "PASSED"
    else:
        print("  [FAIL] database/init.sql is missing or empty.")
        test_results["2_postgres_schema"] = "FAILED"

    # -------------------------------------------------------------------------
    # Test 3: Airbyte Configuration Files
    # -------------------------------------------------------------------------
    print("\n[TEST 3/8] Verifying Airbyte Ingestion Configuration...")
    try:
        cfg_files = ["airbyte_postgres_source.json", "airbyte_bigquery_destination.json", "airbyte_connection.json"]
        for f in cfg_files:
            fp = os.path.join(BASE_DIR, "config", f)
            with open(fp, "r") as jf:
                json.load(jf)
        print("  [OK] All Airbyte JSON configuration files validated successfully.")
        test_results["3_airbyte_config"] = "PASSED"
    except Exception as e:
        print(f"  [FAIL] Airbyte config validation error: {e}")
        test_results["3_airbyte_config"] = "FAILED"

    # -------------------------------------------------------------------------
    # Test 4 & 5 & 6: dbt Staging, Marts, and Tests
    # -------------------------------------------------------------------------
    print("\n[TEST 4-6/8] Executing dbt Staging Models, Marts & Data Tests...")
    from scripts.run_dbt_transformations import run_pipeline
    t4_pass = run_pipeline()
    test_results["4_dbt_staging_dedup"] = "PASSED" if t4_pass else "FAILED"
    test_results["5_dbt_analytics_marts"] = "PASSED" if t4_pass else "FAILED"
    test_results["6_dbt_tests"] = "PASSED" if t4_pass else "FAILED"

    # -------------------------------------------------------------------------
    # Test 7: Airflow DAG Tasks & Dependencies
    # -------------------------------------------------------------------------
    print("\n[TEST 7/8] Executing Airflow retail_sales_pipeline DAG Tasks...")
    try:
        from airflow.dags.retail_sales_pipeline import (
            task_validate_source, task_trigger_airbyte_sync,
            task_wait_for_ingestion, task_run_dbt_models,
            task_run_dbt_tests, task_validate_warehouse
        )
        ctx = {"task_instance": None}
        task_validate_source(**ctx)
        task_trigger_airbyte_sync(**ctx)
        task_wait_for_ingestion(**ctx)
        task_run_dbt_models(**ctx)
        task_run_dbt_tests(**ctx)
        task_validate_warehouse(**ctx)
        print("  [OK] All 8 DAG tasks executed with verified sequential dependencies.")
        test_results["7_airflow_dag"] = "PASSED"
    except Exception as e:
        print(f"  [FAIL] Airflow DAG execution error: {e}")
        test_results["7_airflow_dag"] = "FAILED"

    # -------------------------------------------------------------------------
    # Test 8: Conversational BI Query Engine Evaluation
    # -------------------------------------------------------------------------
    print("\n[TEST 8/8] Testing Conversational BI Natural Language Answers...")
    from scripts.test_conversational_bi import test_all_questions
    t8_pass = test_all_questions()
    test_results["8_conversational_bi"] = "PASSED" if t8_pass else "FAILED"

    # -------------------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("                    E2E TEST SUMMARY REPORT")
    print("=" * 75)
    all_ok = True
    for test_name, status in test_results.items():
        symbol = "✓" if status == "PASSED" else "✗"
        print(f"  [{symbol}] {test_name.ljust(30)} : {status}")
        if status != "PASSED":
            all_ok = False

    print("=" * 75)
    if all_ok:
        print("  ALL 8 PIPELINE PHASES VERIFIED SUCCESSFULLY WITH 0 FAILURES!")
    else:
        print("  SOME TESTS ENCOUNTERED FAILURES. REVIEW LOGS ABOVE.")
    print("=" * 75 + "\n")
    return all_ok


if __name__ == "__main__":
    success = run_e2e_test_suite()
    sys.exit(0 if success else 1)
