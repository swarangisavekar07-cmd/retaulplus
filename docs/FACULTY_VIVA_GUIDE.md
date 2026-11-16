# RetailPulse AI — Faculty Demonstration & Viva Defense Guide

This guide is designed for engineering students presenting **RetailPulse AI** during academic reviews, project demonstrations, and viva voce examinations.

---

## 1. 2-Minute Project Pitch (Elevator Pitch)

> *"Good morning professors. RetailPulse AI is an enterprise-grade automated Modern Data Stack (MDS) implementation for retail sales analytics and conversational Business Intelligence.*
>
> *We established an automated end-to-end pipeline: transactional sales records from a PostgreSQL database are ingested into Google BigQuery using Airbyte. Inside BigQuery, raw records undergo cleaning, deduplication, and multidimensional modeling using dbt. Apache Airflow orchestrates all 8 tasks as a cohesive workflow DAG with dependency validation. Finally, we provide a Conversational BI interface built in Streamlit that allows business executives to ask natural language questions—such as 'Which product generates the highest revenue?'—and receive live SQL execution results, KPI cards, and dynamic Plotly charts from actual transformed warehouse marts."*

---

## 2. Walkthrough of the 6 Mandatory Business Questions

| # | Business Question | Executed Mart | Exact Analytical Answer (Verified) | Visualization |
|---|-------------------|---------------|------------------------------------|---------------|
| 1 | **Which product generates the highest revenue?** | `analytics.mart_product_performance` | **4K Ultra HD 27-inch IPS Monitor** ($45,522.35 total revenue) | Horizontal Bar Chart |
| 2 | **Which region has the highest sales?** | `analytics.mart_regional_performance` | **East** Region ($43,720.63, 28.47% market share) | Donut Distribution |
| 3 | **How does revenue change month by month?** | `analytics.mart_monthly_revenue` | Peak sales in Q4, highest single month: **$29,957.25** | Line + Bar Trend Combo |
| 4 | **Which products have the highest sales volume?** | `analytics.mart_product_performance` | **4K Ultra HD 27-inch IPS Monitor** (132 units sold) | Ranked Bar Chart |
| 5 | **What is the average order value?** | `analytics.mart_sales_summary` | Overall AOV: **$191.94** across 800 total orders | KPI Metric Card |
| 6 | **How many orders are completed?** | `analytics.mart_sales_summary` | **680 completed orders** (85.0% completion rate) | Metric + Completion % |
| 7 | **Which category performs best?** | `analytics.mart_sales_summary` | **Electronics** ($83,106.78 gross revenue) | Categorical Bar Chart |

---

## 3. Sample SQL Queries Executed by Conversational BI

### Query 1: Top Product by Revenue
```sql
SELECT
    product_name,
    category,
    total_revenue,
    total_units_sold,
    rank_by_revenue
FROM analytics.mart_product_performance
ORDER BY total_revenue DESC
LIMIT 5;
```

### Query 2: Regional Sales Breakdown
```sql
SELECT
    region,
    total_revenue,
    total_orders,
    pct_of_total_revenue,
    avg_order_value
FROM analytics.mart_regional_performance
ORDER BY total_revenue DESC;
```

### Query 3: Monthly Revenue Trend & MoM Growth
```sql
SELECT
    year_month,
    total_revenue,
    total_orders,
    total_quantity_sold,
    avg_order_value,
    mom_growth_pct
FROM analytics.mart_monthly_revenue
ORDER BY year_month ASC;
```

### Query 4: Average Order Value & Order Status
```sql
SELECT
    SUM(completed_orders) AS completed_orders,
    SUM(total_orders) AS total_orders,
    ROUND(SUM(completed_orders) * 100.0 / SUM(total_orders), 2) AS completion_rate_pct
FROM analytics.mart_sales_summary;
```

---

## 4. Key Viva Questions & Answers

### Q1: Why use ELT (Extract-Load-Transform) with Airbyte and dbt instead of traditional ETL with Python scripts?
**Answer:**
In traditional ETL, data is transformed in-memory using Python or an intermediate server before loading, which creates computational bottlenecks and requires proprietary transformation scripts. In ELT:
1. **Airbyte** focuses strictly on high-throughput, standardized extraction and loading from source to warehouse.
2. **dbt** executes SQL transformations natively inside cloud warehouses (BigQuery), leveraging massively parallel processing (MPP), columnar storage, and automatic partition caching.
3. Transformations are version-controlled, modular, reproducible, and verifiable with dbt test assertions.

### Q2: How did you handle duplicate transactions and missing values in dbt?
**Answer:**
In `models/staging/stg_retail_sales.sql`:
1. **Deduplication:** We applied a SQL window function:
   ```sql
   ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_date DESC) AS row_num
   ```
   and filtered `WHERE row_num = 1`. In our synthetic test dataset containing 10 duplicate rows, exactly 10 rows were pruned, moving from 810 raw rows to 800 clean staged rows.
2. **Missing Customer Names:** Replaced nulls with `'Guest Customer'` using `COALESCE(NULLIF(TRIM(customer_name), ''), 'Guest Customer')`.
3. **Missing Payment Status:** Normalized nulls to `'Pending'` using `COALESCE(payment_status, 'Pending')`.
4. **Data Tests:** Asserted `unique` and `not_null` on `order_id`, `not_null` on `product_name`, and custom `non_negative` checks on `quantity` and `unit_price`.

### Q3: Why is Apache Airflow separated from the data processing tasks?
**Answer:**
Airflow is an orchestration engine (the control plane), not a data execution engine (the data plane). Passing large volumes of data directly through Airflow workers or XCom creates severe memory overhead and violates data engineering best practices. Airflow simply coordinates:
- Validates data availability
- Issues API calls to Airbyte (`/api/v1/connections/sync`)
- Polls for completion
- Triggers `dbt run` and `dbt test`
- Performs end-of-pipeline warehouse validation

### Q4: How is security ensured in the Conversational BI interface?
**Answer:**
1. **Strict Read-Only Enforcement:** The query engine verifies that SQL statements begin exclusively with `SELECT` or `WITH` and rejects destructive keywords (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, `EXEC`).
2. **Sanitized Credential Management:** Service account keys and database passwords are stored exclusively in `.env` and loaded via system environment variables. They are never exposed in UI or committed to git.
3. **Schema Isolation:** The Streamlit application is granted read-only access strictly to the `analytics.*` marts schema.
