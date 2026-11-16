"""
query_engine.py
---------------
Conversational Business Intelligence Engine for RetailPulse AI.
Translates user natural language questions into safe analytical SQL queries,
executes them against the warehouse, and formats answers with dynamic visualizations.
"""

import re
import os
import logging
import pandas as pd
from dotenv import load_dotenv

from .db_connector import warehouse_connector
from ..queries.predefined_queries import BUSINESS_QUERIES

load_dotenv()
logger = logging.getLogger("query_engine")


class ConversationalBIEngine:
    def __init__(self):
        self.queries = BUSINESS_QUERIES

    def match_intent(self, question: str) -> str:
        """
        Matches a natural language question to a canonical business query.
        """
        q = question.lower().strip()

        # 1. Product sales volume (check volume/units before generic product checks)
        if any(term in q for term in ["volume", "quantity", "units", "units sold", "most popular", "highest volume", "highest sales volume"]):
            return "top_volume_products"

        # 2. Product revenue
        if any(term in q for term in ["product", "item"]) and any(term in q for term in ["highest revenue", "top revenue", "most revenue", "best selling product", "highest sales", "generates the highest revenue", "generated the highest revenue"]):
            return "top_revenue_product"

        # 3. Region revenue
        if any(term in q for term in ["region", "territory", "area", "zone"]) and any(term in q for term in ["highest", "best", "top", "most", "sales", "revenue"]):
            return "top_sales_region"

        # 4. Monthly revenue
        if any(term in q for term in ["month", "monthly", "month by month", "timeline", "trend", "trends", "over time"]):
            return "monthly_revenue_trend"

        # 5. Average order value
        if any(term in q for term in ["average order value", "aov", "average order", "avg order", "average spend"]):
            return "average_order_value"

        # 6. Completed orders
        if any(term in q for term in ["completed", "complete", "completion", "how many orders", "order status", "fulfilled"]):
            return "completed_orders_count"

        # 7. Category performance
        if any(term in q for term in ["category", "categories", "merchandise", "department", "category performs best"]):
            return "category_performance"

        # Keyword fallbacks
        if "volume" in q or "unit" in q:
            return "top_volume_products"
        if "product" in q or "highest revenue" in q:
            return "top_revenue_product"
        if "region" in q:
            return "top_sales_region"
        if "month" in q:
            return "monthly_revenue_trend"
        if "order" in q and "value" in q:
            return "average_order_value"
        if "order" in q and ("count" in q or "how many" in q):
            return "completed_orders_count"

        return None

    def ask(self, question: str) -> dict:
        """
        Processes a user question, executes the corresponding SQL query,
        and returns structured result with answer text and chart configuration.
        """
        intent = self.match_intent(question)

        if not intent or intent not in self.queries:
            # Handle unsupported question gracefully
            return {
                "success": False,
                "question": question,
                "answer": (
                    "I couldn't map that specific question to our analytical models. "
                    "Try asking one of the core retail performance questions:\n"
                    "- *'Which product generates the highest revenue?'*\n"
                    "- *'Which region has the highest sales?'*\n"
                    "- *'How does revenue change month by month?'*\n"
                    "- *'Which products have the highest sales volume?'*\n"
                    "- *'What is the average order value?'*\n"
                    "- *'How many orders are completed?'*\n"
                    "- *'Which category performs best?'*"
                ),
                "sql": None,
                "df": None,
                "chart_type": None
            }

        q_config = self.queries[intent]
        sql = q_config["sql"].strip()

        try:
            df = warehouse_connector.execute_query(sql)
            if df.empty:
                return {
                    "success": True,
                    "question": question,
                    "answer": "The query executed successfully, but no matching records were found in the warehouse.",
                    "sql": sql,
                    "df": df,
                    "chart_type": "table"
                }

            # Generate natural language answer
            top_row = df.iloc[0]
            answer_text = ""

            if intent == "top_revenue_product":
                answer_text = q_config["answer_template"].format(
                    top_item=top_row["product_name"],
                    top_val=float(top_row["total_revenue"]),
                    cat=top_row.get("category", "its category")
                )
            elif intent == "top_sales_region":
                answer_text = q_config["answer_template"].format(
                    top_item=top_row["region"],
                    top_val=float(top_row["total_revenue"]),
                    top_pct=top_row.get("pct_of_total_revenue", 0.0)
                )
            elif intent == "monthly_revenue_trend":
                max_rev = df["total_revenue"].max()
                answer_text = q_config["answer_template"].format(top_val=float(max_rev))
            elif intent == "top_volume_products":
                answer_text = q_config["answer_template"].format(
                    top_item=top_row["product_name"],
                    top_val=int(top_row["total_units_sold"])
                )
            elif intent == "average_order_value":
                answer_text = q_config["answer_template"].format(
                    top_val=float(top_row["avg_order_value"]),
                    orders=int(top_row["total_orders"])
                )
            elif intent == "completed_orders_count":
                answer_text = q_config["answer_template"].format(
                    top_val=int(top_row["completed_orders"]),
                    total=int(top_row["total_orders"]),
                    pct=float(top_row["completion_rate_pct"])
                )
            elif intent == "category_performance":
                answer_text = q_config["answer_template"].format(
                    top_item=top_row["category"],
                    top_val=float(top_row["total_revenue"])
                )
            else:
                answer_text = f"Query returned {len(df)} records."

            return {
                "success": True,
                "question": question,
                "intent": intent,
                "title": q_config["title"],
                "answer": answer_text,
                "sql": sql,
                "df": df,
                "chart_type": q_config.get("chart_type", "table"),
                "chart_config": q_config
            }

        except Exception as e:
            logger.error(f"Error executing conversational query for intent '{intent}': {e}")
            return {
                "success": False,
                "question": question,
                "answer": f"Error executing query against warehouse: {str(e)}",
                "sql": sql,
                "df": None,
                "chart_type": None
            }


bi_engine = ConversationalBIEngine()
