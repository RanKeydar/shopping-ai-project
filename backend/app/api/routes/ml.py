from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.current_user import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.ml import SpendPredictionRequest, SpendPredictionResponse
from app.services.ml_service import predict_user_spend_30d


router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/predict-spend", response_model=SpendPredictionResponse)
def predict_spend(
    payload: SpendPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user_id = payload.user_id or current_user.id

    if target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only predict for your own account")

    try:
        prediction, model_version = predict_user_spend_30d(db=db, user_id=target_user_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=503, detail="Prediction service unavailable")

    return SpendPredictionResponse(
        user_id=target_user_id,
        predicted_spend_usd_30d=prediction,
        model_version=model_version,
        generated_at=datetime.now(timezone.utc),
    )
