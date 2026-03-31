from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
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

    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }

    results: list[dict] = []

    print("\n🧠 Comparing models...\n")

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))

        results.append(
            {
                "name": name,
                "mae": mae,
                "rmse": rmse,
            }
        )

        print(f"{name}")
        print(f"MAE  : {mae:.2f}")
        print(f"RMSE : {rmse:.2f}")
        print("-" * 40)

    best_model = min(results, key=lambda x: x["mae"])

    print("\n🏆 Best model by MAE")
    print(f"Model: {best_model['name']}")
    print(f"MAE  : {best_model['mae']:.2f}")
    print(f"RMSE : {best_model['rmse']:.2f}")


if __name__ == "__main__":
    main()