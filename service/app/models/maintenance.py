from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MaintenanceBase(BaseModel):
    vehicle_id: str
    type: str  # "oil_change" | "tire" | "inspection" | "other"...
    scheduled_date: datetime
    status: str = "pending"  # "pending" | "done" (quá hạn suy ra từ ngày)
    odometer: Optional[int] = None
    note: Optional[str] = None


class MaintenanceCreate(MaintenanceBase):
    pass


class Maintenance(MaintenanceBase):
    id: str
