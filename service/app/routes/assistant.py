from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services import rag_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
    return rag_service.answer(payload.question)
