"""Price Elasticity Sandbox + Next-Best-Offer.

A small Streamlit app over analytics.db with two tabs:

  Tab 1 — Price Elasticity Sandbox: pick a product, slide a price, see the
          demand curve, expected revenue/margin, and margin-optimal price.

  Tab 2 — Next-Best-Offer: pick a customer, get a ranked list of products
          with the optimal discount per product, scored by
          affinity_score x purchase_probability x expected_margin.

Run with:
    streamlit run price_elasticity_app.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "analytics.db"


# =========================
# Data loaders
# =========================

@st.cache_data
def load_products() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT p.product_id, p.product_name, p.brand, p.category,
                   p.unit_cost, p.list_price, p.affinity_score
            FROM dim_product p
            WHERE p.is_active = 1
            ORDER BY p.product_name
            """,
            conn,
        )


@st.cache_data
def load_price_responses(product_id: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT customer_id, price_point, response_date,
                   displayed_price, reference_price, discount_pct,
                   price_elasticity, purchase_probability,
                   predicted_quantity, actual_purchase_flag, actual_quantity
            FROM fact_price_response
            WHERE product_id = ?
            ORDER BY response_date
            """,
            conn,
            params=(product_id,),
        )


@st.cache_data
def load_all_price_responses() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT product_id,
                   AVG(reference_price)      AS reference_price,
                   AVG(price_elasticity)     AS price_elasticity,
                   AVG(purchase_probability) AS purchase_probability,
                   AVG(predicted_quantity)   AS predicted_quantity
            FROM fact_price_response
            GROUP BY product_id
            """,
            conn,
        )


@st.cache_data
def load_customers() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT customer_id, first_name, last_name, loyalty_tier, city, state
            FROM dim_customer
            WHERE is_current = 1
            ORDER BY customer_id
            """,
            conn,
        )


@st.cache_data
def load_customer_metrics(customer_id: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT customer_id, metric_date, churn_score,
                   customer_lifetime_value, recency_days, frequency_count,
                   monetary_value, rfm_score, loyalty_tier,
                   total_orders, total_revenue
            FROM fact_customer_metrics_daily
            WHERE customer_id = ?
            ORDER BY metric_date DESC
            LIMIT 1
            """,
            conn,
            params=(customer_id,),
        )


@st.cache_data
def load_customer_orders(customer_id: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT product_id, COUNT(*) AS orders, SUM(quantity) AS quantity
            FROM fact_order
            WHERE customer_id = ?
            GROUP BY product_id
            """,
            conn,
            params=(customer_id,),
        )


# =========================
# Elasticity math
# =========================

def demand_curve(
    prices: np.ndarray,
    reference_price: float,
    reference_quantity: float,
    elasticity: float,
) -> np.ndarray:
    """Constant-elasticity demand: Q(p) = Q_ref * (p / p_ref) ^ elasticity."""
    return reference_quantity * np.power(prices / reference_price, elasticity)


def probability_at_price(
    prices: np.ndarray,
    reference_price: float,
    reference_probability: float,
    elasticity: float,
) -> np.ndarray:
    scaled = reference_probability * np.power(prices / reference_price, elasticity)
    return np.clip(scaled, 0.0, 1.0)


# =========================
# Tab 1: Price Elasticity
# =========================

def render_price_elasticity_tab() -> None:
    st.caption("Pick a product, slide the price, watch the demand curve react.")

    products = load_products()
    if products.empty:
        st.error("No products found. Run create_schema.py and load_seed_data.py first.")
        return

    product_label = st.selectbox(
        "Product",
        options=products["product_id"],
        format_func=lambda pid: f"{pid} — {products.loc[products.product_id == pid, 'product_name'].iloc[0]}",
        key="elasticity_product",
    )
    product = products[products.product_id == product_label].iloc[0]
    responses = load_price_responses(product_label)

    if responses.empty:
        st.warning("No price-response data for this product.")
        return

    ref_price = float(responses["reference_price"].iloc[0])
    elasticity = float(responses["price_elasticity"].mean())
    ref_quantity = float(responses["predicted_quantity"].mean())
    ref_probability = float(responses["purchase_probability"].mean())
    unit_cost = float(product["unit_cost"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Reference price", f"${ref_price:,.2f}")
    col2.metric("Unit cost", f"${unit_cost:,.2f}")
    col3.metric("Elasticity", f"{elasticity:.2f}")

    price = st.slider(
        "Price point ($)",
        min_value=float(round(unit_cost, 2)),
        max_value=float(round(ref_price * 1.5, 2)),
        value=float(round(ref_price, 2)),
        step=0.50,
    )

    predicted_q = float(
        demand_curve(np.array([price]), ref_price, ref_quantity, elasticity)[0]
    )
    predicted_p = float(
        probability_at_price(np.array([price]), ref_price, ref_probability, elasticity)[0]
    )
    expected_revenue = predicted_p * predicted_q * price
    expected_margin = predicted_p * predicted_q * (price - unit_cost)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Purchase probability", f"{predicted_p:.1%}")
    m2.metric("Predicted quantity", f"{predicted_q:.2f}")
    m3.metric("Expected revenue / customer", f"${expected_revenue:,.2f}")
    m4.metric("Expected margin / customer", f"${expected_margin:,.2f}")

    price_grid = np.linspace(max(unit_cost, 0.01), ref_price * 1.5, 80)
    q_grid = demand_curve(price_grid, ref_price, ref_quantity, elasticity)
    p_grid = probability_at_price(price_grid, ref_price, ref_probability, elasticity)
    revenue_grid = p_grid * q_grid * price_grid
    margin_grid = p_grid * q_grid * (price_grid - unit_cost)

    curve_df = pd.DataFrame(
        {
            "price": price_grid,
            "expected_revenue": revenue_grid,
            "expected_margin": margin_grid,
        }
    ).set_index("price")

    st.subheader("Revenue and margin vs price")
    st.line_chart(curve_df)

    optimal_idx = int(np.argmax(margin_grid))
    optimal_price = float(price_grid[optimal_idx])
    st.info(
        f"Margin-optimal price (model estimate): **${optimal_price:,.2f}** "
        f"→ expected margin **${margin_grid[optimal_idx]:,.2f}** per customer."
    )

    st.subheader("Observed price-response rows")
    st.dataframe(responses, use_container_width=True)


# =========================
# Tab 2: Next-Best-Offer
# =========================

LOYALTY_BOOST = {
    "Platinum": 1.15,
    "Gold": 1.10,
    "Silver": 1.05,
    "Bronze": 1.00,
}


def score_offers(
    customer_id: str,
    customer_tier: str,
    products: pd.DataFrame,
    price_responses: pd.DataFrame,
    purchase_history: pd.DataFrame,
    discount_grid: np.ndarray,
) -> pd.DataFrame:
    """For each product, sweep discount levels and pick the one with the
    highest expected margin. Final score weights by affinity, loyalty boost,
    and a small bump if the customer has bought it before."""

    merged = products.merge(price_responses, on="product_id", how="left")
    boost = LOYALTY_BOOST.get(customer_tier, 1.0)
    bought_set = set(purchase_history["product_id"].tolist())

    rows = []
    for _, r in merged.iterrows():
        ref_price = r["reference_price"]
        elasticity = r["price_elasticity"]
        ref_q = r["predicted_quantity"]
        ref_p = r["purchase_probability"]
        unit_cost = r["unit_cost"]
        list_price = r["list_price"]
        affinity = r["affinity_score"] if pd.notna(r["affinity_score"]) else 0.5

        if pd.isna(ref_price) or pd.isna(elasticity):
            ref_price = list_price
            elasticity = -1.0
            ref_q = 1.0
            ref_p = 0.5

        prices = list_price * (1.0 - discount_grid)
        prices = np.maximum(prices, unit_cost + 0.01)

        q = demand_curve(prices, ref_price, ref_q, elasticity)
        p = probability_at_price(prices, ref_price, ref_p, elasticity)
        p_boosted = np.clip(p * boost, 0.0, 1.0)
        if r["product_id"] in bought_set:
            p_boosted = np.clip(p_boosted * 1.05, 0.0, 1.0)

        expected_margin = p_boosted * q * (prices - unit_cost)
        best_idx = int(np.argmax(expected_margin))

        rows.append(
            {
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "category": r["category"],
                "list_price": float(list_price),
                "best_discount_pct": float(discount_grid[best_idx]),
                "offer_price": float(prices[best_idx]),
                "purchase_probability": float(p_boosted[best_idx]),
                "expected_margin": float(expected_margin[best_idx]),
                "affinity_score": float(affinity),
                "score": float(affinity * p_boosted[best_idx] * expected_margin[best_idx]),
                "previously_bought": r["product_id"] in bought_set,
            }
        )

    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


def render_next_best_offer_tab() -> None:
    st.caption(
        "Pick a customer, get the top product offers ranked by "
        "affinity × purchase probability × expected margin, with the "
        "discount level optimized per product."
    )

    customers = load_customers()
    products = load_products()
    pr_summary = load_all_price_responses()

    if customers.empty or products.empty:
        st.error("Missing customer or product data. Run the loader first.")
        return

    customer_id = st.selectbox(
        "Customer",
        options=customers["customer_id"],
        format_func=lambda cid: (
            f"{cid} — "
            f"{customers.loc[customers.customer_id == cid, 'first_name'].iloc[0]} "
            f"{customers.loc[customers.customer_id == cid, 'last_name'].iloc[0]} "
            f"({customers.loc[customers.customer_id == cid, 'loyalty_tier'].iloc[0]})"
        ),
        key="nbo_customer",
    )

    customer = customers[customers.customer_id == customer_id].iloc[0]
    metrics = load_customer_metrics(customer_id)
    history = load_customer_orders(customer_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Loyalty tier", customer["loyalty_tier"] or "—")
    if not metrics.empty:
        m = metrics.iloc[0]
        c2.metric("Churn score", f"{m['churn_score']:.2f}")
        c3.metric("Lifetime value", f"${m['customer_lifetime_value']:,.0f}")
        c4.metric("RFM", str(m["rfm_score"]))
    else:
        c2.metric("Churn score", "—")
        c3.metric("Lifetime value", "—")
        c4.metric("RFM", "—")

    st.markdown("**Discount levels considered:** 0%, 5%, 10%, 15%, 20%, 25%, 30%")
    discount_grid = np.array([0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])

    top_n = st.slider("Number of offers to show", 1, len(products), min(3, len(products)))

    offers = score_offers(
        customer_id=customer_id,
        customer_tier=customer["loyalty_tier"] or "Bronze",
        products=products,
        price_responses=pr_summary,
        purchase_history=history,
        discount_grid=discount_grid,
    )

    st.subheader(f"Top {top_n} offers")
    display = offers.head(top_n).copy()
    display["best_discount_pct"] = display["best_discount_pct"].map(lambda x: f"{x:.0%}")
    display["offer_price"] = display["offer_price"].map(lambda x: f"${x:,.2f}")
    display["list_price"] = display["list_price"].map(lambda x: f"${x:,.2f}")
    display["purchase_probability"] = display["purchase_probability"].map(lambda x: f"{x:.1%}")
    display["expected_margin"] = display["expected_margin"].map(lambda x: f"${x:,.2f}")
    display["affinity_score"] = display["affinity_score"].map(lambda x: f"{x:.2f}")
    display["score"] = display["score"].map(lambda x: f"{x:.3f}")
    st.dataframe(
        display[
            [
                "product_id", "product_name", "category",
                "list_price", "best_discount_pct", "offer_price",
                "purchase_probability", "expected_margin",
                "affinity_score", "score", "previously_bought",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("Expected margin by product (at recommended discount)")
    chart_df = offers.set_index("product_name")[["expected_margin"]]
    st.bar_chart(chart_df)

    with st.expander("Full ranking and purchase history"):
        st.write("**All products, ranked:**")
        st.dataframe(offers, use_container_width=True)
        st.write("**Customer purchase history (from fact_order):**")
        if history.empty:
            st.info("No prior orders for this customer.")
        else:
            st.dataframe(history, use_container_width=True)


# =========================
# Main
# =========================

def main() -> None:
    st.set_page_config(page_title="Pricing & Offers Sandbox", layout="wide")
    st.title("Pricing & Offers Sandbox")

    tab_elasticity, tab_nbo = st.tabs(
        ["Price Elasticity", "Next-Best-Offer"]
    )
    with tab_elasticity:
        render_price_elasticity_tab()
    with tab_nbo:
        render_next_best_offer_tab()


if __name__ == "__main__":
    main()
