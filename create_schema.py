"""Create the analytics schema using Python's embedded SQL engine (sqlite3).

PostgreSQL-specific types from schema.sql are mapped to SQLite equivalents:
    BIGSERIAL  -> INTEGER PRIMARY KEY AUTOINCREMENT
    DECIMAL(p,s) -> NUMERIC
    BOOLEAN    -> INTEGER (0/1)
    TIMESTAMP  -> TEXT (ISO-8601)
    CHAR(n)    -> TEXT
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "analytics.db"

DDL_STATEMENTS = [
    # =========================
    # Dimension Tables
    # =========================
    """
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_sk INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        version_number INTEGER NOT NULL,
        effective_start_date TEXT NOT NULL,
        effective_end_date TEXT,
        is_current INTEGER DEFAULT 1,

        first_name TEXT,
        last_name TEXT,
        email_hash TEXT,
        phone_hash TEXT,
        gender TEXT,
        date_of_birth TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        postal_code TEXT,

        consent_email INTEGER,
        consent_sms INTEGER,
        consent_push INTEGER,

        loyalty_tier TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE (customer_id, version_number)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bridge_identity (
        raw_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        identity_type TEXT,
        source_system TEXT,
        first_seen_at TEXT,
        last_seen_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_product (
        product_id TEXT PRIMARY KEY,
        sku TEXT NOT NULL,
        product_name TEXT,
        brand TEXT,
        category TEXT,
        subcategory TEXT,
        department TEXT,
        unit_cost NUMERIC,
        list_price NUMERIC,
        gross_margin_pct NUMERIC,
        affinity_score NUMERIC,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_campaign (
        campaign_id TEXT PRIMARY KEY,
        campaign_name TEXT,
        platform TEXT,
        channel TEXT,
        creative_id TEXT,
        creative_name TEXT,
        spend NUMERIC,
        start_date TEXT,
        end_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_location (
        location_id TEXT PRIMARY KEY,
        store_id TEXT,
        location_name TEXT,
        location_type TEXT,
        latitude NUMERIC,
        longitude NUMERIC,
        city TEXT,
        state TEXT,
        country TEXT,
        postal_code TEXT,
        timezone TEXT,
        ops_region TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # =========================
    # Fact Tables
    # =========================
    """
    CREATE TABLE IF NOT EXISTS fact_interaction (
        event_id TEXT PRIMARY KEY,
        event_ts TEXT NOT NULL,
        event_date TEXT NOT NULL,

        customer_id TEXT,
        raw_id TEXT,
        session_id TEXT,
        product_id TEXT,
        campaign_id TEXT,
        location_id TEXT,

        event_type TEXT NOT NULL,
        channel TEXT,
        device_type TEXT,
        page_url TEXT,
        referrer_url TEXT,

        impression_count INTEGER DEFAULT 0,
        click_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        purchase_count INTEGER DEFAULT 0,
        login_count INTEGER DEFAULT 0,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
        FOREIGN KEY (campaign_id) REFERENCES dim_campaign(campaign_id),
        FOREIGN KEY (location_id) REFERENCES dim_location(location_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_order (
        order_id TEXT PRIMARY KEY,
        transaction_id TEXT,
        order_ts TEXT NOT NULL,
        order_date TEXT NOT NULL,

        customer_id TEXT,
        product_id TEXT,
        campaign_id TEXT,
        location_id TEXT,

        channel TEXT,
        order_status TEXT,

        item_count INTEGER,
        quantity INTEGER,
        gross_revenue NUMERIC,
        discount_amount NUMERIC,
        tax_amount NUMERIC,
        shipping_amount NUMERIC,
        net_revenue NUMERIC,

        currency_code TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
        FOREIGN KEY (campaign_id) REFERENCES dim_campaign(campaign_id),
        FOREIGN KEY (location_id) REFERENCES dim_location(location_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_customer_metrics_daily (
        customer_id TEXT NOT NULL,
        metric_date TEXT NOT NULL,

        churn_score NUMERIC,
        customer_lifetime_value NUMERIC,
        recency_days INTEGER,
        frequency_count INTEGER,
        monetary_value NUMERIC,
        rfm_score TEXT,
        loyalty_tier TEXT,

        total_orders INTEGER,
        total_revenue NUMERIC,
        total_interactions INTEGER,
        last_order_date TEXT,
        last_interaction_date TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        PRIMARY KEY (customer_id, metric_date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_segment_membership (
        customer_id TEXT NOT NULL,
        segment_id TEXT NOT NULL,
        segment_name TEXT,

        membership_start_date TEXT NOT NULL,
        membership_end_date TEXT,
        is_current_member INTEGER DEFAULT 1,
        inclusion_reason TEXT,
        exclusion_reason TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        PRIMARY KEY (customer_id, segment_id, membership_start_date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_price_response (
        customer_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        price_point NUMERIC NOT NULL,
        response_date TEXT NOT NULL,

        displayed_price NUMERIC,
        reference_price NUMERIC,
        discount_pct NUMERIC,

        price_elasticity NUMERIC,
        purchase_probability NUMERIC,
        predicted_quantity NUMERIC,
        actual_purchase_flag INTEGER,
        actual_quantity INTEGER,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        PRIMARY KEY (customer_id, product_id, price_point, response_date),

        FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
    )
    """,
]


def create_schema(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        for ddl in DDL_STATEMENTS:
            cur.execute(ddl)
        conn.commit()

        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cur.fetchall() if not row[0].startswith("sqlite_")]
        print(f"Created database at: {db_path}")
        print(f"Tables ({len(tables)}):")
        for t in tables:
            print(f"  - {t}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_schema()
