from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import (
    get_current_active_driver,
    get_current_admin,
    get_current_user,
)
from app.models.driver import DriverCreate, DriverRegister, DriverReject
from app.services import driver_service

router = APIRouter(
    prefix="/drivers",
    tags=["drivers"],
    dependencies=[Depends(get_current_admin)],
)

# Router riêng: các endpoint app tài xế tự gọi — chỉ cần đăng nhập, KHÔNG cần
# quyền admin.
self_router = APIRouter(prefix="/drivers", tags=["drivers (app tài xế)"])


# ── App tài xế ───────────────────────────────────────────────────────────
@self_router.post("/register", status_code=201)
def register_driver(
    reg: DriverRegister,
    user: dict = Depends(get_current_user),
):
    """Tài xế tự đăng ký sau khi tạo tài khoản Firebase. Hồ sơ ở trạng thái
    `pending` chờ admin duyệt."""
    result = driver_service.register_driver(user["uid"], user.get("email"), reg)
    if result is None:
        raise HTTPException(
            status_code=409, detail="Tài khoản này đã đăng ký hồ sơ tài xế"
        )
    return result


@self_router.get("/me")
def get_my_driver_profile(user: dict = Depends(get_current_user)):
    """App gọi mỗi lần mở để biết nên vào phần giám sát hay hiện màn chờ duyệt."""
    driver = driver_service.get_driver(user["uid"])
    if driver is None:
        raise HTTPException(status_code=404, detail="Chưa đăng ký hồ sơ tài xế")
    return driver


class PresenceUpdate(BaseModel):
    presence: str  # "online" | "offline" | "driving"


@self_router.put("/{driver_id}/presence")
def update_presence(
    driver_id: str,
    payload: PresenceUpdate,
    user: dict = Depends(get_current_active_driver),
):
    if user["uid"] != driver_id:
        raise HTTPException(status_code=403, detail="Không thể sửa tài xế khác")
    if payload.presence not in driver_service.PRESENCE_VALUES:
        raise HTTPException(status_code=422, detail="Giá trị presence không hợp lệ")
    driver = driver_service.set_presence(driver_id, payload.presence)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


class FcmTokenUpdate(BaseModel):
    fcm_token: str


@self_router.put("/{driver_id}/fcm-token")
def update_fcm_token(
    driver_id: str,
    payload: FcmTokenUpdate,
    user: dict = Depends(get_current_active_driver),
):
    if user["uid"] != driver_id:
        raise HTTPException(status_code=403, detail="Không thể sửa tài xế khác")
    driver = driver_service.set_fcm_token(driver_id, payload.fcm_token)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


# ── Web admin ────────────────────────────────────────────────────────────
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


@router.put("/{driver_id}/approve")
def approve_driver(driver_id: str, admin: dict = Depends(get_current_admin)):
    driver = driver_service.approve_driver(driver_id, admin["uid"])
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}/reject")
def reject_driver(driver_id: str, payload: DriverReject):
    driver = driver_service.reject_driver(driver_id, payload.reason)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}/lock")
def lock_driver(driver_id: str):
    driver = driver_service.set_active(driver_id, False)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}/unlock")
def unlock_driver(driver_id: str):
    driver = driver_service.set_active(driver_id, True)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.delete("/{driver_id}")
def delete_driver(driver_id: str):
    if not driver_service.delete_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"status": "success"}
