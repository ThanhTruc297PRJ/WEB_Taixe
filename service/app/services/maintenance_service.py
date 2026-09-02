from typing import Optional

from app.core.firebase import db
from app.models.maintenance import MaintenanceCreate
from app.services import driver_service, notification_service, vehicle_service

COLLECTION = "maintenance_schedules"

_TYPE_LABELS = {
    "oil_change": "Thay dầu",
    "tire": "Kiểm tra/thay lốp",
    "inspection": "Đăng kiểm",
    "other": "Bảo trì khác",
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


def notify_maintenance(maintenance_id: str) -> dict:
    """Gửi FCM nhắc lịch bảo trì tới tài xế đang phụ trách xe.

    Trả về {"sent": bool, "reason": str} — không raise để route trả 200 kèm
    lý do (không có token / chưa gán tài xế...) cho UI hiển thị.
    """
    maintenance = get_maintenance(maintenance_id)
    if maintenance is None:
        return {"sent": False, "reason": "maintenance_not_found"}

    vehicle = vehicle_service.get_vehicle(maintenance["vehicle_id"])
    if vehicle is None:
        return {"sent": False, "reason": "vehicle_not_found"}

    driver_id = vehicle.get("driver_id")
    driver = driver_service.get_driver(driver_id) if driver_id else None
    if not driver or not driver.get("fcm_token"):
        return {"sent": False, "reason": "driver_has_no_fcm_token"}

    scheduled = maintenance["scheduled_date"]
    when = scheduled.strftime("%d/%m/%Y") if hasattr(scheduled, "strftime") else str(scheduled)
    label = _TYPE_LABELS.get(maintenance["type"], maintenance["type"])

    try:
        notification_service.send_push(
            token=driver["fcm_token"],
            title="Nhắc lịch bảo trì xe",
            body=f"Xe {vehicle.get('plate_number', '')}: {label} — hạn {when}",
            data={
                "maintenance_id": maintenance_id,
                "vehicle_id": maintenance["vehicle_id"],
            },
        )
    except Exception as e:
        return {"sent": False, "reason": f"push_failed: {e}"}
    return {"sent": True, "reason": "ok"}
