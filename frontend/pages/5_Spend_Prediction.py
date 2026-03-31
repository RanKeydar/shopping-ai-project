from __future__ import annotations

import streamlit as st

from services.ml_service import ml_service

st.set_page_config(page_title="Spend Prediction", page_icon="💸", layout="centered")

st.title("💸 Spend Prediction")
st.caption("Predict the user's next order total using the trained ML model.")

DEFAULT_VALUES = {
    "recent_avg_order_total": 120.0,
    "avg_order_total_so_far": 110.0,
    "last_order_total": 130.0,
    "min_order_total_so_far": 80.0,
    "avg_items_per_order_so_far": 4.0,
    "trend_slope": 3.0,
    "days_since_prev_order": 10.0,
    "last_vs_avg_ratio": 1.10,
    "max_order_total_so_far": 160.0,
    "geo_avg_order_total": 100.0,
    "country_encoded": 0.0,
    "category_diversity": 2.0,
    "favorite_category_encoded": 1.0,
    "recent_category_encoded": 1.0,
    "favorite_price_tier_encoded": 2.0,
    "recent_price_tier_encoded": 2.0,
    "closed_orders_count_so_far": 5.0,
    "order_total_std_so_far": 20.0,
    "last_items_count": 4.0,
    "max_items_per_order_so_far": 7.0,
}


def build_features_form() -> dict[str, float]:
    with st.form("spend_prediction_form"):
        st.subheader("Input Features")

        features: dict[str, float] = {}

        for feature_name, default_value in DEFAULT_VALUES.items():
            features[feature_name] = st.number_input(
                label=feature_name,
                value=float(default_value),
                step=1.0 if feature_name.endswith("_encoded") or "count" in feature_name else 0.1,
                format="%.2f",
            )

        submitted = st.form_submit_button("Predict next order total")

    if submitted:
        return features

    return {}


features = build_features_form()

if features:
    try:
        result = ml_service.predict_spend(features)
        prediction = result["predicted_next_order_total"]

        st.success("Prediction completed successfully.")
        st.metric("Predicted next order total", f"${prediction:,.2f}")

        with st.expander("Submitted features"):
            st.json(features)

        with st.expander("Raw API response"):
            st.json(result)

    except Exception as exc:
        st.error(f"Prediction failed: {exc}")
