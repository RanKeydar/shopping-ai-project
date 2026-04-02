from __future__ import annotations

def build_segment(prediction: float, days_since_last_order: float) -> str:
    if days_since_last_order > 60:
        return "at_risk"

    if prediction >= 100:
        return "high_value"
    elif prediction >= 40:
        return "medium_value"
    else:
        return "low_value"


def build_confidence(closed_orders_90d: float) -> str:
    if closed_orders_90d >= 5:
        return "high"
    elif closed_orders_90d >= 2:
        return "medium"
    return "low"


def build_reasons(features: dict[str, float]) -> list[str]:
    reasons: list[str] = []

    if features["closed_orders_count_90d"] >= 3:
        reasons.append("multiple recent purchases")

    if features["avg_order_value_90d"] > 40:
        reasons.append("high average order value")

    if features["days_since_last_order"] < 14:
        reasons.append("recent activity")

    if features["days_since_last_order"] > 45:
        reasons.append("no recent activity")

    if features["favorites_count"] >= 5:
        reasons.append("many favorite items")

    return reasons[:3]


def build_recommended_action(segment: str) -> str:
    return {
        "high_value": "offer premium products or bundles",
        "medium_value": "standard recommendations and cross-sell",
        "low_value": "highlight cheaper options or discounts",
        "at_risk": "send retention offer or promotion",
    }.get(segment, "monitor")