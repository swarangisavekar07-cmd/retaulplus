-- ====================================================================
-- RetailPulse AI — PostgreSQL Source Database Initialization
-- ====================================================================
-- Database: retail_pulse_db (or postgres default)
-- Table: public.retail_sales
-- Purpose: Source transactional store serving raw retail sales data
--          for Airbyte ingestion into Google BigQuery.
-- ====================================================================

-- Drop table if exists to allow clean re-initialization
DROP TABLE IF EXISTS public.retail_sales CASCADE;

-- Create retail_sales source table
CREATE TABLE public.retail_sales (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    order_date DATE NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    customer_name VARCHAR(128),
    product_id VARCHAR(64) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    region VARCHAR(64) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    payment_status VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comments on table and columns for data governance & schema cataloging
COMMENT ON TABLE public.retail_sales IS 'Source transactional table holding retail sales records to be synced via Airbyte to BigQuery';
COMMENT ON COLUMN public.retail_sales.order_id IS 'Unique business order identifier';
COMMENT ON COLUMN public.retail_sales.order_date IS 'Calendar date when transaction was recorded';
COMMENT ON COLUMN public.retail_sales.customer_id IS 'Unique customer identifier';
COMMENT ON COLUMN public.retail_sales.customer_name IS 'Customer name (may be null for anonymous guest checkout)';
COMMENT ON COLUMN public.retail_sales.product_id IS 'Stock Keeping Unit or product identifier';
COMMENT ON COLUMN public.retail_sales.product_name IS 'Descriptive title of product';
COMMENT ON COLUMN public.retail_sales.category IS 'High-level commercial merchandise category';
COMMENT ON COLUMN public.retail_sales.region IS 'Sales territory / geographical zone';
COMMENT ON COLUMN public.retail_sales.quantity IS 'Number of units ordered';
COMMENT ON COLUMN public.retail_sales.unit_price IS 'Sales price per item in USD';
COMMENT ON COLUMN public.retail_sales.payment_status IS 'Transaction status: Completed, Pending, Cancelled, Refunded';

-- Indexes for efficient querying, delta capture, and Airbyte incremental sync
CREATE INDEX idx_retail_sales_order_date ON public.retail_sales(order_date);
CREATE INDEX idx_retail_sales_region ON public.retail_sales(region);
CREATE INDEX idx_retail_sales_category ON public.retail_sales(category);
CREATE INDEX idx_retail_sales_created_at ON public.retail_sales(created_at);
