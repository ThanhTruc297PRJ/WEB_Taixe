from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DriverBase(BaseModel):
    name: str
    phone: str
    license_number: str
    status: str = "active"  # "active" | "inactive" (do admin đặt)
    # presence do app tài xế cập nhật realtime; web nghe qua Firestore onSnapshot.
    presence: str = "offline"  # "online" | "offline" | "driving"
    last_seen: Optional[datetime] = None
    fcm_token: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class Driver(DriverBase):
    id: str
