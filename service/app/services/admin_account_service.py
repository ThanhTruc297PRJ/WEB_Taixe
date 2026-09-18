"""Quản lý tài khoản quản trị viên (custom claim Firebase `admin`) — thay thế
việc phải chạy tay `scripts/set_admin.py` trên server bằng thao tác ngay trên
trang Cài đặt web."""

from firebase_admin import auth as firebase_auth


def list_admins() -> list[dict]:
    admins = []
    for user in firebase_auth.list_users().iterate_all():
        if (user.custom_claims or {}).get("admin") is True:
            admins.append(
                {"uid": user.uid, "email": user.email, "disabled": user.disabled}
            )
    return admins


def grant_admin(email: str) -> dict:
    """Raise firebase_auth.UserNotFoundError nếu email chưa có tài khoản
    Firebase nào (route dịch thành 404)."""
    user = firebase_auth.get_user_by_email(email)
    claims = dict(user.custom_claims or {})
    claims["admin"] = True
    firebase_auth.set_custom_user_claims(user.uid, claims)
    firebase_auth.revoke_refresh_tokens(user.uid)  # buộc lấy claim mới ở lần đăng nhập tới
    return {"uid": user.uid, "email": user.email}


def revoke_admin(uid: str, requester_uid: str) -> None:
    """Raise ValueError("cannot_revoke_self") nếu tự thu hồi quyền của chính
    mình (tránh khoá hết đường vào web admin). Raise
    firebase_auth.UserNotFoundError nếu uid không tồn tại."""
    if uid == requester_uid:
        raise ValueError("cannot_revoke_self")
    user = firebase_auth.get_user(uid)
    claims = dict(user.custom_claims or {})
    claims.pop("admin", None)
    firebase_auth.set_custom_user_claims(uid, claims)
    firebase_auth.revoke_refresh_tokens(uid)
