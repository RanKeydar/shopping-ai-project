from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from app.ml.dataset import MODEL_FEATURES, build_spend_dataset


MODEL_PATH = Path("app/ml/models/spend_model.pkl")


def train_model() -> None:
    print("📦 Building dataset...")
    df = build_spend_dataset(num_users=300)

    X = df[MODEL_FEATURES]
    y = df["target_next_order_total"]

    print(f"Dataset shape: {df.shape}")
    print(f"Unique users: {df['user_id'].nunique()}")
    print(f"Features: {len(MODEL_FEATURES)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    print("🪨 Training baseline...")
    baseline = DummyRegressor(strategy="mean")
    baseline.fit(X_train, y_train)
    baseline_pred = baseline.predict(X_test)

    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))

    print("🧠 Training GradientBoosting model...")
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=2,
        random_state=42,
    )
    model.fit(X_train, y_train)

    print("📊 Evaluating...")
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print("\n=== Metrics ===")
    print(f"Baseline MAE   : {baseline_mae:.2f}")
    print(f"Baseline RMSE  : {baseline_rmse:.2f}")
    print(f"Model MAE      : {mae:.2f}")
    print(f"Model RMSE     : {rmse:.2f}")
    print(f"MAE improvement: {baseline_mae - mae:.2f}")
    print(f"RMSE improve.  : {baseline_rmse - rmse:.2f}")

    print("\n=== Top Feature Importances ===")
    feature_importances = sorted(
        zip(MODEL_FEATURES, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )

    for feature_name, importance in feature_importances[:10]:
        print(f"{feature_name:<35} {importance:.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"\n💾 Model saved to: {MODEL_PATH}")

    print("\n🔮 Sample prediction:")
    sample_row = X_test.iloc[[0]]
    actual = y_test.iloc[0]
    predicted = model.predict(sample_row)[0]
    baseline_value = baseline.predict(sample_row)[0]

    print(f"Actual      : {actual:.2f}")
    print(f"Predicted   : {predicted:.2f}")
    print(f"Baseline    : {baseline_value:.2f}")


if __name__ == "__main__":
    train_model()