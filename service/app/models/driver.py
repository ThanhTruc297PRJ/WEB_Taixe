from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DriverBase(BaseModel):
    name: str
    phone: str
    license_number: str
    # "pending" | "active" | "inactive" | "rejected"
    # admin tạo tay -> "active"; tài xế tự đăng ký -> "pending" (set trong service).
    status: str = "active"
    # presence do app tài xế cập nhật realtime; web nghe qua Firestore onSnapshot.
    presence: str = "offline"  # "online" | "offline" | "driving"
    last_seen: Optional[datetime] = None
    fcm_token: Optional[str] = None
    # Đồng bộ từ Firebase Auth (nguồn sự thật là Auth, đây chỉ là cache để web
    # admin xem nhanh) — xem driver_service.sync_email_verified.
    email_verified: bool = False
    # Tài xế tự upload từ app (Firebase Storage) rồi gọi PUT .../photo để lưu
    # URL vào đây — web admin đọc thẳng field này, không cần gọi Firebase Auth
    # Admin SDK riêng cho từng dòng khi hiển thị danh sách.
    photo_url: Optional[str] = None
    # App gửi định kỳ CHỈ KHI đang mở ở foreground (không theo dõi nền) — xem
    # driver_service.set_speed. speed_updated_at để web tự biết dữ liệu đã cũ
    # (tài xế tắt app) và ẩn đi thay vì hiện số liệu sai lệch mãi mãi.
    current_speed_kmh: Optional[float] = None
    speed_updated_at: Optional[datetime] = None


class DriverCreate(DriverBase):
    """Admin tạo tài xế trực tiếp (doc id ngẫu nhiên)."""

    pass


class DriverRegister(BaseModel):
    """Tài xế tự khai khi đăng ký qua app (doc id = Firebase Auth uid)."""

    name: str
    phone: str
    license_number: str


class DriverReject(BaseModel):
    reason: str


class Driver(DriverBase):
    id: str  # = Firebase Auth uid nếu tài xế tự đăng ký
    email: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None  # uid của admin duyệt
    reject_reason: Optional[str] = None
