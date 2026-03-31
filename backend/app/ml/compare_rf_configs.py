from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from app.ml.dataset import MODEL_FEATURES, build_spend_dataset


def main() -> None:
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

    configs = [
        {
            "n_estimators": 50,
            "max_depth": 5,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
        },
        {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
        },
        {
            "n_estimators": 200,
            "max_depth": 10,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
        },
        {
            "n_estimators": 100,
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
        },
        {
            "n_estimators": 200,
            "max_depth": None,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
        },
        {
            "n_estimators": 300,
            "max_depth": 12,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
        },
    ]

    results: list[dict] = []

    print("\n🧠 Comparing RandomForest configs...\n")

    for i, cfg in enumerate(configs, start=1):
        model = RandomForestRegressor(
            **cfg,
            random_state=42,
            n_jobs=-1,
        )

        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))

        result = {
            "config_index": i,
            "config": cfg,
            "mae": mae,
            "rmse": rmse,
        }
        results.append(result)

        print(f"Config #{i}")
        print(f"Params: {cfg}")
        print(f"MAE   : {mae:.2f}")
        print(f"RMSE  : {rmse:.2f}")
        print("-" * 50)

    best_by_mae = min(results, key=lambda x: x["mae"])

    print("\n🏆 Best config by MAE")
    print(f"Config #{best_by_mae['config_index']}")
    print(f"Params: {best_by_mae['config']}")
    print(f"MAE   : {best_by_mae['mae']:.2f}")
    print(f"RMSE  : {best_by_mae['rmse']:.2f}")


if __name__ == "__main__":
    main()