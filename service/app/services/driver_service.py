import secrets
from datetime import datetime, timezone
from typing import Optional

from firebase_admin import auth as firebase_auth

from app.core.firebase import db
from app.models.driver import DriverCreate, DriverRegister
from app.services import email_service, notification_service

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

    # Xoá HẲN tài xế -> dọn luôn lịch sử sự cố gắn với họ, tránh điểm vi phạm
    # "ma" của tài khoản không còn tồn tại vẫn cộng vào tổng điểm toàn đội xe
    # trên trang Báo cáo sự cố. Import trễ để tránh vòng lặp import (incident_
    # service đã import driver_service ở trên).
    from app.services import incident_service

    incident_service.delete_by_driver(driver_id)
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

    # email_verified: Firebase gửi sẵn email xác thực lúc tạo tài khoản (client
    # gọi user.sendEmailVerification()) — false cho tới khi tài xế bấm link.
    data = {
        "name": reg.name,
        "phone": reg.phone,
        "license_number": reg.license_number,
        "email": email,
        "status": "pending",
        "email_verified": False,
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


def sync_email_verified(driver_id: str) -> Optional[dict]:
    """Đọc trạng thái xác thực email THẬT (Firebase Auth) và ghi lại vào hồ sơ
    nếu khác — gọi mỗi lần app tài xế check-in (GET /drivers/me) hoặc trước
    khi admin duyệt, để không dựa vào dữ liệu Firestore có thể lỗi thời."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    snap = doc_ref.get()
    if not snap.exists:
        return None
    data = snap.to_dict()
    try:
        verified = bool(firebase_auth.get_user(driver_id).email_verified)
    except firebase_auth.UserNotFoundError:
        return {"id": driver_id, **data}
    if data.get("email_verified") != verified:
        doc_ref.update({"email_verified": verified})
        data["email_verified"] = verified
    return {"id": driver_id, **data}


def approve_driver(driver_id: str, admin_uid: str) -> Optional[dict]:
    """Duyệt hồ sơ. Raise ValueError("email_not_verified") nếu tài xế chưa
    xác thực email — chặn đúng theo luồng: đăng ký -> xác thực email -> mới
    được admin duyệt -> gửi mail báo đã duyệt."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None

    current = sync_email_verified(driver_id)  # luôn kiểm tra lại bằng dữ liệu thật
    if not (current or {}).get("email_verified"):
        raise ValueError("email_not_verified")

    doc_ref.update(
        {
            "status": "active",
            "approved_at": _now(),
            "approved_by": admin_uid,
            "reject_reason": None,
        }
    )
    _set_approved_claim(driver_id, True)
    driver = {"id": driver_id, **doc_ref.get().to_dict()}

    try:
        email_service.send_registration_approved(driver.get("email"), driver.get("name", ""))
    except Exception:
        pass  # gửi mail lỗi không được làm hỏng việc duyệt đã thành công
    return driver


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


def set_speed(driver_id: str, speed_kmh: float) -> Optional[dict]:
    """App gọi định kỳ CHỈ KHI đang mở ở foreground (quyết định có chủ đích —
    không theo dõi nền để đỡ tốn pin và tôn trọng quyền riêng tư tài xế)."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(
        {"current_speed_kmh": max(0.0, speed_kmh), "speed_updated_at": _now()}
    )
    return {"id": driver_id, **doc_ref.get().to_dict()}


def send_alert_sound(driver_id: str) -> dict:
    """Admin bấm "Phát loa cảnh báo" trên web -> đẩy FCM tới app tài xế; app
    nhận data `type=play_alert_sound` thì tự phát âm thanh cảnh báo local
    (AlertService, có sẵn từ luồng phát hiện buồn ngủ) — hoạt động cả khi
    app đang nền. Trả {"sent": bool, "reason": str}, không raise, để route
    trả 200 kèm lý do (chưa có token...) cho UI hiển thị."""
    driver = get_driver(driver_id)
    if driver is None:
        return {"sent": False, "reason": "driver_not_found"}
    token = driver.get("fcm_token")
    if not token:
        return {"sent": False, "reason": "driver_has_no_fcm_token"}
    try:
        notification_service.send_push(
            token=token,
            title="Cảnh báo từ quản trị viên",
            body="Vui lòng chú ý quan sát và lái xe an toàn.",
            data={"type": "play_alert_sound"},
        )
    except Exception as e:
        return {"sent": False, "reason": f"push_failed: {e}"}
    return {"sent": True, "reason": "ok"}


def set_photo_url(driver_id: str, photo_url: str) -> Optional[dict]:
    """Tài xế tự upload ảnh lên Firebase Storage xong (client-side, giống
    cách admin đang làm ở web) thì gọi hàm này lưu URL vào hồ sơ."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update({"photo_url": photo_url})
    return {"id": driver_id, **doc_ref.get().to_dict()}


def reset_password(driver_id: str) -> dict:
    """Admin đặt lại mật khẩu cho tài xế — dùng khi tài xế gọi báo quên mật
    khẩu (bổ sung cho luồng tự gửi mail đặt lại mật khẩu trên app, phòng khi
    tài xế không vào được email). Sinh mật khẩu tạm ngẫu nhiên, ghi thẳng vào
    Firebase Auth, thu hồi phiên đăng nhập cũ để bắt buộc dùng mật khẩu mới
    ngay. Trả về mật khẩu tạm — KHÔNG lưu lại ở đâu, admin phải báo ngay cho
    tài xế lúc này vì chỉ xem được một lần.

    Raise ValueError("driver_not_found") hoặc ValueError("no_firebase_account")
    — route dịch thành 404 / 400 tương ứng."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        raise ValueError("driver_not_found")

    try:
        firebase_auth.get_user(driver_id)
    except firebase_auth.UserNotFoundError:
        # Tài xế do admin tạo tay (doc id ngẫu nhiên, không gắn tài khoản
        # Firebase nào) -> không có mật khẩu nào để đặt lại.
        raise ValueError("no_firebase_account")

    temp_password = secrets.token_urlsafe(9)  # ~12 ký tự, đủ mạnh
    firebase_auth.update_user(driver_id, password=temp_password)
    firebase_auth.revoke_refresh_tokens(driver_id)
    return {"temp_password": temp_password}


def set_presence(driver_id: str, presence: str) -> Optional[dict]:
    """Cập nhật trạng thái kết nối do app tài xế báo lên. Ghi kèm last_seen để
    web phát hiện 'online nhưng mất tín hiệu' (app crash không kịp báo offline)."""
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update({"presence": presence, "last_seen": _now()})
    return {"id": driver_id, **doc_ref.get().to_dict()}
