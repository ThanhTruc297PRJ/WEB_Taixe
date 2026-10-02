"""Báo cáo tài xế tự gửi từ app (xe hỏng, va quẹt, sự cố dọc đường...) kèm
mô tả + ảnh tuỳ chọn.

Tách riêng khỏi `incidents`: incidents là vi phạm an toàn do model phát hiện
và bị TÍNH ĐIỂM VI PHẠM; báo cáo ở đây không phải lỗi của tài xế nên không
được lẫn vào điểm phạt / thống kê vi phạm."""

import urllib.parse
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.firebase import bucket, db
from app.services import driver_service
from app.services.websocket_manager import manager

COLLECTION = "driver_reports"
ADMIN_ROOM = "admin"


def _upload_photo(uid: str, data: bytes, content_type: Optional[str]) -> str:
    if bucket is None:
        raise RuntimeError("Chưa cấu hình FIREBASE_STORAGE_BUCKET")
    ext = "png" if content_type == "image/png" else "jpg"
    name = f"driver_reports/{uid}/{uuid.uuid4().hex}.{ext}"
    token = str(uuid.uuid4())
    blob = bucket.blob(name)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(data, content_type=content_type or "image/jpeg")
    encoded = urllib.parse.quote(name, safe="")
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
        f"/o/{encoded}?alt=media&token={token}"
    )


def create_report(
    uid: str,
    note: str,
    photo_bytes: Optional[bytes],
    content_type: Optional[str],
) -> dict:
    photo_url = _upload_photo(uid, photo_bytes, content_type) if photo_bytes else None
    data = {
        "driver_id": uid,
        "note": note,
        "photo_url": photo_url,
        "status": "new",  # "new" | "resolved"
        "created_at": datetime.now(timezone.utc),
        "resolved_at": None,
        "resolved_by": None,
    }
    doc_ref = db.collection(COLLECTION).document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def list_reports() -> list[dict]:
    docs = db.collection(COLLECTION).stream()
    reports = [{"id": d.id, **d.to_dict()} for d in docs]
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    reports.sort(key=lambda r: r.get("created_at") or oldest, reverse=True)
    return reports


def list_new() -> list[dict]:
    return [r for r in list_reports() if r.get("status") == "new"]


def resolve_report(report_id: str, admin_uid: str) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(report_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(
        {
            "status": "resolved",
            "resolved_at": datetime.now(timezone.utc),
            "resolved_by": admin_uid,
        }
    )
    return {"id": report_id, **doc_ref.get().to_dict()}


def delete_by_driver(driver_id: str) -> int:
    docs = list(db.collection(COLLECTION).where("driver_id", "==", driver_id).stream())
    for d in docs:
        d.reference.delete()
    return len(docs)


async def broadcast_report(report: dict) -> None:
    """Báo web admin có báo cáo mới (chuông tự cập nhật). Best-effort."""
    try:
        driver = driver_service.get_driver(report.get("driver_id", ""))
        await manager.broadcast_to_room(
            ADMIN_ROOM,
            {
                "type": "driver_report",
                "report_id": report.get("id"),
                "driver_id": report.get("driver_id"),
                "driver_name": (driver or {}).get("name"),
                "note": report.get("note"),
            },
        )
    except Exception:
        pass
