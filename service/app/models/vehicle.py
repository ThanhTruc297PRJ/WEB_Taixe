from typing import Optional

from pydantic import BaseModel


class VehicleBase(BaseModel):
    plate_number: str
    brand: str
    model: str
    year: Optional[int] = None
    status: str = "active"  # "active" | "maintenance" | "inactive"
    driver_id: Optional[str] = None  # tài xế đang phụ trách xe
    note: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class Vehicle(VehicleBase):
    id: str
