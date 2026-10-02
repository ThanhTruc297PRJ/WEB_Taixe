"""Thống kê rủi ro tài xế — tính thẳng từ collection `incidents` trên Firestore.

Trước đây đọc bảng BigQuery `driver_analytics.incidents_raw`, nhưng không có
luồng nào đẩy dữ liệu sang BigQuery nên bảng rỗng/không tồn tại. Quy mô đội xe
hiện tại (vài nghìn sự cố) tính trong RAM chỉ mất vài ms; khi dữ liệu lên hàng
trăm nghìn dòng mới cần cân nhắc BigQuery. Giữ nguyên dạng dữ liệu trả về như
bản BigQuery để bên dùng không phải đổi gì.

"Điểm" (score) = `confidence` của model phát hiện (0..1), sự cố không có
confidence thì vẫn đếm nhưng không tính vào trung bình."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services import incident_service

# Việt Nam không có giờ mùa hè -> offset cố định, khỏi cần gói tzdata trên Windows.
_VN_TZ = timezone(timedelta(hours=7))

_HIGH = 0.8
_MEDIUM = 0.5


def _avg(values: list[float]) -> Optional[float]:
    return round(sum(values) / len(values), 2) if values else None


def _risk_level(avg_score: Optional[float]) -> str:
    if avg_score is None:
        return "LOW"
    if avg_score >= _HIGH:
        return "HIGH"
    if avg_score >= _MEDIUM:
        return "MEDIUM"
    return "LOW"


def get_driver_risk() -> list[dict]:
    count: dict[str, int] = defaultdict(int)
    scores: dict[str, list[float]] = defaultdict(list)
    for incident in incident_service.list_incidents():
        driver_id = incident.get("driver_id")
        if not driver_id:
            continue
        count[driver_id] += 1
        if incident.get("confidence") is not None:
            scores[driver_id].append(float(incident["confidence"]))

    rows = []
    for driver_id, incident_count in count.items():
        avg_score = _avg(scores[driver_id])
        rows.append(
            {
                "driver_id": driver_id,
                "incident_count": incident_count,
                "avg_score": avg_score,
                "risk_level": _risk_level(avg_score),
            }
        )
    rows.sort(key=lambda r: r["avg_score"] if r["avg_score"] is not None else -1, reverse=True)
    return rows


def get_drowsiness_by_hour() -> list[dict]:
    """Giờ tính theo giờ Việt Nam (UTC+7) — Firestore lưu UTC."""
    count: dict[int, int] = defaultdict(int)
    scores: dict[int, list[float]] = defaultdict(list)
    for incident in incident_service.list_incidents():
        detected_at = incident.get("detected_at")
        if not isinstance(detected_at, datetime):
            continue
        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(tzinfo=timezone.utc)
        hour = detected_at.astimezone(_VN_TZ).hour
        count[hour] += 1
        if incident.get("confidence") is not None:
            scores[hour].append(float(incident["confidence"]))

    return [
        {
            "hour": hour,
            "total_incidents": count[hour],
            "avg_score": _avg(scores[hour]),
        }
        for hour in sorted(count)
    ]
