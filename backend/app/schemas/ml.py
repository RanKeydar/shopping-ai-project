from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SpendPredictionRequest(BaseModel):
    user_id: int | None = Field(default=None, ge=1)


class SpendPredictionResponse(BaseModel):
    user_id: int
    predicted_spend_usd_30d: float
    model_version: str
    generated_at: datetime
