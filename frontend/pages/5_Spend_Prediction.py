from __future__ import annotations

import streamlit as st

from components.protected_page import require_auth
from services.api_client import APIClientError, APIConnectionError
from services.ml_service import ml_service

user = require_auth("Bonus Prediction")

st.title("Bonus Prediction")
st.caption("דשבורד תחזיות לבעלי האתר: חיזוי הוצאה חודשית עבור משתמשים.")

st.write(f"מחובר כעת: **{user.get('username', user.get('id'))}**")

single_user_id = st.number_input("חיזוי למשתמש ספציפי (user_id)", min_value=1, value=1)

if st.button("חיזוי למשתמש בודד", type="primary"):
    try:
        result = ml_service.predict_spend_for_user(user_id=int(single_user_id))

        st.success("החיזוי הושלם בהצלחה")
        st.metric(
            label=f"Predicted spend for user {result.get('username')}",
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

st.divider()
st.subheader("חיזוי למספר משתמשים")
user_ids_input = st.text_input(
    "רשימת user_id מופרדת בפסיקים (אופציונלי)",
    placeholder="לדוגמה: 1,2,5,9",
)
limit = st.slider("אם לא הזנת user_ids, כמה משתמשים לטעון", min_value=1, max_value=200, value=20)

if st.button("הרץ תחזית מרובה"):
    try:
        user_ids = None
        if user_ids_input.strip():
            user_ids = [int(part.strip()) for part in user_ids_input.split(",") if part.strip()]

        result = ml_service.predict_spend_for_users(user_ids=user_ids, limit=limit)
        rows = result.get("predictions", [])
        if not rows:
            st.warning("לא חזרו תוצאות")
        else:
            st.dataframe(rows, use_container_width=True)
            st.caption(f"Generated at: {result.get('generated_at', '-')}")

    except ValueError:
        st.error("פורמט user_ids לא תקין. יש להזין מספרים מופרדים בפסיקים בלבד.")
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע")
    except APIClientError as e:
        st.error(f"שגיאה מהשרת: {e.detail.message}")
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")
