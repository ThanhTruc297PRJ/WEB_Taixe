"""Tổng hợp các việc cần admin chú ý — phục vụ chuông thông báo trên web admin.

Gom 6 nguồn: tài xế chờ duyệt, bảo trì sắp tới hạn, đăng kiểm sắp tới hạn, sự
cố an toàn gần đây, báo cáo từ tài xế, bài hát bị báo cáo. Mỗi nguồn trả {count, items} — items
giới hạn _ITEM_LIMIT bản ghi để payload nhẹ, count là tổng số thật (hiển thị
trên badge)."""

from app.services import (
    driver_report_service,
    driver_service,
    incident_service,
    inspection_service,
    maintenance_service,
    music_service,
    vehicle_job_service,
    vehicle_service,
)
from app.services.maintenance_service import _TYPE_LABELS as _MAINTENANCE_TYPE_LABELS

_ITEM_LIMIT = 5
_INCIDENT_WINDOW_HOURS = 24


def _pending_drivers() -> dict:
    pending = [d for d in driver_service.list_drivers() if d.get("status") == "pending"]

    def sort_key(d: dict):
        submitted = d.get("submitted_at")
        ts = submitted.timestamp() if hasattr(submitted, "timestamp") else 0
        # Đã xác thực email (sẵn sàng duyệt ngay) lên trước, rồi tới mới nhất.
        return (0 if d.get("email_verified") else 1, -ts)

    pending.sort(key=sort_key)
    items = [
        {
            "id": d["id"],
            "name": d.get("name"),
            "email_verified": bool(d.get("email_verified")),
            "submitted_at": d.get("submitted_at"),
        }
        for d in pending[:_ITEM_LIMIT]
    ]
    return {"count": len(pending), "items": items}


def _maintenance_due() -> dict:
    due = maintenance_service.list_upcoming()
    items = []
    for m in due[:_ITEM_LIMIT]:
        vehicle = vehicle_service.get_vehicle(m.get("vehicle_id"))
        items.append(
            {
                "id": m["id"],
                "vehicle_id": m.get("vehicle_id"),
                # Biển số + nhãn loại bảo trì đã dịch — web chỉ hiển thị thẳng,
                # không tự tra cứu/dịch lại (tránh hiện raw id/enum kiểu
                # "oil_change" hay chuỗi document id dài ngoằng ngoài UI).
                "plate_number": (vehicle or {}).get("plate_number"),
                "type": m.get("type"),
                "type_label": _MAINTENANCE_TYPE_LABELS.get(m.get("type"), m.get("type")),
                "scheduled_date": m.get("scheduled_date"),
                "due_odometer_km": m.get("due_odometer_km"),
            }
        )
    return {"count": len(due), "items": items}


def _inspections_due() -> dict:
    due = inspection_service.list_upcoming()
    items = []
    for i in due[:_ITEM_LIMIT]:
        vehicle = vehicle_service.get_vehicle(i.get("vehicle_id"))
        items.append(
            {
                "id": i["id"],
                "vehicle_id": i.get("vehicle_id"),
                "plate_number": (vehicle or {}).get("plate_number"),
                "station": i.get("station"),
                "old_sticker_expiry": i.get("old_sticker_expiry"),
            }
        )
    return {"count": len(due), "items": items}


def _recent_incidents() -> dict:
    recent = incident_service.list_recent(hours=_INCIDENT_WINDOW_HOURS)
    items = [
        {
            "id": i["id"],
            "driver_id": i.get("driver_id"),
            "type": i.get("type"),
            "points": i.get("points"),
            "detected_at": i.get("detected_at"),
        }
        for i in recent[:_ITEM_LIMIT]
    ]
    return {"count": len(recent), "items": items}


def _driver_reports() -> dict:
    new = driver_report_service.list_new()
    items = []
    for r in new[:_ITEM_LIMIT]:
        driver = driver_service.get_driver(r.get("driver_id", ""))
        items.append(
            {
                "id": r["id"],
                "name": (driver or {}).get("name"),
                "note": r.get("note"),
                "created_at": r.get("created_at"),
            }
        )
    return {"count": len(new), "items": items}


def _awaiting_confirmation() -> dict:
    """Bảo trì / đăng kiểm tài xế đã báo xong, chờ admin xác nhận."""
    awaiting = vehicle_job_service.list_awaiting()
    items = []
    for j in awaiting[:_ITEM_LIMIT]:
        vehicle = vehicle_service.get_vehicle(j.get("vehicle_id", ""))
        sub = j.get("driver_submission") or {}
        driver = driver_service.get_driver(sub.get("submitted_by", ""))
        is_maintenance = j["kind"] == vehicle_job_service.MAINTENANCE
        items.append(
            {
                "id": j["id"],
                "kind": j["kind"],
                "plate_number": (vehicle or {}).get("plate_number"),
                "type_label": (
                    _MAINTENANCE_TYPE_LABELS.get(j.get("type"), j.get("type"))
                    if is_maintenance
                    else "Đăng kiểm"
                ),
                "driver_name": (driver or {}).get("name"),
                "submitted_at": sub.get("submitted_at"),
            }
        )
    return {"count": len(awaiting), "items": items}


def _reported_music() -> dict:
    # Sắp theo số lượt báo cáo giảm dần -> bài bị nhiều người báo cáo nhất lên
    # đầu danh sách xem trước (quan trọng hơn bài chỉ 1 người báo cáo nhầm).
    reported = sorted(
        music_service.list_reported(),
        key=lambda t: t.get("report_count") or 0,
        reverse=True,
    )
    items = [
        {
            "id": t["id"],
            "title": t.get("title"),
            "artist": t.get("artist"),
            "report_count": t.get("report_count") or 0,
        }
        for t in reported[:_ITEM_LIMIT]
    ]
    return {"count": len(reported), "items": items}


def get_summary() -> dict:
    sections = {
        "pending_drivers": _pending_drivers(),
        "maintenance_due": _maintenance_due(),
        "inspections_due": _inspections_due(),
        "recent_incidents": _recent_incidents(),
        "driver_reports": _driver_reports(),
        "awaiting_confirmation": _awaiting_confirmation(),
        "reported_music": _reported_music(),
    }
    sections["total"] = sum(s["count"] for s in sections.values())
    return sections
