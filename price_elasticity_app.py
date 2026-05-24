"""Price Elasticity Sandbox.

A small Streamlit app over analytics.db. Pick a product, slide a price, and see:
  - predicted demand curve (constant-elasticity model anchored at reference price)
  - purchase probability and expected revenue per customer
  - actual observed purchases from fact_price_response for backtest

Run with:
    streamlit run price_elasticity_app.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "analytics.db"


@st.cache_data
def load_products() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT p.product_id, p.product_name, p.brand, p.category,
                   p.unit_cost, p.list_price
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
    """Same shape as demand curve, clipped to [0, 1]."""
    scaled = reference_probability * np.power(prices / reference_price, elasticity)
    return np.clip(scaled, 0.0, 1.0)


def main() -> None:
    st.set_page_config(page_title="Price Elasticity Sandbox", layout="wide")
    st.title("Price Elasticity Sandbox")
    st.caption("Pick a product, slide the price, watch the demand curve react.")

    products = load_products()
    if products.empty:
        st.error("No products found. Run create_schema.py and load_seed_data.py first.")
        return

    product_label = st.selectbox(
        "Product",
        options=products["product_id"],
        format_func=lambda pid: f"{pid} — {products.loc[products.product_id == pid, 'product_name'].iloc[0]}",
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


if __name__ == "__main__":
    main()
