from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class OfflineIncident(BaseModel):
    event_id: str
    driver_id: str
    trip_id: Optional[str] = None
    type: str
    detected_at: datetime
    confidence: Optional[float] = None
    note: Optional[str] = None


class OfflineSyncRequest(BaseModel):
    incidents: List[OfflineIncident]


class OfflineSyncResult(BaseModel):
    total_received: int
    inserted: int
    skipped_duplicate: int