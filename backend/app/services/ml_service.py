from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Favorite
from app.models.enums import OrderStatus
from app.repositories.orders_repository import list_orders_by_user
from app.services.ml_interpretation import (
    build_segment,
    build_confidence,
    build_reasons,
    build_recommended_action,
)

BASE_DIR = Path(__file__).resolve().parents[1] / "ml"
MODEL_PATH = BASE_DIR / "model.joblib"
METADATA_PATH = BASE_DIR / "metadata.json"

_FEATURES: list[str] | None = None
_MODEL = None
_MODEL_VERSION = "v1"


def _load_artifacts() -> tuple[object, list[str], str]:
    global _MODEL, _FEATURES, _MODEL_VERSION

    if _MODEL is not None and _FEATURES is not None:
        return _MODEL, _FEATURES, _MODEL_VERSION

    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise RuntimeError("ML model artifacts were not found. Run: python backend/app/ml/train.py")

    _MODEL = joblib.load(MODEL_PATH)

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    _FEATURES = list(metadata.get("features") or [])
    _MODEL_VERSION = str(metadata.get("model_version") or "v1")

    if not _FEATURES:
        raise RuntimeError("Invalid ML metadata: missing features list")

    return _MODEL, _FEATURES, _MODEL_VERSION


def _build_user_feature_row(db: Session, user_id: int) -> dict[str, float]:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=90)

    orders = list_orders_by_user(db, user_id)

    recent_orders = [
        order
        for order in orders
        if order.created_at.replace(tzinfo=timezone.utc) >= window_start
    ]

    recent_closed = [
        order for order in recent_orders if order.status == OrderStatus.CLOSE
    ]

    order_totals = [float(order.total_price) for order in recent_closed]

    items_bought = 0
    for order in recent_closed:
        for row in order.items:
            items_bought += int(row.quantity)

    days_since_last_order = 120
    if orders:
        latest = max(order.created_at for order in orders)
        latest_utc = latest.replace(tzinfo=timezone.utc)
        days_since_last_order = max(0, (now - latest_utc).days)

    favorites_count = db.execute(
        select(Favorite).where(Favorite.user_id == user_id)
    ).scalars().all()

    return {
        "orders_count_90d": float(len(recent_orders)),
        "closed_orders_count_90d": float(len(recent_closed)),
        "avg_order_value_90d": float(sum(order_totals) / len(order_totals)) if order_totals else 0.0,
        "max_order_value_90d": float(max(order_totals)) if order_totals else 0.0,
        "items_bought_90d": float(items_bought),
        "days_since_last_order": float(days_since_last_order),
        "favorites_count": float(len(favorites_count)),
    }


def predict_user_spend_30d(db: Session, user_id: int) -> tuple[float, str]:
    model, features, model_version = _load_artifacts()
    feature_row = _build_user_feature_row(db, user_id)

    row = {feature: feature_row.get(feature, 0.0) for feature in features}
    x = pd.DataFrame([row], columns=features)

    prediction = float(model.predict(x)[0])
    prediction = round(max(0.0, prediction), 2)

    segment = build_segment(
        prediction,
        feature_row["days_since_last_order"],
    )

    confidence = build_confidence(
        feature_row["closed_orders_count_90d"],
    )

    reasons = build_reasons(feature_row)

    action = build_recommended_action(segment)

    return {
        "prediction": prediction,
        "model_version": model_version,
        "segment": segment,
        "confidence": confidence,
        "reasons": reasons,
        "recommended_action": action,
        "features": feature_row,
    }