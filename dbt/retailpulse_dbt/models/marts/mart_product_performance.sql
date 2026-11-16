/*
    Model: mart_product_performance
    Description:
      Product catalog analytics ranking products by revenue and sales volume.
      Answers Business Question #1: "Which product generates the highest revenue?"
      Answers Business Question #4: "Which products have the highest sales volume?"
*/

WITH sales AS (
    SELECT * FROM {{ ref('stg_retail_sales') }}
),

product_metrics AS (
    SELECT
        product_id,
        product_name,
        category,
        ROUND(SUM(revenue), 2) AS total_revenue,
        SUM(quantity) AS total_units_sold,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT CASE WHEN payment_status = 'Completed' THEN order_id END) AS completed_orders,
        ROUND(AVG(unit_price), 2) AS avg_unit_price,
        ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS revenue_per_order
    FROM sales
    GROUP BY
        product_id,
        product_name,
        category
),

ranked AS (
    SELECT
        product_id,
        product_name,
        category,
        total_revenue,
        total_units_sold,
        total_orders,
        completed_orders,
        avg_unit_price,
        revenue_per_order,
        DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS rank_by_revenue,
        DENSE_RANK() OVER (ORDER BY total_units_sold DESC) AS rank_by_volume
    FROM product_metrics
)

SELECT * FROM ranked
ORDER BY rank_by_revenue ASC
