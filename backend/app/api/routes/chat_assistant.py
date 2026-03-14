from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_rate_limit_service import (
    consume_prompt,
    has_remaining_prompts,
)
from app.services.chat_service import (
    build_store_context,
    generate_ai_answer,
    list_items_for_ai,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat-assistant", tags=["chat-assistant"])


def get_chat_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        return f"guest:{ip}"

    client_host = request.client.host if request.client else "unknown"
    return f"guest:{client_host}"


@router.post("")
def chat_with_assistant(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    identifier = get_chat_identifier(request)

    if not has_remaining_prompts(identifier):
        raise HTTPException(
            status_code=429,
            detail="ניצלת את כל 5 הפרומפטים הזמינים כרגע. נסה שוב מאוחר יותר.",
        )

    try:
        items = list_items_for_ai(db)
        store_context = build_store_context(items)
        answer = generate_ai_answer(payload.prompt, store_context)

        remaining_prompts = consume_prompt(identifier)

        return {
            "answer": answer,
            "remaining_prompts": remaining_prompts,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("chat_assistant failed")
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )