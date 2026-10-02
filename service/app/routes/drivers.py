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
    """App gọi mỗi lần mở để biết nên vào phần giám sát hay hiện màn chờ duyệt.
    Đồng bộ luôn trạng thái xác thực email thật từ Firebase Auth (không chỉ
    đọc cache Firestore) — để màn "chờ xác thực email" tự cập nhật đúng lúc."""
    driver = driver_service.sync_email_verified(user["uid"])
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


class PhotoUpdate(BaseModel):
    photo_url: str


@self_router.put("/{driver_id}/photo")
def update_photo(
    driver_id: str,
    payload: PhotoUpdate,
    user: dict = Depends(get_current_active_driver),
):
    if user["uid"] != driver_id:
        raise HTTPException(status_code=403, detail="Không thể sửa tài xế khác")
    driver = driver_service.set_photo_url(driver_id, payload.photo_url)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@self_router.put("/{driver_id}/profile")
def update_my_profile(
    driver_id: str,
    payload: DriverRegister,
    user: dict = Depends(get_current_active_driver),
):
    """Tài xế tự sửa thông tin cá nhân — chỉ đúng 3 trường này, không đụng
    được status/presence/quyền (khác PUT /{driver_id} của admin nhận dict tự do)."""
    if user["uid"] != driver_id:
        raise HTTPException(status_code=403, detail="Không thể sửa tài xế khác")
    driver = driver_service.update_driver(driver_id, payload.model_dump())
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


class SpeedUpdate(BaseModel):
    speed_kmh: float


@self_router.put("/{driver_id}/speed")
def update_speed(
    driver_id: str,
    payload: SpeedUpdate,
    user: dict = Depends(get_current_active_driver),
):
    """App gọi định kỳ CHỈ KHI đang mở ở foreground — xem driver_service.set_speed."""
    if user["uid"] != driver_id:
        raise HTTPException(status_code=403, detail="Không thể sửa tài xế khác")
    driver = driver_service.set_speed(driver_id, payload.speed_kmh)
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
    try:
        driver = driver_service.approve_driver(driver_id, admin["uid"])
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Tài xế chưa xác thực email — chưa thể duyệt",
        )
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


@router.post("/{driver_id}/alert-sound")
def send_alert_sound(driver_id: str):
    """Đẩy FCM cho app tài xế tự phát âm thanh cảnh báo ngay (dù đang nền)."""
    result = driver_service.send_alert_sound(driver_id)
    if result["reason"] == "driver_not_found":
        raise HTTPException(status_code=404, detail="Driver not found")
    return result


@router.post("/{driver_id}/reset-password")
def reset_driver_password(driver_id: str):
    """Admin đặt lại mật khẩu cho tài xế (hỗ trợ khi tài xế gọi báo quên mật
    khẩu). Trả `{"temp_password": "..."}` — chỉ hiện đúng 1 lần, admin phải
    báo ngay cho tài xế."""
    try:
        return driver_service.reset_password(driver_id)
    except ValueError as e:
        if str(e) == "driver_not_found":
            raise HTTPException(status_code=404, detail="Driver not found")
        raise HTTPException(
            status_code=400,
            detail="Tài xế này không có tài khoản Firebase (do admin tạo tay) — không đặt lại mật khẩu được",
        )


@router.delete("/{driver_id}")
def delete_driver(driver_id: str):
    if not driver_service.delete_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"status": "success"}
