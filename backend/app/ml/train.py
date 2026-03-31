from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "data" / "user_spend_training.csv"
MODEL_PATH = BASE_DIR / "model.joblib"
METADATA_PATH = BASE_DIR / "metadata.json"

FEATURES = [
    "orders_count_90d",
    "closed_orders_count_90d",
    "avg_order_value_90d",
    "max_order_value_90d",
    "items_bought_90d",
    "days_since_last_order",
    "favorites_count",
]
TARGET = "spend_next_30d"


def main() -> None:
    df = pd.read_csv(DATASET_PATH)

    missing = [column for column in FEATURES + [TARGET] if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    x = df[FEATURES]
    y = df[TARGET]

    x_train, x_val, y_train, y_val = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
    )

    baseline = DummyRegressor(strategy="median")
    baseline.fit(x_train, y_train)
    baseline_pred = baseline.predict(x_val)

    model = RandomForestRegressor(
        n_estimators=220,
        max_depth=10,
        random_state=42,
    )
    model.fit(x_train, y_train)
    pred = model.predict(x_val)

    metrics = {
        "baseline": {
            "mae": round(float(mean_absolute_error(y_val, baseline_pred)), 4),
            "rmse": round(float(mean_squared_error(y_val, baseline_pred) ** 0.5), 4),
            "r2": round(float(r2_score(y_val, baseline_pred)), 4),
        },
        "model": {
            "mae": round(float(mean_absolute_error(y_val, pred)), 4),
            "rmse": round(float(mean_squared_error(y_val, pred) ** 0.5), 4),
            "r2": round(float(r2_score(y_val, pred)), 4),
        },
    }

    joblib.dump(model, MODEL_PATH)

    metadata = {
        "model_version": "v1",
        "features": FEATURES,
        "target": TARGET,
        "metrics": metrics,
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metadata to: {METADATA_PATH}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
