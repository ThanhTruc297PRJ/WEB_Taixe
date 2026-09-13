from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.firebase import db
from app.models.maintenance import MaintenanceCreate
from app.services import driver_service, notification_service, vehicle_service

COLLECTION = "maintenance_schedules"

_TYPE_LABELS = {
    "oil_change": "Thay dầu",
    "tire": "Kiểm tra/thay lốp",
    "brake": "Phanh/thắng",
    "battery": "Ắc quy",
    "other": "Bảo trì khác",
    # Giá trị cũ, còn lại từ trước khi tách Đăng kiểm (TASK-C10) — vẫn hiển thị
    # được cho dữ liệu cũ, không còn chọn được khi tạo mới.
    "inspection": "Đăng kiểm (cũ)",
}


def create_maintenance(maintenance: MaintenanceCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = maintenance.model_dump()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def get_maintenance(maintenance_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(maintenance_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_maintenance(vehicle_id: Optional[str] = None) -> list[dict]:
    query = db.collection(COLLECTION)
    if vehicle_id:
        query = query.where("vehicle_id", "==", vehicle_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def update_maintenance(maintenance_id: str, data: dict) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(maintenance_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(data)
    return {"id": maintenance_id, **doc_ref.get().to_dict()}


def delete_maintenance(maintenance_id: str) -> bool:
    doc_ref = db.collection(COLLECTION).document(maintenance_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


def _push_to_driver(driver_id: Optional[str], title: str, body: str, data: dict) -> dict:
    driver = driver_service.get_driver(driver_id) if driver_id else None
    if not driver or not driver.get("fcm_token"):
        return {"sent": False, "reason": "driver_has_no_fcm_token"}
    try:
        notification_service.send_push(
            token=driver["fcm_token"], title=title, body=body, data=data
        )
    except Exception as e:
        return {"sent": False, "reason": f"push_failed: {e}"}
    return {"sent": True, "reason": "ok"}


def notify_maintenance(maintenance_id: str) -> dict:
    """Gửi FCM nhắc lịch bảo trì tới tài xế đang phụ trách xe — nhắc thủ công
    (nút "Gửi nhắc" trên web). Xem [[reminder_scheduler]] cho nhắc tự động.

    Trả về {"sent": bool, "reason": str} — không raise để route trả 200 kèm
    lý do (không có token / chưa gán tài xế...) cho UI hiển thị.
    """
    maintenance = get_maintenance(maintenance_id)
    if maintenance is None:
        return {"sent": False, "reason": "maintenance_not_found"}

    vehicle = vehicle_service.get_vehicle(maintenance["vehicle_id"])
    if vehicle is None:
        return {"sent": False, "reason": "vehicle_not_found"}

    scheduled = maintenance["scheduled_date"]
    when = scheduled.strftime("%d/%m/%Y") if hasattr(scheduled, "strftime") else str(scheduled)
    label = _TYPE_LABELS.get(maintenance["type"], maintenance["type"])

    # Ưu tiên người phụ trách RIÊNG cho lần bảo trì này; không có thì gửi cho
    # tài xế đang phụ trách xe nói chung.
    driver_id = maintenance.get("driver_id") or vehicle.get("driver_id")
    result = _push_to_driver(
        driver_id,
        title="Nhắc lịch bảo trì xe",
        body=f"Xe {vehicle.get('plate_number', '')}: {label} — hạn {when}",
        data={"maintenance_id": maintenance_id, "vehicle_id": maintenance["vehicle_id"]},
    )
    if result["sent"]:
        update_maintenance(maintenance_id, {"last_reminded_at": datetime.now(timezone.utc)})
    return result


# ── Quét nhắc tự động (gọi từ reminder_scheduler theo chu kỳ) ────────────
def due_for_auto_reminder(now: Optional[datetime] = None) -> list[dict]:
    """Các lịch bảo trì cần nhắc NGAY: còn pending, và (gần tới ngày hẹn theo
    remind_days_before) HOẶC (gần tới km hẹn theo remind_km_before) — cái nào
    tới trước cũng kích hoạt. Bỏ qua nếu đã nhắc trong 24h gần nhất."""
    now = now or datetime.now(timezone.utc)
    due = []
    for m in list_maintenance():
        if m.get("status") != "pending":
            continue
        last = m.get("last_reminded_at")
        if last:
            last_dt = last if hasattr(last, "tzinfo") else None
            if last_dt and now - last_dt < timedelta(hours=24):
                continue

        near_by_date = False
        scheduled = m.get("scheduled_date")
        if scheduled:
            days_left = (scheduled - now).total_seconds() / 86400
            near_by_date = days_left <= m.get("remind_days_before", 7)

        near_by_km = False
        due_km = m.get("due_odometer_km")
        if due_km is not None:
            vehicle = vehicle_service.get_vehicle(m["vehicle_id"])
            current_km = (vehicle or {}).get("current_odometer_km")
            if current_km is not None:
                km_left = due_km - current_km
                near_by_km = km_left <= m.get("remind_km_before", 500)

        if near_by_date or near_by_km:
            due.append(m)
    return due


def run_auto_reminders() -> list[dict]:
    """Gửi nhắc cho tất cả lịch bảo trì tới hạn, trả log từng cái để debug/test."""
    results = []
    for m in due_for_auto_reminder():
        result = notify_maintenance(m["id"])
        results.append({"maintenance_id": m["id"], **result})
    return results
