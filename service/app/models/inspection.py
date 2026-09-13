from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InspectionBase(BaseModel):
    """Đăng kiểm xe — tách riêng khỏi bảo trì (TASK-C10): có trạm, khung giờ
    hẹn, ngày hết hạn tem cũ, chi phí, tách biệt việc "đi đăng kiểm" khỏi việc
    "thay dầu/lốp"."""

    vehicle_id: str
    driver_id: Optional[str] = None  # người phụ trách mang xe đi đăng kiểm

    station: str  # trạm đăng kiểm
    # Khung giờ hẹn — có thể để trống khi mới sinh lịch kỳ tiếp theo (chưa đặt
    # lịch cụ thể), điền sau khi admin liên hệ trạm đặt hẹn.
    appointment_at: Optional[datetime] = None
    old_sticker_expiry: datetime  # ngày hết hạn tem/giấy chứng nhận cũ

    status: str = "pending"  # "pending" | "done"
    result: Optional[str] = None  # "passed" | "failed" — chỉ có khi status=done
    remind_days_before: int = 15  # báo trước bao nhiêu ngày (tính từ ngày hết hạn tem)

    inspection_fee: Optional[float] = None  # phí kiểm định
    road_fee: Optional[float] = None  # phí bảo trì đường bộ
    note: Optional[str] = None


class InspectionCreate(InspectionBase):
    pass


class Inspection(InspectionBase):
    id: str
    last_reminded_at: Optional[datetime] = None


class InspectionComplete(BaseModel):
    """Đóng hồ sơ đăng kiểm: bắt buộc chọn kết quả. Nếu Đạt và có
    new_sticker_expiry -> tự sinh hồ sơ kỳ tiếp theo (tem mới, chưa đặt lịch)."""

    result: str  # "passed" | "failed"
    new_sticker_expiry: Optional[datetime] = None
