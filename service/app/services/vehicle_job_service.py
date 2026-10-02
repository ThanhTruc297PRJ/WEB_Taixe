"""Tài xế báo đã làm xong bảo trì / đăng kiểm -> admin xác nhận trên web.

Một lịch bảo trì (`maintenance_schedules`) hoặc hồ sơ đăng kiểm
(`vehicle_inspections`) đi qua các trạng thái:

    pending ──(tài xế gửi ảnh + số km + chi phí)──> awaiting_confirmation
    awaiting_confirmation ──(admin Xác nhận)──> done
    awaiting_confirmation ──(admin Trả lại + lý do)──> pending

Chỉ khi admin xác nhận thì lịch mới tính là đã xong: số liệu tài xế gửi mới
được ghi vào lịch (chi phí -> Báo cáo chi phí), số km xe mới được cập nhật, và
đăng kiểm Đạt mới sinh hồ sơ kỳ tiếp theo. Lịch đang chờ xác nhận không bị
nhắc tự động nữa (các hàm nhắc chỉ xét status == "pending").
"""

import urllib.parse
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.firebase import bucket, db
from app.services import (
    driver_service,
    inspection_service,
    maintenance_service,
    vehicle_service,
)
from app.services.websocket_manager import manager

ADMIN_ROOM = "admin"

MAINTENANCE = "maintenance"
INSPECTION = "inspection"
KINDS = (MAINTENANCE, INSPECTION)

PENDING = "pending"
AWAITING = "awaiting_confirmation"
DONE = "done"

_COLLECTIONS = {
    MAINTENANCE: maintenance_service.COLLECTION,
    INSPECTION: inspection_service.COLLECTION,
}
_RESULT_LABELS = {"passed": "Đạt", "failed": "Không đạt"}


class JobError(Exception):
    """Lỗi nghiệp vụ có thông báo hiển thị thẳng cho người dùng."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get(kind: str, job_id: str) -> Optional[dict]:
    if kind == MAINTENANCE:
        return maintenance_service.get_maintenance(job_id)
    return inspection_service.get_inspection(job_id)


def _update(kind: str, job_id: str, data: dict) -> Optional[dict]:
    if kind == MAINTENANCE:
        return maintenance_service.update_maintenance(job_id, data)
    return inspection_service.update_inspection(job_id, data)


def _title(kind: str, job: dict) -> str:
    if kind == MAINTENANCE:
        return maintenance_service._TYPE_LABELS.get(job.get("type"), job.get("type") or "Bảo trì")
    return "Đăng kiểm"


def _responsible_driver(job: dict, vehicle: Optional[dict]) -> Optional[str]:
    """Người phụ trách riêng cho lần này; không có thì tài xế đang lái xe đó."""
    return job.get("driver_id") or (vehicle or {}).get("driver_id")


def _upload_proof(uid: str, data: bytes, content_type: Optional[str]) -> str:
    if bucket is None:
        raise JobError(503, "Chưa cấu hình FIREBASE_STORAGE_BUCKET")
    ext = "png" if content_type == "image/png" else "jpg"
    name = f"job_proofs/{uid}/{uuid.uuid4().hex}.{ext}"
    token = str(uuid.uuid4())
    blob = bucket.blob(name)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(data, content_type=content_type or "image/jpeg")
    encoded = urllib.parse.quote(name, safe="")
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
        f"/o/{encoded}?alt=media&token={token}"
    )


def _to_driver_shape(kind: str, job: dict, vehicle: Optional[dict]) -> dict:
    """Shape gọn cho app tài xế — gộp bảo trì và đăng kiểm vào 1 danh sách."""
    return {
        "kind": kind,
        "id": job["id"],
        "vehicle_id": job.get("vehicle_id"),
        "plate_number": (vehicle or {}).get("plate_number"),
        "current_odometer_km": (vehicle or {}).get("current_odometer_km"),
        "title": _title(kind, job),
        "due_date": job.get("scheduled_date") if kind == MAINTENANCE else job.get("old_sticker_expiry"),
        "due_odometer_km": job.get("due_odometer_km") if kind == MAINTENANCE else None,
        "place": job.get("vendor") if kind == MAINTENANCE else job.get("station"),
        "appointment_at": job.get("appointment_at") if kind == INSPECTION else None,
        "status": job.get("status", PENDING),
        "rejection": job.get("rejection"),
        "submission": job.get("driver_submission"),
    }


# ── App tài xế ───────────────────────────────────────────────────────────
def list_for_driver(uid: str) -> list[dict]:
    """Lịch chưa xong mà tài xế này phụ trách (riêng cho lần đó, hoặc qua xe
    đang được gán). Sắp theo hạn gần nhất."""
    my_vehicles = {v["id"]: v for v in vehicle_service.list_vehicles(driver_id=uid)}
    vehicle_cache: dict[str, Optional[dict]] = dict(my_vehicles)

    def vehicle_of(vehicle_id: str) -> Optional[dict]:
        if vehicle_id not in vehicle_cache:
            vehicle_cache[vehicle_id] = vehicle_service.get_vehicle(vehicle_id)
        return vehicle_cache[vehicle_id]

    rows = []
    sources = [
        (MAINTENANCE, maintenance_service.list_maintenance()),
        (INSPECTION, inspection_service.list_inspections()),
    ]
    for kind, jobs in sources:
        for job in jobs:
            if job.get("status", PENDING) not in (PENDING, AWAITING):
                continue
            vehicle = vehicle_of(job.get("vehicle_id", ""))
            if _responsible_driver(job, vehicle) != uid:
                continue
            rows.append(_to_driver_shape(kind, job, vehicle))

    far_future = datetime.max.replace(tzinfo=timezone.utc)
    rows.sort(key=lambda r: r["due_date"] if isinstance(r["due_date"], datetime) else far_future)
    return rows


def submit(
    kind: str,
    job_id: str,
    uid: str,
    *,
    photo_bytes: bytes,
    content_type: Optional[str],
    odometer: int,
    note: str = "",
    cost: Optional[float] = None,
    inspection_fee: Optional[float] = None,
    road_fee: Optional[float] = None,
    result: Optional[str] = None,
    new_sticker_expiry: Optional[datetime] = None,
) -> dict:
    job = _get(kind, job_id)
    if job is None:
        raise JobError(404, "Không tìm thấy lịch này")
    vehicle = vehicle_service.get_vehicle(job.get("vehicle_id", ""))
    if _responsible_driver(job, vehicle) != uid:
        raise JobError(403, "Bạn không phụ trách lịch này")
    status = job.get("status", PENDING)
    if status == AWAITING:
        raise JobError(409, "Lịch này đã gửi, đang chờ quản lý xác nhận")
    if status != PENDING:
        raise JobError(409, "Lịch này đã hoàn tất")

    current_km = (vehicle or {}).get("current_odometer_km")
    if current_km is not None and odometer < current_km:
        raise JobError(
            422, f"Số km nhỏ hơn số km hiện tại của xe ({current_km:,} km)".replace(",", ".")
        )

    submission = {
        "odometer": odometer,
        "note": note or None,
        "submitted_by": uid,
        "submitted_at": _now(),
    }
    if kind == MAINTENANCE:
        if cost is None:
            raise JobError(422, "Nhập chi phí bảo trì")
        submission["cost"] = cost
    else:
        if result not in _RESULT_LABELS:
            raise JobError(422, "Chọn kết quả đăng kiểm (Đạt / Không đạt)")
        if inspection_fee is None:
            raise JobError(422, "Nhập phí kiểm định")
        if result == "passed" and new_sticker_expiry is None:
            raise JobError(422, "Đăng kiểm Đạt cần nhập ngày hết hạn tem mới")
        submission.update(
            {
                "result": result,
                "inspection_fee": inspection_fee,
                "road_fee": road_fee,
                "new_sticker_expiry": new_sticker_expiry if result == "passed" else None,
            }
        )

    submission["photo_url"] = _upload_proof(uid, photo_bytes, content_type)
    updated = _update(
        kind, job_id, {"status": AWAITING, "driver_submission": submission, "rejection": None}
    )
    return _to_driver_shape(kind, updated, vehicle)


async def broadcast_submitted(kind: str, job: dict, uid: str) -> None:
    """Báo web admin có lịch cần xác nhận (chuông tự cập nhật). Best-effort."""
    try:
        driver = driver_service.get_driver(uid)
        await manager.broadcast_to_room(
            ADMIN_ROOM,
            {
                "type": "job_submitted",
                "kind": kind,
                "job_id": job.get("id"),
                "title": job.get("title"),
                "plate_number": job.get("plate_number"),
                "driver_name": (driver or {}).get("name"),
            },
        )
    except Exception:
        pass


# ── Web admin ────────────────────────────────────────────────────────────
def list_awaiting() -> list[dict]:
    """Lịch đang chờ admin xác nhận — cho chuông thông báo. Cũ nhất lên đầu."""
    rows = []
    for kind, collection in _COLLECTIONS.items():
        docs = db.collection(collection).where("status", "==", AWAITING).stream()
        for d in docs:
            rows.append({"kind": kind, "id": d.id, **d.to_dict()})
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    rows.sort(key=lambda r: (r.get("driver_submission") or {}).get("submitted_at") or oldest)
    return rows


def _require_awaiting(kind: str, job_id: str) -> dict:
    job = _get(kind, job_id)
    if job is None:
        raise JobError(404, "Không tìm thấy lịch này")
    if job.get("status") != AWAITING or not job.get("driver_submission"):
        raise JobError(409, "Lịch này không ở trạng thái chờ xác nhận")
    return job


def confirm(kind: str, job_id: str, admin_uid: str) -> dict:
    job = _require_awaiting(kind, job_id)
    sub = job["driver_submission"]
    confirmed = {"confirmed_by": admin_uid, "confirmed_at": _now()}
    next_job = None

    if kind == MAINTENANCE:
        updated = _update(
            kind,
            job_id,
            {
                "status": DONE,
                "odometer": sub.get("odometer"),
                "cost": sub.get("cost"),
                **confirmed,
            },
        )
    else:
        _update(
            kind,
            job_id,
            {
                "inspection_fee": sub.get("inspection_fee"),
                "road_fee": sub.get("road_fee"),
                **confirmed,
            },
        )
        completed = inspection_service.complete_inspection(
            job_id, sub.get("result"), sub.get("new_sticker_expiry")
        )
        updated = completed["closed"]
        next_job = completed["next"]

    vehicle = vehicle_service.get_vehicle(job.get("vehicle_id", ""))
    odometer = sub.get("odometer")
    if vehicle and odometer is not None and odometer > (vehicle.get("current_odometer_km") or 0):
        vehicle_service.update_vehicle(vehicle["id"], {"current_odometer_km": odometer})

    _notify_driver(
        sub.get("submitted_by"),
        title="Quản lý đã xác nhận",
        body=f"{_title(kind, job)} xe {(vehicle or {}).get('plate_number', '')} đã được xác nhận hoàn tất",
        data={"kind": kind, "job_id": job_id},
    )
    return {"job": updated, "next": next_job}


def reject(kind: str, job_id: str, admin_uid: str, reason: str) -> dict:
    job = _require_awaiting(kind, job_id)
    sub = job["driver_submission"]
    updated = _update(
        kind,
        job_id,
        {
            "status": PENDING,
            "driver_submission": None,
            "rejection": {
                "reason": reason,
                "rejected_by": admin_uid,
                "rejected_at": _now(),
                "submission": sub,
            },
        },
    )
    vehicle = vehicle_service.get_vehicle(job.get("vehicle_id", ""))
    _notify_driver(
        sub.get("submitted_by"),
        title="Quản lý trả lại báo cáo",
        body=f"{_title(kind, job)} xe {(vehicle or {}).get('plate_number', '')}: {reason}",
        data={"kind": kind, "job_id": job_id},
    )
    return updated


def _notify_driver(uid: Optional[str], title: str, body: str, data: dict) -> None:
    """Push FCM best-effort: tài xế chưa có token thì vẫn thấy khi mở app."""
    try:
        maintenance_service._push_to_driver(uid, title, body, data)
    except Exception:
        pass
