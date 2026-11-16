"""
predefined_queries.py
---------------------
Predefined SQL queries mapping natural language business questions
to read-only SQL queries against RetailPulse AI analytical warehouse marts.
"""

# Dictionary of canonical business questions and their SQL queries
BUSINESS_QUERIES = {
    "top_revenue_product": {
        "title": "Top Product by Revenue",
        "description": "Identifies the highest revenue-generating product across all sales.",
        "sql": """
            SELECT
                product_name,
                category,
                total_revenue,
                total_units_sold,
                rank_by_revenue
            FROM analytics.mart_product_performance
            ORDER BY total_revenue DESC
            LIMIT 5;
        """,
        "chart_type": "bar",
        "x": "product_name",
        "y": "total_revenue",
        "metric_col": "total_revenue",
        "metric_label": "Highest Product Revenue",
        "answer_template": "The product generating the highest revenue is **{top_item}** with **${top_val:,.2f}** in total sales across {cat}."
    },

    "top_sales_region": {
        "title": "Highest Sales Region",
        "description": "Compares geographic territories by revenue and sales percentage.",
        "sql": """
            SELECT
                region,
                total_revenue,
                total_orders,
                pct_of_total_revenue,
                avg_order_value
            FROM analytics.mart_regional_performance
            ORDER BY total_revenue DESC;
        """,
        "chart_type": "pie",
        "names": "region",
        "values": "total_revenue",
        "metric_col": "total_revenue",
        "metric_label": "Top Region Sales",
        "answer_template": "The **{top_item}** region leads in sales with **${top_val:,.2f}**, representing **{top_pct}%** of total retail revenue."
    },

    "monthly_revenue_trend": {
        "title": "Monthly Revenue Trends",
        "description": "Tracks revenue changes month-by-month and calculates growth percentages.",
        "sql": """
            SELECT
                year_month,
                total_revenue,
                total_orders,
                total_quantity_sold,
                avg_order_value,
                mom_growth_pct
            FROM analytics.mart_monthly_revenue
            ORDER BY year_month ASC;
        """,
        "chart_type": "line",
        "x": "year_month",
        "y": "total_revenue",
        "metric_col": "total_revenue",
        "metric_label": "Annual Revenue",
        "answer_template": "Monthly revenue trends across 12 months show peak sales during Q4, with the highest single month recording **${top_val:,.2f}**."
    },

    "top_volume_products": {
        "title": "Top Products by Sales Volume",
        "description": "Ranks products based on the total physical units sold.",
        "sql": """
            SELECT
                product_name,
                category,
                total_units_sold,
                total_revenue,
                rank_by_volume
            FROM analytics.mart_product_performance
            ORDER BY total_units_sold DESC
            LIMIT 5;
        """,
        "chart_type": "bar",
        "x": "product_name",
        "y": "total_units_sold",
        "metric_col": "total_units_sold",
        "metric_label": "Highest Unit Volume",
        "answer_template": "The highest sales volume product is **{top_item}** with **{top_val:,} units** sold."
    },

    "average_order_value": {
        "title": "Average Order Value (AOV)",
        "description": "Calculates overall and regional Average Order Value across completed orders.",
        "sql": """
            SELECT
                'All Regions' AS territory,
                ROUND(SUM(total_revenue) / SUM(total_orders), 2) AS avg_order_value,
                SUM(total_orders) AS total_orders,
                ROUND(SUM(total_revenue), 2) AS total_revenue
            FROM analytics.mart_sales_summary;
        """,
        "chart_type": "kpi",
        "metric_col": "avg_order_value",
        "metric_label": "Average Order Value",
        "answer_template": "The overall Average Order Value (AOV) across the store is **${top_val:,.2f}** across {orders} total orders."
    },

    "completed_orders_count": {
        "title": "Completed Orders Count",
        "description": "Counts the number of orders successfully processed and completed.",
        "sql": """
            SELECT
                SUM(completed_orders) AS completed_orders,
                SUM(total_orders) AS total_orders,
                ROUND(SUM(completed_orders) * 100.0 / SUM(total_orders), 2) AS completion_rate_pct
            FROM analytics.mart_sales_summary;
        """,
        "chart_type": "kpi",
        "metric_col": "completed_orders",
        "metric_label": "Completed Orders",
        "answer_template": "There are **{top_val:,} completed orders** out of {total} total orders, achieving an order completion rate of **{pct}%**."
    },

    "category_performance": {
        "title": "Category Performance",
        "description": "Analyzes total revenue and order distribution across merchandise categories.",
        "sql": """
            SELECT
                category,
                ROUND(SUM(total_revenue), 2) AS total_revenue,
                SUM(total_orders) AS total_orders,
                SUM(total_quantity_sold) AS total_units_sold,
                ROUND(SUM(total_revenue) / SUM(total_orders), 2) AS avg_order_value
            FROM analytics.mart_sales_summary
            GROUP BY category
            ORDER BY total_revenue DESC;
        """,
        "chart_type": "bar",
        "x": "category",
        "y": "total_revenue",
        "metric_col": "total_revenue",
        "metric_label": "Top Category Revenue",
        "answer_template": "The top-performing category is **{top_item}** generating **${top_val:,.2f}** in gross revenue."
    }
}
