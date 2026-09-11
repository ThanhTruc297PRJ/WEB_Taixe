from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Nhóm tài liệu — retriever lọc theo nhóm tuỳ ý định câu hỏi (xem intent_router).
KB_CATEGORIES = ("safety", "traffic_law", "vehicle_manual")


class KbDocumentIn(BaseModel):
    """Admin thêm/sửa tài liệu cơ sở tri thức. `content` là markdown; tách chunk
    theo tiêu đề `## ` khi nạp vào vector store."""

    title: str
    content: str
    category: str = "safety"


class KbDocument(KbDocumentIn):
    id: str
    chunks: int = 0
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
