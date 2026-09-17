"""Tổng hợp các việc cần admin chú ý — phục vụ chuông thông báo trên web admin.

Gom 5 nguồn: tài xế chờ duyệt, bảo trì sắp tới hạn, đăng kiểm sắp tới hạn, sự
cố an toàn gần đây, bài hát bị báo cáo. Mỗi nguồn trả {count, items} — items
giới hạn _ITEM_LIMIT bản ghi để payload nhẹ, count là tổng số thật (hiển thị
trên badge)."""

from app.services import (
    driver_service,
    incident_service,
    inspection_service,
    maintenance_service,
    music_service,
)

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
    items = [
        {
            "id": m["id"],
            "vehicle_id": m.get("vehicle_id"),
            "type": m.get("type"),
            "scheduled_date": m.get("scheduled_date"),
            "due_odometer_km": m.get("due_odometer_km"),
        }
        for m in due[:_ITEM_LIMIT]
    ]
    return {"count": len(due), "items": items}


def _inspections_due() -> dict:
    due = inspection_service.list_upcoming()
    items = [
        {
            "id": i["id"],
            "vehicle_id": i.get("vehicle_id"),
            "station": i.get("station"),
            "old_sticker_expiry": i.get("old_sticker_expiry"),
        }
        for i in due[:_ITEM_LIMIT]
    ]
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


def _reported_music() -> dict:
    reported = music_service.list_reported()
    items = [
        {
            "id": t["id"],
            "title": t.get("title"),
            "artist": t.get("artist"),
            "report_count": t.get("report_count"),
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
        "reported_music": _reported_music(),
    }
    sections["total"] = sum(s["count"] for s in sections.values())
    return sections
