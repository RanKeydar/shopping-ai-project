from __future__ import annotations

import pandas as pd
import streamlit as st

from components.protected_page import require_auth
from services.api_client import APIClientError, APIConnectionError
from services.ml_service import ml_service


SEGMENT_LABELS = {
    "high_value": "ערך גבוה",
    "medium_value": "ערך בינוני",
    "low_value": "ערך נמוך",
    "at_risk": "בסיכון",
}

CONFIDENCE_LABELS = {
    "high": "גבוהה",
    "medium": "בינונית",
    "low": "נמוכה",
}

REASONS_LABELS = {
    "multiple recent purchases": "רכישות רבות לאחרונה",
    "high average order value": "סכום הזמנה ממוצע גבוה",
    "recent activity": "פעילות לאחרונה",
    "no recent activity": "אין פעילות לאחרונה",
    "many favorite items": "הרבה פריטים במועדפים",
}

ACTION_LABELS = {
    "offer premium products or bundles": "הצג מוצרים פרימיום או חבילות",
    "standard recommendations and cross-sell": "המלצות רגילות ומכירה משלימה",
    "highlight cheaper options or discounts": "הצג מוצרים זולים או הנחות",
    "send retention offer or promotion": "שלח הצעת שימור או מבצע",
    "monitor": "מעקב בלבד",
}


def format_segment(value: str | None) -> str:
    if not value:
        return "-"
    return SEGMENT_LABELS.get(value, value)


def format_confidence(value: str | None) -> str:
    if not value:
        return "-"
    return CONFIDENCE_LABELS.get(value, value)


def format_reason(reason: str) -> str:
    return REASONS_LABELS.get(reason, reason)


def format_action(action: str | None) -> str:
    if not action:
        return "-"
    return ACTION_LABELS.get(action, action)


user = require_auth("Spend Prediction")

st.title("חיזוי הוצאה למשתמשים")
st.caption("דשבורד תחזיות לבעלי האתר: חיזוי הוצאה חודשית עבור משתמשים.")

st.write(f"מחובר כעת: **{user.get('username', user.get('id'))}**")

single_user_id = st.number_input(
    "חיזוי למשתמש ספציפי (user_id)",
    min_value=1,
    value=1,
)

if st.button("חיזוי למשתמש בודד", type="primary"):
    try:
        result = ml_service.predict_spend_for_user(user_id=int(single_user_id))

        st.success("החיזוי הושלם בהצלחה")

        st.metric(
            label=f"תחזית הוצאה עבור המשתמש {result.get('username')}",
            value=f"${float(result.get('predicted_spend_usd_30d', 0.0)):.2f}",
        )

        st.markdown(f"**סגמנט:** {format_segment(result.get('segment'))}")
        st.markdown(f"**רמת ביטחון:** {format_confidence(result.get('confidence'))}")

        st.subheader("למה?")
        for reason in result.get("top_reasons", []):
            st.write(f"- {format_reason(reason)}")

        st.subheader("המלצה לפעולה")
        st.info(format_action(result.get("recommended_action")))

        st.caption(f"גרסת מודל: {result.get('model_version', 'unknown')}")
        st.caption(f"נוצר בתאריך: {result.get('generated_at', '-')}")

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

limit = st.slider(
    "אם לא הזנת user_ids, כמה משתמשים לטעון",
    min_value=1,
    max_value=200,
    value=20,
)

if st.button("הרץ תחזית מרובה"):
    try:
        user_ids = None
        if user_ids_input.strip():
            user_ids = [
                int(part.strip())
                for part in user_ids_input.split(",")
                if part.strip()
            ]

        result = ml_service.predict_spend_for_users(user_ids=user_ids, limit=limit)
        rows = result.get("predictions", [])

        if not rows:
            st.warning("לא חזרו תוצאות")
        else:
            df = pd.DataFrame(rows)

            if "predicted_spend_usd_30d" in df.columns:
                df = df.sort_values(
                    by="predicted_spend_usd_30d",
                    ascending=False,
                )

            if "segment" in df.columns:
                df["segment_display"] = df["segment"].apply(format_segment)

            if "confidence" in df.columns:
                df["confidence_display"] = df["confidence"].apply(format_confidence)

            display_cols = [
                "user_id",
                "username",
                "predicted_spend_usd_30d",
                "segment_display",
                "confidence_display",
            ]
            display_cols = [col for col in display_cols if col in df.columns]

            df_display = df[display_cols].rename(
                columns={
                    "user_id": "מזהה משתמש",
                    "username": "שם משתמש",
                    "predicted_spend_usd_30d": "תחזית הוצאה חודשית",
                    "segment_display": "סגמנט",
                    "confidence_display": "רמת ביטחון",
                }
            )

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            st.subheader("פירוט למשתמש נבחר")

            selected_user_id = st.selectbox(
                "בחר משתמש",
                df["user_id"].tolist(),
            )

            selected_row = df[df["user_id"] == selected_user_id].iloc[0]

            st.write(f"**שם משתמש:** {selected_row.get('username', '-')}")
            st.write(
                f"**תחזית הוצאה:** "
                f"${float(selected_row.get('predicted_spend_usd_30d', 0.0)):.2f}"
            )
            st.write(f"**סגמנט:** {format_segment(selected_row.get('segment'))}")
            st.write(f"**רמת ביטחון:** {format_confidence(selected_row.get('confidence'))}")

            st.subheader("למה?")
            for reason in selected_row.get("top_reasons", []):
                st.write(f"- {format_reason(reason)}")

            st.subheader("המלצה לפעולה")
            st.info(format_action(selected_row.get("recommended_action")))

            st.caption(f"נוצר בתאריך: {result.get('generated_at', '-')}")

    except ValueError:
        st.error("פורמט user_ids לא תקין. יש להזין מספרים מופרדים בפסיקים בלבד.")
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע")
    except APIClientError as e:
        st.error(f"שגיאה מהשרת: {e.detail.message}")
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")