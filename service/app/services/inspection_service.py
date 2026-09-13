"""Đăng kiểm xe — tách riêng khỏi bảo trì (TASK-C10).

Khác bảo trì ở chỗ: gắn trạm + khung giờ hẹn cụ thể, nhắc tính từ NGÀY HẾT HẠN
TEM CŨ (không phải ngày hẹn — tránh phải tự nhớ đặt lịch sớm), và lưu riêng
2 khoản phí (kiểm định + bảo trì đường bộ) để sau này tổng hợp báo cáo ngân
sách bảo trì xe.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.firebase import db
from app.models.inspection import InspectionCreate
from app.services import driver_service, notification_service, vehicle_service

COLLECTION = "vehicle_inspections"

_RESULTS = {"passed", "failed"}


def create_inspection(inspection: InspectionCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = inspection.model_dump()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def get_inspection(inspection_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(inspection_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_inspections(vehicle_id: Optional[str] = None) -> list[dict]:
    query = db.collection(COLLECTION)
    if vehicle_id:
        query = query.where("vehicle_id", "==", vehicle_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def update_inspection(inspection_id: str, data: dict) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(inspection_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(data)
    return {"id": inspection_id, **doc_ref.get().to_dict()}


def delete_inspection(inspection_id: str) -> bool:
    doc_ref = db.collection(COLLECTION).document(inspection_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


def complete_inspection(
    inspection_id: str, result: str, new_sticker_expiry: Optional[datetime]
) -> Optional[dict]:
    """Đóng hồ sơ đăng kiểm kèm kết quả. Nếu Đạt và có ngày hết hạn tem mới ->
    tự sinh hồ sơ kỳ tiếp theo (status=pending, chưa đặt khung giờ hẹn) để
    admin không phải tự nhớ tạo lại. Trả {"closed": {...}, "next": {...}|None}.
    """
    inspection = get_inspection(inspection_id)
    if inspection is None:
        return None
    result = result if result in _RESULTS else "failed"

    closed = update_inspection(
        inspection_id, {"status": "done", "result": result}
    )

    next_inspection = None
    if result == "passed" and new_sticker_expiry is not None:
        next_inspection = create_inspection(
            InspectionCreate(
                vehicle_id=inspection["vehicle_id"],
                driver_id=inspection.get("driver_id"),
                station=inspection.get("station", ""),
                appointment_at=None,
                old_sticker_expiry=new_sticker_expiry,
                remind_days_before=inspection.get("remind_days_before", 15),
            )
        )

    return {"closed": closed, "next": next_inspection}


def notify_inspection(inspection_id: str) -> dict:
    """Nhắc thủ công (nút "Gửi nhắc" trên web). Ưu tiên gửi cho người phụ
    trách đăng kiểm (driver_id trên hồ sơ); không có thì gửi cho tài xế đang
    phụ trách xe."""
    inspection = get_inspection(inspection_id)
    if inspection is None:
        return {"sent": False, "reason": "inspection_not_found"}

    vehicle = vehicle_service.get_vehicle(inspection["vehicle_id"])
    if vehicle is None:
        return {"sent": False, "reason": "vehicle_not_found"}

    driver_id = inspection.get("driver_id") or vehicle.get("driver_id")
    driver = driver_service.get_driver(driver_id) if driver_id else None
    if not driver or not driver.get("fcm_token"):
        return {"sent": False, "reason": "driver_has_no_fcm_token"}

    expiry = inspection["old_sticker_expiry"]
    when = expiry.strftime("%d/%m/%Y") if hasattr(expiry, "strftime") else str(expiry)

    try:
        notification_service.send_push(
            token=driver["fcm_token"],
            title="Nhắc lịch đăng kiểm xe",
            body=(
                f"Xe {vehicle.get('plate_number', '')}: tem hết hạn {when} — "
                f"hẹn tại {inspection.get('station', '')}"
            ),
            data={"inspection_id": inspection_id, "vehicle_id": inspection["vehicle_id"]},
        )
    except Exception as e:
        return {"sent": False, "reason": f"push_failed: {e}"}

    update_inspection(inspection_id, {"last_reminded_at": datetime.now(timezone.utc)})
    return {"sent": True, "reason": "ok"}


def due_for_auto_reminder(now: Optional[datetime] = None) -> list[dict]:
    """Đăng kiểm cần nhắc NGAY: còn pending và ngày hết hạn tem đã tới trong
    vòng remind_days_before. Bỏ qua nếu đã nhắc trong 24h gần nhất."""
    now = now or datetime.now(timezone.utc)
    due = []
    for insp in list_inspections():
        if insp.get("status") != "pending":
            continue
        last = insp.get("last_reminded_at")
        if last and hasattr(last, "tzinfo") and now - last < timedelta(hours=24):
            continue
        expiry = insp.get("old_sticker_expiry")
        if not expiry:
            continue
        days_left = (expiry - now).total_seconds() / 86400
        if days_left <= insp.get("remind_days_before", 15):
            due.append(insp)
    return due


def run_auto_reminders() -> list[dict]:
    results = []
    for insp in due_for_auto_reminder():
        result = notify_inspection(insp["id"])
        results.append({"inspection_id": insp["id"], **result})
    return results
