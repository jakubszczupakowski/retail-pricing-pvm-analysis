import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_synthetic_retail_data():
    os.makedirs('data_raw', exist_ok=True)
    os.makedirs('data_clean', exist_ok=True)

    np.random.seed(42)

    # 1. Product Dimension (Dim_Product)
    n_products = 100
    categories = ['Electronics', 'Home & Kitchen', 'Home & Garden', 'Sports']
    brands = ['Apex', 'Vanguard', 'Horizon', 'Delta', 'Nova']

    products_data = {
        'product_id': [f'PRD_{i:03d}' for i in range(1, n_products + 1)],
        'product_name': [f'Product {i}' for i in range(1, n_products + 1)],
        'category': np.random.choice(categories, n_products),
        'brand': np.random.choice(brands, n_products),
        'base_price': np.round(np.random.uniform(50, 3000, n_products), 2),
    }
    df_products = pd.DataFrame(products_data)
    # Unit cost baseline (COGS: 50% - 75% of base price)
    df_products['unit_cost'] = np.round(
        df_products['base_price'] * np.random.uniform(0.50, 0.75, n_products), 2
    )

    # 2. Store Dimension (Dim_Store)
    stores_data = {
        'store_id': ['STR_001', 'STR_002', 'STR_003', 'STR_004', 'STR_ONLINE'],
        'store_name': [
            'Central Hub Retail',
            'West Coast Store',
            'North Flagship',
            'South Outlet',
            'E-Commerce Channel',
        ],
        'region': ['Central', 'West', 'North', 'South', 'Online'],
        'channel': ['Offline', 'Offline', 'Offline', 'Offline', 'Online'],
    }
    df_stores = pd.DataFrame(stores_data)

    # 3. Transaction Fact Table (Fact_Sales)
    n_transactions = 200000
    start_date = datetime(2024, 1, 1)

    date_series = [
        start_date + timedelta(days=int(np.random.randint(0, 730)))
        for _ in range(n_transactions)
    ]
    product_samples = np.random.choice(df_products['product_id'], n_transactions)
    store_samples = np.random.choice(df_stores['store_id'], n_transactions)
    qty_samples = np.random.choice(
        [1, 2, 3, 4, 5], n_transactions, p=[0.60, 0.25, 0.10, 0.03, 0.02]
    )

    promo_mechanics = ['No Promo', 'Catalog -10%', 'Seasonal -20%', 'Clearance -35%']
    promo_distribution = [0.50, 0.25, 0.15, 0.10]
    promo_samples = np.random.choice(
        promo_mechanics, n_transactions, p=promo_distribution
    )

    df_sales = pd.DataFrame({
        'transaction_id': [f'TRX_{i:07d}' for i in range(1, n_transactions + 1)],
        'transaction_date': date_series,
        'store_id': store_samples,
        'product_id': product_samples,
        'quantity': qty_samples,
        'promo_type': promo_samples,
    })

    # Join baseline prices and costs
    df_sales = df_sales.merge(
        df_products[['product_id', 'base_price', 'unit_cost']],
        on='product_id',
        how='left',
    )

    # Price markdown logic
    discount_mapping = {
        'Catalog -10%': 0.90,
        'Seasonal -20%': 0.80,
        'Clearance -35%': 0.65,
    }

    df_sales['discount_rate'] = (
        df_sales['promo_type'].map(discount_mapping).fillna(1.0)
    )
    df_sales['unit_selling_price'] = np.round(
        df_sales['base_price'] * df_sales['discount_rate'], 2
    )
    df_sales['gross_revenue'] = np.round(
        df_sales['unit_selling_price'] * df_sales['quantity'], 2
    )
    df_sales['total_cogs'] = np.round(
        df_sales['unit_cost'] * df_sales['quantity'], 2
    )

    # Export raw data extract
    df_products.to_csv('data_raw/dim_products_raw.csv', index=False)
    df_stores.to_csv('data_raw/dim_stores_raw.csv', index=False)
    df_sales.to_csv('data_raw/fact_transactions_raw.csv', index=False)

    print("Data generation complete:")
    print(" - data_raw/dim_products_raw.csv")
    print(" - data_raw/dim_stores_raw.csv")
    print(" - data_raw/fact_transactions_raw.csv")


if __name__ == '__main__':
    generate_synthetic_retail_data()