import urllib.parse
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.firebase import bucket, db
from app.models.incident import IncidentCreate
from app.services import driver_service, notification_service

COLLECTION = "incidents"

_ALLOWED_TYPES = {"drowsiness", "distraction"}

_INCIDENT_LABELS = {
    "drowsiness": "Phát hiện dấu hiệu buồn ngủ",
    "distraction": "Phát hiện mất tập trung",
}

# Điểm vi phạm mặc định theo loại khi client không gửi kèm.
_DEFAULT_POINTS = {"drowsiness": 10, "distraction": 5}


def create_incident(incident: IncidentCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = incident.model_dump()
    if not data.get("points"):
        data["points"] = _DEFAULT_POINTS.get(incident.type, 5)
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


def _upload_clip(uid: str, data: bytes, content_type: Optional[str]) -> str:
    """Đưa clip lên Firebase Storage kèm download token, trả URL tải qua CDN
    (giống URL Firebase SDK sinh ra). App tài xế KHÔNG ghi thẳng Storage —
    gửi file qua backend, backend upload bằng Admin SDK."""
    if bucket is None:
        raise RuntimeError("Chưa cấu hình FIREBASE_STORAGE_BUCKET")
    ext = "mp4" if content_type and "mp4" in content_type else "bin"
    name = f"incident_clips/{uid}/{uuid.uuid4().hex}.{ext}"
    token = str(uuid.uuid4())
    blob = bucket.blob(name)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(data, content_type=content_type or "video/mp4")
    encoded = urllib.parse.quote(name, safe="")
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
        f"/o/{encoded}?alt=media&token={token}"
    )


def report_from_driver(
    uid: str,
    incident_type: str,
    detected_at: str,
    confidence: Optional[float],
    clip_bytes: bytes,
    content_type: Optional[str],
) -> dict:
    """App tài xế: model phát hiện buồn ngủ -> quay 10s -> gửi lên đây.
    driver_id lấy từ token, không tin client."""
    clip_url = _upload_clip(uid, clip_bytes, content_type)
    try:
        dt = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.now(timezone.utc)
    return create_incident(
        IncidentCreate(
            driver_id=uid,
            type=incident_type if incident_type in _ALLOWED_TYPES else "drowsiness",
            detected_at=dt,
            confidence=confidence,
            clip_url=clip_url,
        )
    )


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


def delete_incident(incident_id: str) -> bool:
    doc_ref = db.collection(COLLECTION).document(incident_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True
