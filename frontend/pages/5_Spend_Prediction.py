from __future__ import annotations

import streamlit as st

from components.protected_page import require_auth
from services.api_client import APIClientError, APIConnectionError
from services.ml_service import ml_service

user = require_auth("Bonus Prediction")

st.title("Bonus Prediction")
st.caption("חיזוי סכום רכישה לחודש הקרוב לפי פעילות המשתמש.")

st.write(f"משתמש נוכחי: **{user.get('username', user.get('id'))}**")

col1, col2 = st.columns([2, 1])
with col1:
    use_custom = st.checkbox("חיזוי לפי user_id ידני")
with col2:
    manual_user_id = st.number_input("user_id", min_value=1, value=int(user["id"]))

if st.button("Predict spend", type="primary"):
    try:
        target_user_id = int(manual_user_id) if use_custom else None
        result = ml_service.predict_spend(user_id=target_user_id)

        st.success("החיזוי הושלם בהצלחה")
        st.metric(
            label="Predicted spend (next 30 days)",
            value=f"${float(result.get('predicted_spend_usd_30d', 0.0)):.2f}",
        )
        st.caption(f"Model version: {result.get('model_version', 'unknown')}")
        st.caption(f"Generated at: {result.get('generated_at', '-')}")

    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע")
    except APIClientError as e:
        st.error(f"שגיאה מהשרת: {e.detail.message}")
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")