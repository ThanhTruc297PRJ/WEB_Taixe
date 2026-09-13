from typing import Optional

from pydantic import BaseModel


class VehicleBase(BaseModel):
    plate_number: str
    brand: str
    model: str
    year: Optional[int] = None
    status: str = "active"  # "active" | "maintenance" | "inactive"
    driver_id: Optional[str] = None  # tài xế đang phụ trách xe
    # Số km đã chạy — cập nhật thủ công bởi admin (hoặc đồng bộ sau này từ app
    # tài xế). Dùng để tính khi nào tới hạn bảo trì/đăng kiểm theo km.
    current_odometer_km: Optional[int] = None
    note: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class Vehicle(VehicleBase):
    id: str
