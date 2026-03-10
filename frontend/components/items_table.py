import pandas as pd
import streamlit as st
from typing import Any, Dict, List


def render_items_table(items: List[Dict[str, Any]]) -> None:
    if not items:
        st.warning("לא נמצאו פריטים מתאימים.")
        return

    df = pd.DataFrame(
        [
            {
                "Item ID": item.get("id"),
                "Item name": item.get("name"),
                "Price in USD": item.get("price_usd"),
                "In stock": item.get("stock_qty"),
            }
            for item in items
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )