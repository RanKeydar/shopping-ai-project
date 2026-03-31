from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ml.predict import predict_single
from app.schemas.ml import SpendPredictionRequest, SpendPredictionResponse


router = APIRouter(prefix="/ml", tags=["ML"])


@router.post(
    "/predict-spend",
    response_model=SpendPredictionResponse,
)
def predict_spend_endpoint(
    payload: SpendPredictionRequest,
) -> SpendPredictionResponse:
    try:
        prediction = predict_single(payload.features)
        return SpendPredictionResponse(
            predicted_next_order_total=round(prediction, 2)
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        ) from exc