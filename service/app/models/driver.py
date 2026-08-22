from typing import Optional

from pydantic import BaseModel


class DriverBase(BaseModel):
    name: str
    phone: str
    license_number: str
    fcm_token: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class Driver(DriverBase):
    id: str
