from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_admin, get_current_user
from app.services import chat_log_service, intent_router, rag_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
    intent = intent_router.classify(payload.question)
    result = rag_service.answer(payload.question, intent)
    chat_log_service.create_log(
        uid=user.get("uid"),
        email=user.get("email"),
        question=payload.question,
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        intent=intent,
    )
    return result


# ── Web admin: kiểm duyệt lịch sử chat ───────────────────────────────────
@router.get("/logs", dependencies=[Depends(get_current_admin)])
def list_logs(driver_id: Optional[str] = None):
    return chat_log_service.list_logs(driver_id)


@router.delete("/logs/{log_id}", dependencies=[Depends(get_current_admin)])
def delete_log(log_id: str):
    if not chat_log_service.delete_log(log_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy log")
    return {"status": "success"}
