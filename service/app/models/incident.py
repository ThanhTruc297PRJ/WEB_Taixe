from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IncidentBase(BaseModel):
    driver_id: str
    trip_id: Optional[str] = None
    type: str  # "drowsiness" | "distraction"
    detected_at: datetime
    confidence: Optional[float] = None
    points: int = 0  # điểm vi phạm; cộng dồn để so mốc 10 / 22 / 30
    snapshot_url: Optional[str] = None  # ảnh chụp lúc vi phạm (URL tải Firebase Storage)
    clip_url: Optional[str] = None  # video clip ngắn (URL tải Firebase Storage)
    note: Optional[str] = None


class IncidentCreate(IncidentBase):
    pass


class Incident(IncidentBase):
    id: str
