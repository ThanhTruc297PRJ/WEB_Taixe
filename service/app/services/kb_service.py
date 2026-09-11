"""Cơ sở tri thức (Knowledge Base) cho RAG — admin quản lý qua web.

Nguồn sự thật: Firestore collection `kb_documents`. Mỗi lần thêm/sửa/xoá, đồng
bộ luôn vào Chroma vector store (tách chunk theo tiêu đề `## `) để trợ lý AI
dùng ngay, không cần chạy tay `ingest_kb.py` nữa.
"""

import re
from datetime import datetime, timezone
from typing import Optional

from app.core.firebase import db
from app.core.vectorstore import collection
from app.models.kb import KB_CATEGORIES, KbDocumentIn

COLLECTION = "kb_documents"
_SECTION_SPLIT = re.compile(r"\n(?=## )")


def _norm_category(value: str) -> str:
    return value if value in KB_CATEGORIES else "safety"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _chunk(title: str, content: str) -> list[str]:
    body = content.strip()
    # Bỏ dòng tiêu đề H1 đầu tiên (# ...) — không phải nội dung hữu ích.
    first, _, rest = body.partition("\n")
    if first.startswith("# "):
        body = rest.strip()
    parts = [s.strip() for s in _SECTION_SPLIT.split(body) if s.strip()]
    return parts or ([body] if body else [])


def _reindex(doc_id: str, title: str, content: str, category: str) -> int:
    """Xoá chunk cũ của tài liệu này trong Chroma rồi nạp lại. Trả số chunk."""
    try:
        collection.delete(where={"source": doc_id})
    except Exception:
        pass
    chunks = _chunk(title, content)
    if chunks:
        collection.upsert(
            ids=[f"{doc_id}-{i}" for i in range(len(chunks))],
            documents=[f"{title}\n{c}" for c in chunks],
            metadatas=[
                {"source": doc_id, "title": title, "category": category}
                for _ in chunks
            ],
        )
    return len(chunks)


def _remove_from_index(doc_id: str) -> None:
    try:
        collection.delete(where={"source": doc_id})
    except Exception:
        pass


def list_documents() -> list[dict]:
    return [
        {"id": d.id, **d.to_dict()}
        for d in db.collection(COLLECTION).stream()
    ]


def get_document(doc_id: str) -> Optional[dict]:
    snap = db.collection(COLLECTION).document(doc_id).get()
    if not snap.exists:
        return None
    return {"id": snap.id, **snap.to_dict()}


def create_document(payload: KbDocumentIn, admin_uid: str) -> dict:
    ref = db.collection(COLLECTION).document()
    category = _norm_category(payload.category)
    n = _reindex(ref.id, payload.title, payload.content, category)
    data = {
        "title": payload.title,
        "content": payload.content,
        "category": category,
        "chunks": n,
        "updated_at": _now(),
        "updated_by": admin_uid,
    }
    ref.set(data)
    return {"id": ref.id, **data}


def update_document(
    doc_id: str, payload: KbDocumentIn, admin_uid: str
) -> Optional[dict]:
    ref = db.collection(COLLECTION).document(doc_id)
    if not ref.get().exists:
        return None
    category = _norm_category(payload.category)
    n = _reindex(doc_id, payload.title, payload.content, category)
    ref.update(
        {
            "title": payload.title,
            "content": payload.content,
            "category": category,
            "chunks": n,
            "updated_at": _now(),
            "updated_by": admin_uid,
        }
    )
    return {"id": doc_id, **ref.get().to_dict()}


def delete_document(doc_id: str) -> bool:
    ref = db.collection(COLLECTION).document(doc_id)
    if not ref.get().exists:
        return False
    _remove_from_index(doc_id)
    ref.delete()
    return True
