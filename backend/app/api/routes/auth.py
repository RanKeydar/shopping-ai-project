from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse
from app.core.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": str(user.id),
        "token_type": "bearer",
    }