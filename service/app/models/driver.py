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
