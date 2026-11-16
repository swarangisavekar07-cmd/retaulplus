/*
    Model: mart_sales_summary
    Description:
      Core analytics mart providing multidimensional aggregations across
      products, categories, regions, and dates.
      Powers executive KPI calculations, conversational BI queries,
      and Streamlit visual dashboards.
*/

WITH sales AS (
    SELECT * FROM {{ ref('stg_retail_sales') }}
),

aggregated AS (
    SELECT
        order_date,
        FORMAT_DATE('%Y-%m', order_date) AS year_month,
        region,
        category,
        product_id,
        product_name,
        -- Total transaction and completed order counts
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT CASE WHEN payment_status = 'Completed' THEN order_id END) AS completed_orders,
        -- Total units sold
        SUM(quantity) AS total_quantity_sold,
        -- Total revenue
        ROUND(SUM(revenue), 2) AS total_revenue,
        -- Average order value
        ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value
    FROM sales
    GROUP BY
        order_date,
        FORMAT_DATE('%Y-%m', order_date),
        region,
        category,
        product_id,
        product_name
)

SELECT * FROM aggregated
