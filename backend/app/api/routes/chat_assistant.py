from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_rate_limit_service import (
    consume_prompt,
    get_remaining_prompts,
)
from app.services.chat_service import generate_ai_answer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat-assistant", tags=["chat-assistant"])


def get_chat_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        return f"guest:{ip}"

    client_host = request.client.host if request.client else "unknown"
    return f"guest:{client_host}"


@router.get("/remaining")
async def get_chat_remaining(request: Request):
    identifier = get_chat_identifier(request)
    remaining = await get_remaining_prompts(identifier)

    return {
        "remaining_prompts": remaining,
    }


@router.post("")
async def chat_with_assistant(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    identifier = get_chat_identifier(request)

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