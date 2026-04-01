from __future__ import annotations

from services.api_client import api


class MLService:
    def predict_spend_for_user(self, user_id: int) -> dict:
        payload = {"user_id": int(user_id)}
        return api.post("/ml/predict-spend", data=payload)

    def predict_spend_for_users(
        self,
        user_ids: list[int] | None = None,
        limit: int = 20,
    ) -> dict:
        params = {"limit": int(limit)}
        if user_ids:
            params["user_ids"] = ",".join(str(int(user_id)) for user_id in user_ids)
        return api.get("/ml/predict-spend/users", params=params)


ml_service = MLService()
