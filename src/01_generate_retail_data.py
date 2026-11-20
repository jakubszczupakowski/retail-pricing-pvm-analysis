import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_synthetic_retail_data():
    os.makedirs('data_raw', exist_ok=True)
    os.makedirs('data_clean', exist_ok=True)

    np.random.seed(42)

    # 1. Product Dimension Table (Dim_Product)
    n_products = 200
    categories = ['Electronics', 'Home & Kitchen', 'Home & Garden', 'Sports']
    prod_categories = np.random.choice(categories, n_products, p=[0.25, 0.25, 0.25, 0.25])

    # Distinct price tiers per category to drive a clear negative Mix Effect
    base_prices = np.where(
        prod_categories == 'Electronics',
        np.random.uniform(1100, 2500, n_products),
        np.random.uniform(120, 480, n_products)
    ).round(2)

    margin_rates = np.where(
        prod_categories == 'Electronics',
        np.random.uniform(0.25, 0.35, n_products),
        np.random.uniform(0.42, 0.55, n_products)
    )
    unit_costs = (base_prices * (1 - margin_rates)).round(2)

    brands = ['Apex', 'NordicHome', 'Veloce', 'Lumina', 'Kinetix']

    df_products = pd.DataFrame({
        'product_id': [f'PROD_{i:04d}' for i in range(1, n_products + 1)],
        'product_name': [f'Product {i:04d}' for i in range(1, n_products + 1)],
        'category': prod_categories,
        'brand': np.random.choice(brands, n_products),
        'base_price': base_prices,
        'unit_cost': unit_costs,
    })

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

    # 3. Transaction Fact Table (Fact_Sales) - 3 Full Years (2023, 2024, 2025)
    n_transactions = 172500

    # Progressive volume growth: 2023 (30%), 2024 (34%), 2025 (36%)
    years = np.random.choice([2023, 2024, 2025], size=n_transactions, p=[0.30, 0.34, 0.36])
    random_days = np.random.randint(0, 365, size=n_transactions)
    date_series = [
        datetime(int(y), 1, 1) + timedelta(days=int(d))
        for y, d in zip(years, random_days)
    ]

    # Category mix shift across years:
    # 2023 -> 2024: slight premiumization (+Mix)
    # 2024 -> 2025: strong shift away from expensive Electronics (-Mix red bar)
    cat_weights = {
        2023: {'Electronics': 0.34, 'Home & Kitchen': 0.22, 'Home & Garden': 0.22, 'Sports': 0.22},
        2024: {'Electronics': 0.40, 'Home & Kitchen': 0.20, 'Home & Garden': 0.20, 'Sports': 0.20},
        2025: {'Electronics': 0.16, 'Home & Kitchen': 0.34, 'Home & Garden': 0.25, 'Sports': 0.25},
    }

    product_samples = np.empty(n_transactions, dtype=object)
    for yr in [2023, 2024, 2025]:
        mask = (years == yr)
        weights = df_products['category'].map(cat_weights[yr])
        weights = weights / weights.sum()
        product_samples[mask] = np.random.choice(df_products['product_id'], size=mask.sum(), p=weights)

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
        df_products[['product_id', 'base_price', 'unit_cost', 'category']],
        on='product_id',
        how='left',
    )

    # Progressive YoY price inflation: 2023 (1.00x) -> 2024 (1.065x) -> 2025 (1.145x)
    tx_year = pd.to_datetime(df_sales['transaction_date']).dt.year
    price_multiplier = np.select(
        [tx_year == 2023, tx_year == 2024, tx_year == 2025],
        [1.00, 1.065, 1.145],
        default=1.00
    )
    df_sales['effective_base_price'] = df_sales['base_price'] * price_multiplier

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
        df_sales['effective_base_price'] * df_sales['discount_rate'], 2
    )
    df_sales['gross_revenue'] = np.round(
        df_sales['unit_selling_price'] * df_sales['quantity'], 2
    )
    df_sales['total_cogs'] = np.round(
        df_sales['unit_cost'] * df_sales['quantity'], 2
    )

    df_sales = df_sales.drop(columns=['category', 'effective_base_price'])

    # Export raw data extract
    df_products.to_csv('data_raw/dim_products_raw.csv', index=False)
    df_stores.to_csv('data_raw/dim_stores_raw.csv', index=False)
    df_sales.to_csv('data_raw/fact_transactions_raw.csv', index=False)


if __name__ == '__main__':
    generate_synthetic_retail_data()