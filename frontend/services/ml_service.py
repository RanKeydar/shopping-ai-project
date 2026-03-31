from __future__ import annotations

from typing import Any

from services.api_client import api


class MLService:
    @staticmethod
    def predict_spend(features: dict[str, float]) -> dict[str, Any]:
        return api.post(
            "/ml/predict-spend",
            data={"features": features},
        )


ml_service = MLService()