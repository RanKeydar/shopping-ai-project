from __future__ import annotations

from services.api_client import api


class MLService:
    def predict_spend(self, user_id: int | None = None) -> dict:
        payload = {}
        if user_id is not None:
            payload["user_id"] = int(user_id)

        return api.post("/ml/predict-spend", data=payload)


ml_service = MLService()
