from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TripBase(BaseModel):
    driver_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None


class TripCreate(TripBase):
    pass


class Trip(TripBase):
    id: str
