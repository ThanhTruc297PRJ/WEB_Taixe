from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IncidentBase(BaseModel):
    driver_id: str
    trip_id: Optional[str] = None
    type: str  # "drowsiness" | "distraction"
    detected_at: datetime
    confidence: Optional[float] = None
    note: Optional[str] = None


class IncidentCreate(IncidentBase):
    pass


class Incident(IncidentBase):
    id: str
