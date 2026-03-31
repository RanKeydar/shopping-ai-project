from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from app.ml.dataset import MODEL_FEATURES


MODEL_PATH = Path("app/ml/models/spend_model.pkl")


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}. Train the model first."
        )
    return joblib.load(MODEL_PATH)


def validate_features(df: pd.DataFrame) -> pd.DataFrame:
    missing_features = [feature for feature in MODEL_FEATURES if feature not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required features: {missing_features}")

    return df[MODEL_FEATURES].copy()


def predict_spend(features_df: pd.DataFrame) -> list[float]:
    model = load_model()
    X = validate_features(features_df)
    predictions = model.predict(X)
    return [float(pred) for pred in predictions]


def predict_single(feature_row: dict) -> float:
    features_df = pd.DataFrame([feature_row])
    prediction = predict_spend(features_df)[0]
    return float(prediction)