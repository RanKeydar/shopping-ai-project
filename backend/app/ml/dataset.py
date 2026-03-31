from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from app.ml.synthetic import generate_synthetic_order_histories


DATASET_COLUMNS = [
    "user_id",
    "snapshot_index",
    "country",
    "city",
    "country_encoded",
    "geo_avg_order_total",
    "closed_orders_count_so_far",
    "avg_order_total_so_far",
    "last_order_total",
    "max_order_total_so_far",
    "min_order_total_so_far",
    "recent_avg_order_total",
    "order_total_std_so_far",
    "trend_slope",
    "last_vs_avg_ratio",
    "avg_items_per_order_so_far",
    "last_items_count",
    "max_items_per_order_so_far",
    "days_since_prev_order",
    "favorite_category_encoded",
    "recent_category_encoded",
    "category_diversity",
    "favorite_price_tier_encoded",
    "recent_price_tier_encoded",
    "target_next_order_total",
]

MODEL_FEATURES = [
    "country_encoded",
    "geo_avg_order_total",
    "closed_orders_count_so_far",
    "avg_order_total_so_far",
    "last_order_total",
    "max_order_total_so_far",
    "min_order_total_so_far",
    "recent_avg_order_total",
    "order_total_std_so_far",
    "trend_slope",
    "last_vs_avg_ratio",
    "avg_items_per_order_so_far",
    "last_items_count",
    "max_items_per_order_so_far",
    "days_since_prev_order",
    "favorite_category_encoded",
    "recent_category_encoded",
    "category_diversity",
    "favorite_price_tier_encoded",
    "recent_price_tier_encoded",
]


def _compute_trend_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0

    x = np.arange(len(values))
    y = np.array(values)

    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def _most_common(values: list[int]) -> int:
    return Counter(values).most_common(1)[0][0]


def build_spend_dataset(num_users: int = 300) -> pd.DataFrame:
    histories = generate_synthetic_order_histories(num_users=num_users)

    rows = []

    for history in histories:
        user = history["user"]
        orders = history["orders"]

        totals = [o["order_total"] for o in orders]
        items = [o["items_count"] for o in orders]
        days = [o["days_since_prev_order"] for o in orders]
        categories = [o["category_encoded"] for o in orders]
        price_tiers = [o["price_tier_encoded"] for o in orders]

        for i in range(1, len(orders)):
            history_totals = totals[:i]
            history_items = items[:i]
            history_categories = categories[:i]
            history_price_tiers = price_tiers[:i]

            target = totals[i]

            count = len(history_totals)
            avg_total = sum(history_totals) / count
            last_total = history_totals[-1]
            max_total = max(history_totals)
            min_total = min(history_totals)

            recent = history_totals[-3:]
            recent_avg = sum(recent) / len(recent)

            std = float(np.std(history_totals)) if count > 1 else 0.0
            slope = _compute_trend_slope(history_totals)
            ratio = last_total / avg_total if avg_total > 0 else 1.0

            avg_items = sum(history_items) / len(history_items)
            last_items = history_items[-1]
            max_items = max(history_items)

            days_since_prev = days[i - 1] if i > 0 else 7

            favorite_category = _most_common(history_categories)
            recent_category = history_categories[-1]
            category_diversity = len(set(history_categories))

            favorite_price_tier = _most_common(history_price_tiers)
            recent_price_tier = history_price_tiers[-1]

            row = {
                "user_id": user["user_id"],
                "snapshot_index": i,
                "country": user["country"],
                "city": user["city"],
                "country_encoded": user["country_encoded"],
                "geo_avg_order_total": user["geo_avg_order_total"],
                "closed_orders_count_so_far": count,
                "avg_order_total_so_far": avg_total,
                "last_order_total": last_total,
                "max_order_total_so_far": max_total,
                "min_order_total_so_far": min_total,
                "recent_avg_order_total": recent_avg,
                "order_total_std_so_far": std,
                "trend_slope": slope,
                "last_vs_avg_ratio": ratio,
                "avg_items_per_order_so_far": avg_items,
                "last_items_count": last_items,
                "max_items_per_order_so_far": max_items,
                "days_since_prev_order": days_since_prev,
                "favorite_category_encoded": favorite_category,
                "recent_category_encoded": recent_category,
                "category_diversity": category_diversity,
                "favorite_price_tier_encoded": favorite_price_tier,
                "recent_price_tier_encoded": recent_price_tier,
                "target_next_order_total": target,
            }

            rows.append(row)

    df = pd.DataFrame(rows, columns=DATASET_COLUMNS)
    return df