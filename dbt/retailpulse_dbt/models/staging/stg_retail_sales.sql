/*
    Model: stg_retail_sales
    Description:
      Staging transformation for raw retail sales ingested from PostgreSQL via Airbyte.
      Standardizes column names, casts types, cleans nulls, deduplicates on order_id,
      and calculates gross line-item revenue.
*/

WITH source_data AS (
    SELECT
        TRIM(CAST(order_id AS STRING)) AS order_id,
        SAFE_CAST(order_date AS DATE) AS order_date,
        TRIM(CAST(customer_id AS STRING)) AS customer_id,
        COALESCE(NULLIF(TRIM(CAST(customer_name AS STRING)), ''), 'Guest Customer') AS customer_name,
        TRIM(CAST(product_id AS STRING)) AS product_id,
        TRIM(CAST(product_name AS STRING)) AS product_name,
        TRIM(CAST(category AS STRING)) AS category,
        TRIM(CAST(region AS STRING)) AS region,
        CAST(quantity AS INT64) AS quantity,
        ROUND(CAST(unit_price AS NUMERIC), 2) AS unit_price,
        COALESCE(NULLIF(TRIM(CAST(payment_status AS STRING)), ''), 'Pending') AS payment_status,
        -- Window function to assign row numbers for deduplication
        ROW_NUMBER() OVER (
            PARTITION BY TRIM(CAST(order_id AS STRING))
            ORDER BY SAFE_CAST(order_date AS DATE) DESC
        ) AS row_num
    FROM {{ source('airbyte_raw', 'retail_sales') }}
    WHERE order_id IS NOT NULL
),

deduplicated AS (
    SELECT
        order_id,
        order_date,
        customer_id,
        customer_name,
        product_id,
        product_name,
        category,
        region,
        quantity,
        unit_price,
        -- Calculated revenue: quantity * unit_price
        ROUND(CAST(quantity AS NUMERIC) * unit_price, 2) AS revenue,
        payment_status
    FROM source_data
    WHERE row_num = 1
)

SELECT * FROM deduplicated
