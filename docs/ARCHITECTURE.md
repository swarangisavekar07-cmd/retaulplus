# RetailPulse AI — System Architecture & Data Flow

This document details the end-to-end architectural design of **RetailPulse AI**, an enterprise-grade automated Modern Data Stack (MDS) implementation for retail sales analytics and conversational Business Intelligence.

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph DATA_SOURCE ["1. Source Ingestion Layer"]
        CSV["📄 Retail Sales CSV<br>(810 Records, Synthetic)"]
        CSV -->|"Batch Insert / psycopg2"| PG[("🐘 PostgreSQL (Source DB)<br>public.retail_sales")]
    end

    subgraph INGESTION ["2. Automated ELT Ingestion"]
        PG -->|"CDC / Full-Refresh Sync"| AB["🔄 Airbyte Ingestion Engine<br>(API v1 / Octavia)"]
        AB -->|"Direct Streaming Load"| BQ_RAW[("☁️ Google BigQuery<br>raw_retailpulse.retail_sales")]
    end

    subgraph TRANSFORMATION ["3. Transformation Layer (dbt-bigquery)"]
        BQ_RAW --> STG["🔍 Staging View: stg_retail_sales<br>• Column Standardization<br>• Type Casting & Null Imputation<br>• Deduplication via ROW_NUMBER()<br>• Line Revenue = qty * price"]
        
        STG --> M1["📊 mart_sales_summary<br>(Multi-dimensional KPI rollups)"]
        STG --> M2["📈 mart_monthly_revenue<br>(MoM trends & growth %)"]
        STG --> M3["🏆 mart_product_performance<br>(Revenue & volume ranks)"]
        STG --> M4["🌍 mart_regional_performance<br>(Territory sales & share %)"]

        STG -.->|"Schema & Integrity Assertions"| TESTS["🧪 dbt Test Suite<br>• unique(order_id)<br>• not_null(order_id, product_name)<br>• non_negative(quantity, price)"]
    end

    subgraph WAREHOUSE ["4. Analytical Warehouse Serving"]
        M1 --> BQ_ANALYTICS[("☁️ Google BigQuery / Analytics Marts<br>analytics_retailpulse")]
        M2 --> BQ_ANALYTICS
        M3 --> BQ_ANALYTICS
        M4 --> BQ_ANALYTICS
    end

    subgraph PRESENTATION ["5. Presentation & Conversational BI"]
        BQ_ANALYTICS --> APP["⚡ RetailPulse AI Dashboard<br>(Streamlit + Plotly + SQL Engine)"]
        APP --> CHAT["💬 Conversational Natural Language Assistant<br>• Intent Parser / Regex Engine<br>• Read-Only Parameterized SQL<br>• Dynamic Chart & KPI Formatter"]
        APP --> INSIGHTS["💡 Real-Time Business Actionable Insights"]
    end

    subgraph ORCHESTRATION ["6. Orchestration Layer (Apache Airflow)"]
        DAG["⚙️ DAG: retail_sales_pipeline<br>Schedule: @daily"]
        T1["start_pipeline"] --> T2["validate_source"]
        T2 --> T3["trigger_airbyte_sync"]
        T3 --> T4["wait_for_ingestion"]
        T4 --> T5["run_dbt_models"]
        T5 --> T6["run_dbt_tests"]
        T6 --> T7["validate_warehouse"]
        T7 --> T8["end_pipeline"]
    end

    %% Airflow Coordination Links (Control Plane)
    T2 -.->|"Asserts row presence"| PG
    T3 -.->|"Triggers /api/v1/connections/sync"| AB
    T4 -.->|"Polls job status until terminal"| AB
    T5 -.->|"Executes dbt run"| STG
    T6 -.->|"Executes dbt test"| TESTS
    T7 -.->|"Asserts warehouse metrics"| BQ_ANALYTICS

    classDef sourceStyle fill:#1E293B,stroke:#3B82F6,stroke-width:2px,color:#FFFFFF;
    classDef ingestStyle fill:#0F172A,stroke:#10B981,stroke-width:2px,color:#FFFFFF;
    classDef dbtStyle fill:#1E1B4B,stroke:#8B5CF6,stroke-width:2px,color:#FFFFFF;
    classDef bqStyle fill:#1E293B,stroke:#F59E0B,stroke-width:2px,color:#FFFFFF;
    classDef biStyle fill:#064E3B,stroke:#34D399,stroke-width:2px,color:#FFFFFF;
    classDef airflowStyle fill:#3B0764,stroke:#C084FC,stroke-width:2px,color:#FFFFFF;

    class CSV,PG sourceStyle;
    class AB ingestStyle;
    class STG,M1,M2,M3,M4,TESTS dbtStyle;
    class BQ_RAW,BQ_ANALYTICS bqStyle;
    class APP,CHAT,INSIGHTS biStyle;
    class DAG,T1,T2,T3,T4,T5,T6,T7,T8 airflowStyle;
```

---

## 2. Component Decoupling & Principles

### Separation of Data Plane vs Control Plane
- **Data Plane (Heavy Lifting):** Data flows sequentially from CSV → PostgreSQL → Airbyte → BigQuery → dbt → Streamlit.
- **Control Plane (Orchestration):** Apache Airflow does **not** move bytes directly across network streams. Instead, Airflow acts strictly as the conductor:
  - Validates source availability
  - Issues REST API instructions to Airbyte
  - Awaits sensor confirmations
  - Dispatches `dbt` transformation commands
  - Executes data tests
  - Verifies warehouse table row counts and total gross revenue integrity.

### Data Warehouse Dual-Mode Strategy
To satisfy both cloud production requirements and offline faculty presentation requirements, the system implements a dual-mode connector:
1. **Cloud Mode:** Direct BigQuery SDK queries targeting `project_id.analytics_retailpulse`.
2. **Local Replica Mode:** High-performance DuckDB analytical engine holding the exact dbt-transformed tables. The user interface features an explicit diagnostic badge displaying which warehouse backend is actively responding.
