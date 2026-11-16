/*
    Model: mart_monthly_revenue
    Description:
      Monthly sales performance mart with month-over-month (MoM) revenue growth.
      Answers Business Question #3: "How does revenue change month by month?"
*/

WITH sales AS (
    SELECT * FROM {{ ref('stg_retail_sales') }}
),

monthly AS (
    SELECT
        FORMAT_DATE('%Y-%m', order_date) AS year_month,
        DATE_TRUNC(order_date, MONTH) AS month_start_date,
        ROUND(SUM(revenue), 2) AS total_revenue,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT CASE WHEN payment_status = 'Completed' THEN order_id END) AS completed_orders,
        SUM(quantity) AS total_quantity_sold,
        ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value
    FROM sales
    GROUP BY
        FORMAT_DATE('%Y-%m', order_date),
        DATE_TRUNC(order_date, MONTH)
),

with_growth AS (
    SELECT
        year_month,
        month_start_date,
        total_revenue,
        total_orders,
        completed_orders,
        total_quantity_sold,
        avg_order_value,
        LAG(total_revenue) OVER (ORDER BY year_month ASC) AS previous_month_revenue,
        ROUND(
            (total_revenue - LAG(total_revenue) OVER (ORDER BY year_month ASC)) /
            NULLIF(LAG(total_revenue) OVER (ORDER BY year_month ASC), 0) * 100,
            2
        ) AS mom_growth_pct
    FROM monthly
)

SELECT * FROM with_growth
ORDER BY year_month ASC
