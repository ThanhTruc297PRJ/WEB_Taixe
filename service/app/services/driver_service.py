from datetime import datetime, timezone
from typing import Optional

from firebase_admin import auth as firebase_auth

from app.core.firebase import db
from app.models.driver import DriverCreate, DriverRegister

COLLECTION = "drivers"

PRESENCE_VALUES = {"online", "offline", "driving"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _set_approved_claim(uid: str, approved: bool) -> None:
    """Gán / gỡ custom claim `approved` trên tài khoản Firebase.

    - Khi DUYỆT (approved=True): chỉ set claim. App gọi getIdToken(true) là
      nhận claim mới ngay — KHÔNG revoke để refresh token còn dùng được.
    - Khi TỪ CHỐI / KHOÁ (approved=False): set claim + revoke refresh token
      để chặn ngay lập tức (token cũ còn `approved:true` tối đa 1 giờ).

    Bỏ qua nếu uid không phải tài khoản Firebase (tài xế do admin tạo tay có
    doc id ngẫu nhiên, không gắn tài khoản nào)."""
    try:
        fb_user = firebase_auth.get_user(uid)
    except firebase_auth.UserNotFoundError:
        return
    claims = dict(fb_user.custom_claims or {})
    if approved:
        claims["approved"] = True
    else:
        claims.pop("approved", None)
    firebase_auth.set_custom_user_claims(uid, claims)
    if not approved:
        firebase_auth.revoke_refresh_tokens(uid)


# ── Admin tạo tài xế trực tiếp ────────────────────────────────────────────
def create_driver(driver: DriverCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = driver.model_dump()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def get_driver(driver_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(driver_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_drivers() -> list[dict]:
    return [{"id": doc.id, **doc.to_dict()} for doc in db.collection(COLLECTION).stream()]


def update_driver(driver_id: str, data: dict) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(data)
    return {"id": driver_id, **doc_ref.get().to_dict()}


def delete_driver(driver_id: str) -> bool:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    try:
        firebase_auth.delete_user(driver_id)  # với tài khoản tự đăng ký: id = uid
    except firebase_auth.UserNotFoundError:
        pass
    return True


# ── Tài xế tự đăng ký + admin duyệt/từ chối/khoá ─────────────────────────
def register_driver(
    uid: str, email: Optional[str], reg: DriverRegister
) -> Optional[dict]:
    """Tài xế tự đăng ký qua app. Doc id = Firebase uid.

    Trả None (route -> 409) nếu đã có hồ sơ đang `pending` / `active` /
    `inactive`. Chỉ cho đăng ký lại khi hồ sơ cũ đã bị `rejected`."""
    doc_ref = db.collection(COLLECTION).document(uid)
    snap = doc_ref.get()
    if snap.exists and snap.to_dict().get("status") != "rejected":
        return None

    data = {
        "name": reg.name,
        "phone": reg.phone,
        "license_number": reg.license_number,
        "email": email,
        "status": "pending",
        "presence": "offline",
        "last_seen": None,
        "fcm_token": None,
        "submitted_at": _now(),
        "approved_at": None,
        "approved_by": None,
        "reject_reason": None,
    }
    doc_ref.set(data)
    return {"id": uid, **data}


def approve_driver(driver_id: str, admin_uid: str) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(
        {
            "status": "active",
            "approved_at": _now(),
            "approved_by": admin_uid,
            "reject_reason": None,
        }
    )
    _set_approved_claim(driver_id, True)
    return {"id": driver_id, **doc_ref.get().to_dict()}


def reject_driver(driver_id: str, reason: str) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update({"status": "rejected", "reject_reason": reason})
    _set_approved_claim(driver_id, False)
    return {"id": driver_id, **doc_ref.get().to_dict()}


def set_active(driver_id: str, active: bool) -> Optional[dict]:
    """Khoá / mở khoá tài khoản đã duyệt (active <-> inactive)."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update({"status": "active" if active else "inactive"})
    _set_approved_claim(driver_id, active)
    return {"id": driver_id, **doc_ref.get().to_dict()}


def set_fcm_token(driver_id: str, token: str) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update({"fcm_token": token})
    return {"id": driver_id, **doc_ref.get().to_dict()}


def set_presence(driver_id: str, presence: str) -> Optional[dict]:
    """Cập nhật trạng thái kết nối do app tài xế báo lên. Ghi kèm last_seen để
    web phát hiện 'online nhưng mất tín hiệu' (app crash không kịp báo offline)."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update({"presence": presence, "last_seen": _now()})
    return {"id": driver_id, **doc_ref.get().to_dict()}
