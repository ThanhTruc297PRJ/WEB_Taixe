import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

bearer_scheme = HTTPBearer(auto_error=False)
_log = logging.getLogger("driver_monitoring.security")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        # clock_skew_seconds: cho phép lệch giờ nhẹ giữa máy chủ và Google
        # (nếu không, token vừa cấp có thể bị coi là "used too early").
        return firebase_auth.verify_id_token(
            credentials.credentials, clock_skew_seconds=10
        )
    except Exception as e:
        _log.warning("verify_id_token failed: %s: %s", type(e).__name__, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """Chỉ cho qua user có custom claim `admin: true` (gán bằng
    scripts/set_admin.py). Dùng cho các route quản trị viên."""
    if user.get("admin") is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yêu cầu quyền quản trị",
        )
    return user


def get_current_active_driver(user: dict = Depends(get_current_user)) -> dict:
    """Chỉ cho qua tài xế đã được duyệt (custom claim `approved: true`, gán khi
    admin bấm Duyệt và gỡ khi bị khoá/từ chối). Dùng cho các route app tài xế
    gọi khi đang giám sát (presence, sync, fcm-token...)."""
    if user.get("approved") is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được duyệt hoặc đã bị khoá",
        )
    return user
