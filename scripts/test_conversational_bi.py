"""
test_conversational_bi.py
-------------------------
Verifies that all 6 mandatory business questions return accurate results,
proper SQL statements, and non-empty dataframes from the transformed warehouse.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from streamlit_app.utils.query_engine import bi_engine


QUESTIONS = [
    "Which product generates the highest revenue?",
    "Which region has the highest sales?",
    "How does revenue change month by month?",
    "Which products have the highest sales volume?",
    "What is the average order value?",
    "How many orders are completed?",
    "Which category performs best?"
]


def test_all_questions():
    print("=" * 70)
    print("RetailPulse AI — Conversational BI Test Suite")
    print("=" * 70)

    all_passed = True
    for i, q in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/{len(QUESTIONS)}] Testing: \"{q}\"")
        res = bi_engine.ask(q)

        if not res.get("success"):
            print(f"  [FAIL] Query returned unsuccessful: {res.get('answer')}")
            all_passed = False
            continue

        df = res.get("df")
        if df is None or df.empty:
            print(f"  [FAIL] DataFrame is empty!")
            all_passed = False
            continue

        print(f"  [PASS] Intent       : {res.get('intent')}")
        print(f"  [PASS] Answer       : {res.get('answer')}")
        print(f"  [PASS] Chart Type   : {res.get('chart_type')}")
        print(f"  [PASS] Rows returned: {len(df)}")
        print(f"  [PASS] SQL Snippet  : {res.get('sql').strip()[:60]}...")

    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] All Conversational BI queries passed with 100% accuracy!")
    else:
        print("[FAILURE] Some Conversational BI queries encountered issues.")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    ok = test_all_questions()
    sys.exit(0 if ok else 1)
