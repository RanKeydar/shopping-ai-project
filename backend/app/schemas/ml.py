from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SpendPredictionRequest(BaseModel):
    user_id: int = Field(ge=1)


class SpendPredictionResponse(BaseModel):
    user_id: int
    username: str
    predicted_spend_usd_30d: float
    model_version: str
    generated_at: datetime


class UserSpendPredictionRow(BaseModel):
    user_id: int
    username: str
    predicted_spend_usd_30d: float
    model_version: str


class UsersSpendPredictionResponse(BaseModel):
    generated_at: datetime
    predictions: list[UserSpendPredictionRow]
