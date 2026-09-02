from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_admin, get_current_user
from app.models.driver import DriverCreate
from app.services import driver_service

router = APIRouter(
    prefix="/drivers",
    tags=["drivers"],
    dependencies=[Depends(get_current_admin)],
)

# Router riêng: endpoint app tài xế tự gọi để báo trạng thái kết nối —
# chỉ cần đăng nhập, KHÔNG cần quyền admin.
self_router = APIRouter(prefix="/drivers", tags=["drivers"])


class PresenceUpdate(BaseModel):
    presence: str  # "online" | "offline" | "driving"


@self_router.put("/{driver_id}/presence")
def update_presence(
    driver_id: str,
    payload: PresenceUpdate,
    _user: dict = Depends(get_current_user),
):
    if payload.presence not in driver_service.PRESENCE_VALUES:
        raise HTTPException(status_code=422, detail="Giá trị presence không hợp lệ")
    driver = driver_service.set_presence(driver_id, payload.presence)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.get("/")
def list_drivers():
    return driver_service.list_drivers()


@router.post("/")
def create_driver(driver: DriverCreate):
    return driver_service.create_driver(driver)


@router.get("/{driver_id}")
def get_driver(driver_id: str):
    driver = driver_service.get_driver(driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}")
def update_driver(driver_id: str, data: dict):
    driver = driver_service.update_driver(driver_id, data)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.delete("/{driver_id}")
def delete_driver(driver_id: str):
    if not driver_service.delete_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"status": "success"}
