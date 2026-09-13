from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MaintenanceBase(BaseModel):
    vehicle_id: str
    driver_id: Optional[str] = None  # người phụ trách mang xe đi bảo trì lần này
    vendor: Optional[str] = None  # gara / đơn vị thực hiện
    type: str  # "oil_change" | "tire" | "brake" | "battery" | "other"
    scheduled_date: datetime
    status: str = "pending"  # "pending" | "done" (quá hạn suy ra từ ngày)
    odometer: Optional[int] = None  # số km lúc bảo trì (ghi nhận khi làm xong)

    # Nhắc tự động: tới hạn theo NGÀY hoặc theo KM, cái nào tới trước thì báo.
    interval_km: Optional[int] = None  # chu kỳ bảo trì (vd: 5000km thay dầu 1 lần)
    due_odometer_km: Optional[int] = None  # km dự kiến tới hạn lần này
    remind_days_before: int = 7  # báo trước bao nhiêu ngày theo lịch
    remind_km_before: int = 500  # còn bấy nhiêu km thì bắt đầu báo

    cost: Optional[float] = None  # chi phí bảo trì lần này
    note: Optional[str] = None


class MaintenanceCreate(MaintenanceBase):
    pass


class Maintenance(MaintenanceBase):
    id: str
    last_reminded_at: Optional[datetime] = None
