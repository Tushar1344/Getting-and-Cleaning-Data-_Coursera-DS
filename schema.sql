-- Generic SQL table structures based on the screenshot
-- Dialect: PostgreSQL-style SQL

-- =========================
-- Dimension Tables
-- =========================

CREATE TABLE dim_customer (
    customer_sk BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    version_number INTEGER NOT NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,

    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email_hash VARCHAR(256),
    phone_hash VARCHAR(256),
    gender VARCHAR(50),
    date_of_birth DATE,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(30),

    consent_email BOOLEAN,
    consent_sms BOOLEAN,
    consent_push BOOLEAN,

    loyalty_tier VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (customer_id, version_number)
);

CREATE TABLE bridge_identity (
    raw_id VARCHAR(256) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    identity_type VARCHAR(50),      -- email, cookie, device_id, phone, etc.
    source_system VARCHAR(100),
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_product (
    product_id VARCHAR(100) PRIMARY KEY,
    sku VARCHAR(100) NOT NULL,
    product_name VARCHAR(255),
    brand VARCHAR(100),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    department VARCHAR(100),
    unit_cost DECIMAL(12, 2),
    list_price DECIMAL(12, 2),
    gross_margin_pct DECIMAL(8, 4),
    affinity_score DECIMAL(10, 4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_campaign (
    campaign_id VARCHAR(100) PRIMARY KEY,
    campaign_name VARCHAR(255),
    platform VARCHAR(100),
    channel VARCHAR(100),
    creative_id VARCHAR(100),
    creative_name VARCHAR(255),
    spend DECIMAL(14, 2),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_location (
    location_id VARCHAR(100) PRIMARY KEY,
    store_id VARCHAR(100),
    location_name VARCHAR(255),
    location_type VARCHAR(100),     -- store, warehouse, region, geo, etc.
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(30),
    timezone VARCHAR(100),
    ops_region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- Fact Tables
-- =========================

CREATE TABLE fact_interaction (
    event_id VARCHAR(100) PRIMARY KEY,
    event_ts TIMESTAMP NOT NULL,
    event_date DATE NOT NULL,

    customer_id VARCHAR(100),
    raw_id VARCHAR(256),
    session_id VARCHAR(100),
    product_id VARCHAR(100),
    campaign_id VARCHAR(100),
    location_id VARCHAR(100),

    event_type VARCHAR(50) NOT NULL, -- click, view, purchase, impression, login
    channel VARCHAR(100),
    device_type VARCHAR(100),
    page_url TEXT,
    referrer_url TEXT,

    impression_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    purchase_count INTEGER DEFAULT 0,
    login_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
    FOREIGN KEY (campaign_id) REFERENCES dim_campaign(campaign_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id)
);

CREATE TABLE fact_order (
    order_id VARCHAR(100) PRIMARY KEY,
    transaction_id VARCHAR(100),
    order_ts TIMESTAMP NOT NULL,
    order_date DATE NOT NULL,

    customer_id VARCHAR(100),
    product_id VARCHAR(100),
    campaign_id VARCHAR(100),
    location_id VARCHAR(100),

    channel VARCHAR(100),
    order_status VARCHAR(50),

    item_count INTEGER,
    quantity INTEGER,
    gross_revenue DECIMAL(14, 2),
    discount_amount DECIMAL(14, 2),
    tax_amount DECIMAL(14, 2),
    shipping_amount DECIMAL(14, 2),
    net_revenue DECIMAL(14, 2),

    currency_code CHAR(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
    FOREIGN KEY (campaign_id) REFERENCES dim_campaign(campaign_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id)
);

CREATE TABLE fact_customer_metrics_daily (
    customer_id VARCHAR(100) NOT NULL,
    metric_date DATE NOT NULL,

    churn_score DECIMAL(10, 4),
    customer_lifetime_value DECIMAL(14, 2),
    recency_days INTEGER,
    frequency_count INTEGER,
    monetary_value DECIMAL(14, 2),
    rfm_score VARCHAR(20),
    loyalty_tier VARCHAR(50),

    total_orders INTEGER,
    total_revenue DECIMAL(14, 2),
    total_interactions INTEGER,
    last_order_date DATE,
    last_interaction_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (customer_id, metric_date)
);

CREATE TABLE fact_segment_membership (
    customer_id VARCHAR(100) NOT NULL,
    segment_id VARCHAR(100) NOT NULL,
    segment_name VARCHAR(255),

    membership_start_date DATE NOT NULL,
    membership_end_date DATE,
    is_current_member BOOLEAN DEFAULT TRUE,
    inclusion_reason TEXT,
    exclusion_reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (customer_id, segment_id, membership_start_date)
);

CREATE TABLE fact_price_response (
    customer_id VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    price_point DECIMAL(12, 2) NOT NULL,
    response_date DATE NOT NULL,

    displayed_price DECIMAL(12, 2),
    reference_price DECIMAL(12, 2),
    discount_pct DECIMAL(8, 4),

    price_elasticity DECIMAL(10, 4),
    purchase_probability DECIMAL(10, 4),
    predicted_quantity DECIMAL(12, 4),
    actual_purchase_flag BOOLEAN,
    actual_quantity INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (customer_id, product_id, price_point, response_date),

    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
);
