"""Cấu hình chung của hệ thống — lưu 1 doc duy nhất trong Firestore, admin tự
chỉnh qua trang Cài đặt web thay vì phải sửa code. Luôn có giá trị mặc định
cứng để dùng được ngay cả khi doc chưa từng được tạo."""

from app.core.firebase import db

COLLECTION = "app_settings"
DOC_ID = "general"

DEFAULTS = {
    "violation_thresholds": {
        "reminder": 10,  # tổng điểm >= giá trị này -> mức "Nhắc nhở"
        "warning": 22,  # -> "Cảnh cáo" (backend dùng làm ngưỡng severity "high")
        "suspend": 30,  # -> "Đình chỉ" (backend dùng làm ngưỡng severity "critical")
    },
    "maintenance_defaults": {
        "remind_days_before": 7,
        "remind_km_before": 500,
    },
    "inspection_defaults": {
        "remind_days_before": 15,
    },
}


def get_settings() -> dict:
    doc = db.collection(COLLECTION).document(DOC_ID).get()
    data = doc.to_dict() if doc.exists else {}
    # Merge nông theo từng nhóm -> thiếu nhóm/field nào vẫn có mặc định, không
    # bao giờ trả về thiếu key khiến frontend phải tự phòng thủ undefined.
    return {
        key: {**default_group, **(data.get(key) or {})}
        for key, default_group in DEFAULTS.items()
    }


def update_settings(data: dict) -> dict:
    current = get_settings()
    for key in DEFAULTS:
        incoming = data.get(key)
        if isinstance(incoming, dict):
            current[key] = {**current[key], **incoming}
    db.collection(COLLECTION).document(DOC_ID).set(current)
    return current


def get_violation_thresholds() -> dict:
    return get_settings()["violation_thresholds"]
