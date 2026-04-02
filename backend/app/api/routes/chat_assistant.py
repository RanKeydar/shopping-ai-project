from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps.current_user import get_current_user_optional
from app.db import get_db
from app.models import User
from app.schemas.chat import ChatRequest
from app.services.chat_rate_limit_service import (
    consume_prompt,
    get_remaining_prompts,
)
from app.services.chat_service import generate_ai_answer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat-assistant", tags=["chat-assistant"])


def get_chat_identifier(request: Request, current_user: Optional[User]) -> str:
    if current_user is not None:
        return f"user:{current_user.id}"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        return f"guest:{ip}"

    client_host = request.client.host if request.client else "unknown"
    return f"guest:{client_host}"


@router.get("/remaining")
async def get_chat_remaining(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    identifier = get_chat_identifier(request, current_user)
    remaining = await get_remaining_prompts(identifier)

    return {
        "remaining_prompts": remaining,
    }


@router.post("")
async def chat_with_assistant(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    identifier = get_chat_identifier(request, current_user)

    try:
        prompt = payload.prompt.strip()

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt must not be empty.")

        remaining_before = await get_remaining_prompts(identifier)
        if remaining_before <= 0:
            raise HTTPException(
                status_code=429,
                detail="You have used all 5 prompts available in this session.",
            )

        answer = generate_ai_answer(prompt, db)
        remaining_after = await consume_prompt(identifier)

        return {
            "answer": answer,
            "remaining_prompts": remaining_after,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("chat_assistant failed")
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )