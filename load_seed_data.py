"""Load fake seed data into the embedded SQLite analytics database.

Uses parameterized INSERTs via Python's sqlite3 module. Python booleans map
to SQLite INTEGER (0/1) automatically.

Run create_schema.py first to create the tables.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "analytics.db"


DIM_CUSTOMER = [
    ('CUST001', 1, '2024-01-01', None, True, 'Ava', 'Patel', 'hash_email_001', 'hash_phone_001', 'Female', '1992-04-15', 'San Francisco', 'CA', 'USA', '94105', True,  True,  False, 'Gold'),
    ('CUST002', 1, '2024-01-01', None, True, 'Liam', 'Chen', 'hash_email_002', 'hash_phone_002', 'Male',   '1988-09-22', 'Seattle',       'WA', 'USA', '98101', True,  False, True,  'Silver'),
    ('CUST003', 1, '2024-01-01', None, True, 'Mia', 'Garcia', 'hash_email_003', 'hash_phone_003', 'Female', '1995-12-03', 'Austin',       'TX', 'USA', '78701', False, False, True,  'Bronze'),
    ('CUST004', 1, '2024-01-01', None, True, 'Noah', 'Wilson', 'hash_email_004', 'hash_phone_004', 'Male',   '1983-07-11', 'New York',    'NY', 'USA', '10001', True,  True,  True,  'Platinum'),
    ('CUST005', 1, '2024-01-01', None, True, 'Sophia', 'Kim', 'hash_email_005', 'hash_phone_005', 'Female', '1990-02-28', 'Chicago',      'IL', 'USA', '60601', True,  False, False, 'Gold'),
]

BRIDGE_IDENTITY = [
    ('email_hash_ava_001',    'CUST001', 'email',     'web_app',    '2024-01-05 10:15:00', '2024-06-01 08:45:00'),
    ('cookie_abc123',         'CUST001', 'cookie',    'website',    '2024-02-12 14:20:00', '2024-06-02 19:05:00'),
    ('email_hash_liam_002',   'CUST002', 'email',     'mobile_app', '2024-01-10 09:00:00', '2024-05-28 11:30:00'),
    ('device_xyz789',         'CUST003', 'device_id', 'mobile_app', '2024-03-01 16:45:00', '2024-06-01 20:10:00'),
    ('cookie_nyc456',         'CUST004', 'cookie',    'website',    '2024-01-20 12:00:00', '2024-06-03 13:25:00'),
    ('email_hash_sophia_005', 'CUST005', 'email',     'crm',        '2024-02-01 08:30:00', '2024-06-01 17:40:00'),
]

DIM_PRODUCT = [
    ('PROD001', 'SKU-1001', 'Everyday Running Shoe',            'StrideCo',    'Footwear',    'Running Shoes', 'Athletics', 42.00,  89.99, 0.5333, 0.8700, True),
    ('PROD002', 'SKU-1002', 'Insulated Travel Mug',             'ThermoGo',    'Home',        'Drinkware',     'Kitchen',    8.50,  24.99, 0.6599, 0.7200, True),
    ('PROD003', 'SKU-1003', 'Organic Cotton Hoodie',            'UrbanNest',   'Apparel',     'Hoodies',       'Clothing',  21.00,  59.99, 0.6499, 0.8100, True),
    ('PROD004', 'SKU-1004', 'Wireless Noise-Canceling Earbuds', 'SoundLoop',   'Electronics', 'Audio',         'Tech',      38.00, 119.99, 0.6833, 0.9100, True),
    ('PROD005', 'SKU-1005', 'Adjustable Standing Desk Lamp',    'BrightWorks', 'Home Office', 'Lighting',      'Furniture', 17.50,  49.99, 0.6499, 0.6900, True),
]

DIM_CAMPAIGN = [
    ('CAMP001', 'Spring Sneaker Launch',   'Meta',       'Paid Social', 'CRE001', 'Video - Runner Lifestyle',     15000.00, '2024-03-01', '2024-03-31'),
    ('CAMP002', 'Mug Bundle Promo',        'Google Ads', 'Paid Search', 'CRE002', 'Search - Travel Mug Discount',  8000.00, '2024-04-01', '2024-04-30'),
    ('CAMP003', 'Hoodie Retargeting',      'TikTok',     'Paid Social', 'CRE003', 'UGC - Cozy Hoodie',            12000.00, '2024-04-15', '2024-05-15'),
    ('CAMP004', 'Earbuds Holiday Push',    'YouTube',    'Video',       'CRE004', 'Product Demo - Earbuds',       22000.00, '2024-05-01', '2024-06-15'),
    ('CAMP005', 'Home Office Essentials',  'Email',      'Owned Email', 'CRE005', 'Newsletter - Desk Setup',       3000.00, '2024-05-10', '2024-06-10'),
]

DIM_LOCATION = [
    ('LOC001', 'STORE001', 'San Francisco Market Street', 'store', 37.7749, -122.4194, 'San Francisco', 'CA', 'USA', '94105', 'America/Los_Angeles', 'West'),
    ('LOC002', 'STORE002', 'Seattle Downtown',            'store', 47.6062, -122.3321, 'Seattle',       'WA', 'USA', '98101', 'America/Los_Angeles', 'West'),
    ('LOC003', 'STORE003', 'Austin South Congress',       'store', 30.2672, -97.7431,  'Austin',        'TX', 'USA', '78701', 'America/Chicago',     'South'),
    ('LOC004', 'STORE004', 'New York Flatiron',           'store', 40.7411, -73.9897,  'New York',      'NY', 'USA', '10001', 'America/New_York',    'East'),
    ('LOC005', 'GEO001',   'Chicago Metro',               'geo',   41.8781, -87.6298,  'Chicago',       'IL', 'USA', '60601', 'America/Chicago',     'Midwest'),
]

FACT_INTERACTION = [
    ('EVT001', '2024-05-01 09:15:00', '2024-05-01', 'CUST001', 'cookie_abc123',         'SESS001', 'PROD001', 'CAMP001', 'LOC001', 'view',       'website',    'mobile',  '/products/running-shoe', 'google.com',  1, 0, 1, 0, 0),
    ('EVT002', '2024-05-01 09:17:00', '2024-05-01', 'CUST001', 'cookie_abc123',         'SESS001', 'PROD001', 'CAMP001', 'LOC001', 'click',      'website',    'mobile',  '/products/running-shoe', 'google.com',  0, 1, 0, 0, 0),
    ('EVT003', '2024-05-02 13:30:00', '2024-05-02', 'CUST002', 'email_hash_liam_002',   'SESS002', 'PROD002', 'CAMP002', 'LOC002', 'purchase',   'mobile_app', 'ios',     '/checkout',              'email',       0, 0, 0, 1, 0),
    ('EVT004', '2024-05-03 18:45:00', '2024-05-03', 'CUST003', 'device_xyz789',         'SESS003', 'PROD003', 'CAMP003', 'LOC003', 'impression', 'mobile_app', 'android', '/home',                  'tiktok.com',  1, 0, 0, 0, 0),
    ('EVT005', '2024-05-04 20:05:00', '2024-05-04', 'CUST004', 'cookie_nyc456',         'SESS004', 'PROD004', 'CAMP004', 'LOC004', 'login',      'website',    'desktop', '/login',                 'direct',      0, 0, 0, 0, 1),
    ('EVT006', '2024-05-05 11:10:00', '2024-05-05', 'CUST005', 'email_hash_sophia_005', 'SESS005', 'PROD005', 'CAMP005', 'LOC005', 'view',       'email',      'mobile',  '/products/desk-lamp',    'newsletter',  1, 0, 1, 0, 0),
]

FACT_ORDER = [
    ('ORD001', 'TXN001', '2024-05-01 09:25:00', '2024-05-01', 'CUST001', 'PROD001', 'CAMP001', 'LOC001', 'website',    'completed', 1, 1,  89.99, 10.00, 7.20, 0.00,  87.19, 'USD'),
    ('ORD002', 'TXN002', '2024-05-02 13:35:00', '2024-05-02', 'CUST002', 'PROD002', 'CAMP002', 'LOC002', 'mobile_app', 'completed', 2, 2,  49.98,  5.00, 3.60, 4.99,  53.57, 'USD'),
    ('ORD003', 'TXN003', '2024-05-07 16:20:00', '2024-05-07', 'CUST003', 'PROD003', 'CAMP003', 'LOC003', 'mobile_app', 'returned',  1, 1,  59.99,  0.00, 4.80, 0.00,  64.79, 'USD'),
    ('ORD004', 'TXN004', '2024-05-08 19:10:00', '2024-05-08', 'CUST004', 'PROD004', 'CAMP004', 'LOC004', 'website',    'completed', 1, 1, 119.99, 20.00, 8.00, 0.00, 107.99, 'USD'),
    ('ORD005', 'TXN005', '2024-05-10 12:40:00', '2024-05-10', 'CUST005', 'PROD005', 'CAMP005', 'LOC005', 'email',      'completed', 1, 1,  49.99,  5.00, 3.60, 4.99,  53.58, 'USD'),
]

FACT_CUSTOMER_METRICS_DAILY = [
    ('CUST001', '2024-05-31', 0.12,  820.50, 3,  14,  620.25, '555', 'Gold',     14,  620.25, 48, '2024-05-28', '2024-05-30'),
    ('CUST002', '2024-05-31', 0.28,  410.10, 8,   7,  315.45, '444', 'Silver',    7,  315.45, 29, '2024-05-23', '2024-05-29'),
    ('CUST003', '2024-05-31', 0.64,  155.75, 22,  3,  120.00, '222', 'Bronze',    3,  120.00, 12, '2024-05-09', '2024-05-20'),
    ('CUST004', '2024-05-31', 0.07, 1450.90, 1,  21, 1305.80, '555', 'Platinum', 21, 1305.80, 76, '2024-05-30', '2024-05-31'),
    ('CUST005', '2024-05-31', 0.18,  730.25, 5,  11,  540.60, '545', 'Gold',     11,  540.60, 41, '2024-05-26', '2024-05-30'),
]

FACT_SEGMENT_MEMBERSHIP = [
    ('CUST001', 'SEG001', 'High Value Customers', '2024-04-01', None,         True,  'CLV above 750 and recent purchase activity',     None),
    ('CUST002', 'SEG002', 'Discount Sensitive',   '2024-04-10', None,         True,  'Responded to multiple discount campaigns',       None),
    ('CUST003', 'SEG003', 'At Risk Customers',    '2024-05-01', None,         True,  'High churn score and low recent engagement',     None),
    ('CUST004', 'SEG001', 'High Value Customers', '2024-03-15', None,         True,  'Top revenue percentile and frequent purchases',  None),
    ('CUST005', 'SEG004', 'Email Engaged',        '2024-05-05', None,         True,  'Opened and clicked recent email campaigns',      None),
    ('CUST003', 'SEG004', 'Email Engaged',        '2024-04-01', '2024-05-01', False, 'Previously clicked email campaigns',             'No email clicks in last 30 days'),
]

FACT_PRICE_RESPONSE = [
    ('CUST001', 'PROD001', 79.99, '2024-05-01', 79.99,  89.99, 0.1111, -1.25, 0.72, 1.0, True,  1),
    ('CUST002', 'PROD002', 22.49, '2024-05-02', 22.49,  24.99, 0.1000, -0.85, 0.68, 2.0, True,  2),
    ('CUST003', 'PROD003', 59.99, '2024-05-03', 59.99,  59.99, 0.0000, -1.75, 0.24, 0.3, False, 0),
    ('CUST004', 'PROD004', 99.99, '2024-05-08', 99.99, 119.99, 0.1667, -1.10, 0.81, 1.0, True,  1),
    ('CUST005', 'PROD005', 44.99, '2024-05-10', 44.99,  49.99, 0.1000, -0.95, 0.59, 1.0, True,  1),
]


INSERTS = [
    ("dim_customer", """
        INSERT INTO dim_customer (
            customer_id, version_number, effective_start_date, effective_end_date, is_current,
            first_name, last_name, email_hash, phone_hash, gender, date_of_birth,
            city, state, country, postal_code,
            consent_email, consent_sms, consent_push,
            loyalty_tier
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, DIM_CUSTOMER),
    ("bridge_identity", """
        INSERT INTO bridge_identity (
            raw_id, customer_id, identity_type, source_system, first_seen_at, last_seen_at
        ) VALUES (?,?,?,?,?,?)
    """, BRIDGE_IDENTITY),
    ("dim_product", """
        INSERT INTO dim_product (
            product_id, sku, product_name, brand, category, subcategory, department,
            unit_cost, list_price, gross_margin_pct, affinity_score, is_active
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, DIM_PRODUCT),
    ("dim_campaign", """
        INSERT INTO dim_campaign (
            campaign_id, campaign_name, platform, channel, creative_id, creative_name,
            spend, start_date, end_date
        ) VALUES (?,?,?,?,?,?,?,?,?)
    """, DIM_CAMPAIGN),
    ("dim_location", """
        INSERT INTO dim_location (
            location_id, store_id, location_name, location_type,
            latitude, longitude, city, state, country, postal_code, timezone, ops_region
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, DIM_LOCATION),
    ("fact_interaction", """
        INSERT INTO fact_interaction (
            event_id, event_ts, event_date,
            customer_id, raw_id, session_id, product_id, campaign_id, location_id,
            event_type, channel, device_type, page_url, referrer_url,
            impression_count, click_count, view_count, purchase_count, login_count
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, FACT_INTERACTION),
    ("fact_order", """
        INSERT INTO fact_order (
            order_id, transaction_id, order_ts, order_date,
            customer_id, product_id, campaign_id, location_id,
            channel, order_status,
            item_count, quantity, gross_revenue, discount_amount, tax_amount,
            shipping_amount, net_revenue, currency_code
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, FACT_ORDER),
    ("fact_customer_metrics_daily", """
        INSERT INTO fact_customer_metrics_daily (
            customer_id, metric_date,
            churn_score, customer_lifetime_value,
            recency_days, frequency_count, monetary_value, rfm_score, loyalty_tier,
            total_orders, total_revenue, total_interactions,
            last_order_date, last_interaction_date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, FACT_CUSTOMER_METRICS_DAILY),
    ("fact_segment_membership", """
        INSERT INTO fact_segment_membership (
            customer_id, segment_id, segment_name,
            membership_start_date, membership_end_date, is_current_member,
            inclusion_reason, exclusion_reason
        ) VALUES (?,?,?,?,?,?,?,?)
    """, FACT_SEGMENT_MEMBERSHIP),
    ("fact_price_response", """
        INSERT INTO fact_price_response (
            customer_id, product_id, price_point, response_date,
            displayed_price, reference_price, discount_pct,
            price_elasticity, purchase_probability,
            predicted_quantity, actual_purchase_flag, actual_quantity
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, FACT_PRICE_RESPONSE),
]


def load_seed_data(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        for table, sql, rows in INSERTS:
            cur.executemany(sql, rows)
            print(f"Inserted {len(rows):>3} row(s) into {table}")
        conn.commit()

        print("\nRow counts after load:")
        for table, _sql, _rows in INSERTS:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    load_seed_data()
