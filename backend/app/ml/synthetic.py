from __future__ import annotations

import random
from typing import Any


GEO_STRUCTURE = {
    "Israel": ["Tel Aviv", "Jerusalem", "Haifa", "Petah Tikva"],
    "USA": ["New York", "Austin", "Miami", "Chicago"],
    "UK": ["London", "Manchester", "Leeds"],
}

COUNTRY_BASE_SPEND = {
    "Israel": 80.0,
    "USA": 120.0,
    "UK": 100.0,
}

COUNTRY_ENCODING = {
    "Israel": 0,
    "USA": 1,
    "UK": 2,
}

SPEND_LEVEL_MULTIPLIER = {
    "low": 0.6,
    "medium": 1.0,
    "high": 1.8,
}

TREND_TYPES = ["increasing", "decreasing", "stable", "volatile"]
SPEND_LEVELS = ["low", "medium", "high"]

CATEGORIES = ["groceries", "electronics", "furniture", "beauty"]
CATEGORY_ENCODING = {
    "groceries": 0,
    "electronics": 1,
    "furniture": 2,
    "beauty": 3,
}

PRICE_TIERS = ["budget", "regular", "premium"]
PRICE_TIER_ENCODING = {
    "budget": 0,
    "regular": 1,
    "premium": 2,
}
PRICE_TIER_MULTIPLIER = {
    "budget": 0.8,
    "regular": 1.0,
    "premium": 1.35,
}


def _clamp(value: float, min_value: float = 5.0) -> float:
    return max(value, min_value)


def _round_money(value: float) -> float:
    return round(value, 2)


def generate_synthetic_users(num_users: int = 300, seed: int = 42) -> list[dict[str, Any]]:
    random.seed(seed)

    users: list[dict[str, Any]] = []

    for user_id in range(1, num_users + 1):
        country = random.choice(list(GEO_STRUCTURE.keys()))
        city = random.choice(GEO_STRUCTURE[country])

        spend_level = random.choices(
            population=SPEND_LEVELS,
            weights=[0.35, 0.45, 0.20],
            k=1,
        )[0]

        trend_type = random.choice(TREND_TYPES)
        num_orders = random.randint(4, 8)

        city_factor = round(random.uniform(0.9, 1.1), 3)
        geo_avg_order_total = _round_money(COUNTRY_BASE_SPEND[country] * city_factor)

        main_category = random.choices(
            population=CATEGORIES,
            weights=[0.40, 0.20, 0.20, 0.20],
            k=1,
        )[0]

        preferred_price_tier = random.choices(
            population=PRICE_TIERS,
            weights=[0.35, 0.45, 0.20],
            k=1,
        )[0]

        users.append(
            {
                "user_id": user_id,
                "country": country,
                "city": city,
                "country_encoded": COUNTRY_ENCODING[country],
                "spend_level": spend_level,
                "trend_type": trend_type,
                "num_orders": num_orders,
                "city_factor": city_factor,
                "geo_avg_order_total": geo_avg_order_total,
                "main_category": main_category,
                "preferred_price_tier": preferred_price_tier,
            }
        )

    return users


def generate_user_order_history(user: dict[str, Any]) -> list[dict[str, Any]]:
    base_amount = (
        COUNTRY_BASE_SPEND[user["country"]]
        * SPEND_LEVEL_MULTIPLIER[user["spend_level"]]
        * user["city_factor"]
    )

    num_orders = user["num_orders"]
    trend_type = user["trend_type"]

    orders: list[dict[str, Any]] = []

    for order_index in range(num_orders):
        if trend_type == "increasing":
            trend_effect = order_index * random.uniform(6.0, 14.0)
            noise = random.uniform(-8.0, 8.0)
        elif trend_type == "decreasing":
            trend_effect = -(order_index * random.uniform(6.0, 14.0))
            noise = random.uniform(-8.0, 8.0)
        elif trend_type == "stable":
            trend_effect = 0.0
            noise = random.uniform(-10.0, 10.0)
        else:  # volatile
            direction = random.choice([-1, 1])
            trend_effect = direction * random.uniform(0.0, 25.0)
            noise = random.uniform(-25.0, 25.0)

        category = random.choices(
            population=[user["main_category"], random.choice(CATEGORIES)],
            weights=[0.7, 0.3],
            k=1,
        )[0]

        price_tier = random.choices(
            population=[user["preferred_price_tier"], random.choice(PRICE_TIERS)],
            weights=[0.75, 0.25],
            k=1,
        )[0]

        category_multiplier = {
            "groceries": 0.75,
            "electronics": 1.35,
            "furniture": 1.55,
            "beauty": 0.95,
        }[category]

        tier_multiplier = PRICE_TIER_MULTIPLIER[price_tier]

        total = _clamp(
            (base_amount * category_multiplier * tier_multiplier) + trend_effect + noise,
            min_value=5.0,
        )
        total = _round_money(total)

        estimated_items = max(1, int(round(total / random.uniform(18.0, 35.0))))
        days_since_prev_order = random.randint(5, 30)

        orders.append(
            {
                "order_index": order_index + 1,
                "order_total": total,
                "items_count": estimated_items,
                "days_since_prev_order": days_since_prev_order,
                "category": category,
                "category_encoded": CATEGORY_ENCODING[category],
                "price_tier": price_tier,
                "price_tier_encoded": PRICE_TIER_ENCODING[price_tier],
            }
        )

    return orders


def generate_synthetic_order_histories(
    num_users: int = 300,
    seed: int = 42,
) -> list[dict[str, Any]]:
    users = generate_synthetic_users(num_users=num_users, seed=seed)

    histories: list[dict[str, Any]] = []

    for user in users:
        orders = generate_user_order_history(user)

        histories.append(
            {
                "user": user,
                "orders": orders,
            }
        )

    return histories