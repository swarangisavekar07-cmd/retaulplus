/*
    Model: mart_regional_performance
    Description:
      Regional sales breakdown comparing territories by total revenue, order count, and AOV.
      Answers Business Question #2: "Which region has the highest sales?"
*/

WITH sales AS (
    SELECT * FROM {{ ref('stg_retail_sales') }}
),

regional AS (
    SELECT
        region,
        ROUND(SUM(revenue), 2) AS total_revenue,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT CASE WHEN payment_status = 'Completed' THEN order_id END) AS completed_orders,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value
    FROM sales
    GROUP BY region
),

with_percentages AS (
    SELECT
        region,
        total_revenue,
        total_orders,
        completed_orders,
        total_units_sold,
        avg_order_value,
        ROUND(
            total_revenue / NULLIF(SUM(total_revenue) OVER (), 0) * 100,
            2
        ) AS pct_of_total_revenue,
        DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS rank_by_sales
    FROM regional
)

SELECT * FROM with_percentages
ORDER BY rank_by_sales ASC
