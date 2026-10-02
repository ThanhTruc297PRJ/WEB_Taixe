from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel

from app.core.security import get_current_active_driver, get_current_admin
from app.services import admin_account_service, app_settings_service

# Đặt tên module là `app_settings` (không phải `settings`) để tránh đụng tên
# với `app.core.config.settings` (đối tượng cấu hình app) đã import trong
# main.py — trùng tên sẽ khiến main.py vô tình dùng nhầm module này.
router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_admin)],
)

# App tài xế chỉ được đọc nhóm "contact", không thấy cấu hình khác.
self_router = APIRouter(prefix="/settings", tags=["settings (app tài xế)"])


@self_router.get("/contact")
def get_contact(_: dict = Depends(get_current_active_driver)):
    return app_settings_service.get_settings()["contact"]


@router.get("/")
def get_settings():
    return app_settings_service.get_settings()


@router.put("/")
def update_settings(data: dict):
    return app_settings_service.update_settings(data)


@router.get("/admins")
def list_admins():
    return admin_account_service.list_admins()


class GrantAdminPayload(BaseModel):
    email: str


@router.post("/admins")
def grant_admin(payload: GrantAdminPayload):
    try:
        return admin_account_service.grant_admin(payload.email)
    except firebase_auth.UserNotFoundError:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy tài khoản với email này"
        )


@router.delete("/admins/{uid}")
def revoke_admin(uid: str, admin: dict = Depends(get_current_admin)):
    try:
        admin_account_service.revoke_admin(uid, admin["uid"])
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Không thể tự thu hồi quyền admin của chính mình"
        )
    except firebase_auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    return {"status": "success"}
