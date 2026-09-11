"""Lưu lịch sử hỏi–đáp với trợ lý AI để admin kiểm duyệt nội dung (C09 SUB-02)."""

from datetime import datetime, timezone
from typing import Optional

from app.core.firebase import db

COLLECTION = "chat_logs"


def create_log(
    uid: Optional[str],
    email: Optional[str],
    question: str,
    answer: str,
    sources: list[str],
    intent: Optional[str] = None,
) -> None:
    """Best-effort — lỗi ghi log không được làm hỏng câu trả lời cho người dùng."""
    try:
        db.collection(COLLECTION).document().set(
            {
                "uid": uid,
                "email": email,
                "question": question,
                "answer": answer,
                "sources": sources or [],
                "intent": intent,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception:
        pass


def list_logs(uid: Optional[str] = None) -> list[dict]:
    query = db.collection(COLLECTION)
    if uid:
        query = query.where("uid", "==", uid)
    return [{"id": d.id, **d.to_dict()} for d in query.stream()]


def delete_log(log_id: str) -> bool:
    ref = db.collection(COLLECTION).document(log_id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True
