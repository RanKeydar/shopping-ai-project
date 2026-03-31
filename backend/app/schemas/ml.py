from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Field


class SpendPredictionRequest(BaseModel):
    features: Dict[str, float] = Field(
        ...,
        description="Feature values for spend prediction",
    )


class SpendPredictionResponse(BaseModel):
    predicted_next_order_total: float