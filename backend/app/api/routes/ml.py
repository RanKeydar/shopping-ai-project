from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.current_user import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models import User
from app.schemas.ml import (
    SpendPredictionRequest,
    SpendPredictionResponse,
    UserSpendPredictionRow,
    UsersSpendPredictionResponse,
)
from app.services.ml_service import predict_user_spend_30d


router = APIRouter(prefix="/ml", tags=["ml"])


def _require_site_owner(current_user: User) -> None:
    if current_user.username.lower() not in settings.site_owner_usernames:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is available only to site owners",
        )


@router.post("/predict-spend", response_model=SpendPredictionResponse)
def predict_spend(
    payload: SpendPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_site_owner(current_user)

    try:
        target_user = db.execute(
            select(User).where(User.id == payload.user_id)
        ).scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        prediction, model_version = predict_user_spend_30d(db=db, user_id=target_user.id)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=503, detail="Prediction service unavailable")

    return SpendPredictionResponse(
        user_id=target_user.id,
        username=target_user.username,
        predicted_spend_usd_30d=prediction,
        model_version=model_version,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/predict-spend/users", response_model=UsersSpendPredictionResponse)
def predict_spend_for_users(
    user_ids: str | None = Query(default=None, description="Comma-separated user IDs"),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_site_owner(current_user)

    query = select(User)
    if user_ids:
        parsed_ids = [int(value.strip()) for value in user_ids.split(",") if value.strip()]
        if not parsed_ids:
            raise HTTPException(status_code=400, detail="user_ids must contain valid integers")
        query = query.where(User.id.in_(parsed_ids))
    else:
        query = query.limit(limit)

    users = db.execute(query).scalars().all()
    if not users:
        raise HTTPException(status_code=404, detail="No matching users found")

    rows: list[UserSpendPredictionRow] = []
    try:
        for user in users:
            prediction, model_version = predict_user_spend_30d(db=db, user_id=user.id)
            rows.append(
                UserSpendPredictionRow(
                    user_id=user.id,
                    username=user.username,
                    predicted_spend_usd_30d=prediction,
                    model_version=model_version,
                )
            )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=503, detail="Prediction service unavailable")

    return UsersSpendPredictionResponse(
        generated_at=datetime.now(timezone.utc),
        predictions=rows,
    )
