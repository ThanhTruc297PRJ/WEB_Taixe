from typing import Optional

from app.core.firebase import db
from app.models.incident import IncidentCreate
from app.services import driver_service, notification_service

COLLECTION = "incidents"

_INCIDENT_LABELS = {
    "drowsiness": "Phát hiện dấu hiệu buồn ngủ",
    "distraction": "Phát hiện mất tập trung",
}


def create_incident(incident: IncidentCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = incident.model_dump()
    doc_ref.set(data)
    result = {"id": doc_ref.id, **data}

    driver = driver_service.get_driver(incident.driver_id)
    if driver and driver.get("fcm_token"):
        try:
            notification_service.send_push(
                token=driver["fcm_token"],
                title="Cảnh báo an toàn",
                body=_INCIDENT_LABELS.get(incident.type, incident.type),
                data={"incident_id": doc_ref.id, "type": incident.type},
            )
        except Exception:
            # Incident đã được ghi thành công; lỗi gửi push (token hết hạn,
            # thiết bị offline...) không nên làm fail request tạo incident.
            pass
    return result


def get_incident(incident_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(incident_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_incidents(driver_id: Optional[str] = None) -> list[dict]:
    query = db.collection(COLLECTION)
    if driver_id:
        query = query.where("driver_id", "==", driver_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]
