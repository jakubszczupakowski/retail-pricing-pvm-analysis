import os
import duckdb


def run_pricing_etl():
    os.makedirs('data_clean', exist_ok=True)

    # In-memory DuckDB instance for pipeline transformations
    con = duckdb.connect(database=':memory:')

    # 1. Product Dimension: calculate baseline unit economics
    con.execute("""
        CREATE TABLE dim_product AS
        SELECT 
            product_id,
            product_name,
            category,
            brand,
            base_price,
            unit_cost,
            ROUND(base_price - unit_cost, 2) AS standard_unit_margin,
            ROUND((base_price - unit_cost) / base_price, 4) AS standard_margin_rate
        FROM read_csv_auto('data_raw/dim_products_raw.csv')
    """)
    con.execute(
        "COPY dim_product TO 'data_clean/dim_product.parquet' (FORMAT PARQUET)"
    )

    # 2. Store Dimension
    con.execute("""
        CREATE TABLE dim_store AS
        SELECT 
            store_id,
            store_name,
            region,
            channel
        FROM read_csv_auto('data_raw/dim_stores_raw.csv')
    """)
    con.execute(
        "COPY dim_store TO 'data_clean/dim_store.parquet' (FORMAT PARQUET)"
    )

    # 3. Sales Fact Table: cast types, set promo flag, derive margin
    con.execute("""
        CREATE TABLE fact_sales AS
        SELECT 
            transaction_id,
            CAST(transaction_date AS DATE) AS transaction_date,
            store_id,
            product_id,
            quantity,
            promo_type,
            CASE 
                WHEN promo_type = 'No Promo' THEN 0 
                ELSE 1 
            END AS is_promo,
            discount_rate,
            unit_selling_price,
            gross_revenue,
            total_cogs,
            ROUND(gross_revenue - total_cogs, 2) AS gross_margin
        FROM read_csv_auto('data_raw/fact_transactions_raw.csv')
    """)
    con.execute(
        "COPY fact_sales TO 'data_clean/fact_sales.parquet' (FORMAT PARQUET)"
    )

    con.close()


if __name__ == '__main__':
    run_pricing_etl()