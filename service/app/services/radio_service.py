"""Kênh radio FM cho app tài xế — admin quản lý danh sách trên web.

Trước đây danh sách kênh viết cứng trong app (radio_screen.dart), muốn thêm/bớt
kênh phải ra bản app mới. Giờ lưu ở collection `radio_stations`; app chỉ nhận
các kênh `enabled=True`, sắp theo `order`.

Lần đầu đọc mà collection trống thì tự thêm các kênh mặc định, đánh dấu
ở `app_meta/radio` để admin xoá hết kênh sau này thì không bị thêm lại.
"""

from datetime import datetime, timezone
from typing import Optional

from firebase_admin import firestore

from app.core.firebase import db

COLLECTION = "radio_stations"
_META_DOC = ("app_meta", "radio")

# Link chính thức của các đài — đã kiểm tra phát được 10/2026.
# Link cũ trong app (vov-live.admicro.vn, stream.voh.com.vn) đã ngừng hoạt động.
_DEFAULT_STATIONS = [
    {
        "name": "VOV1 - Thời sự",
        "frequency": "FM 100 MHz",
        "stream_url": "https://str.vov.gov.vn/vovlive/vov1vov5Vietnamese.sdp_aac/playlist.m3u8",
    },
    {
        "name": "VOV3 - Âm nhạc",
        "frequency": "FM 102.7 MHz",
        "stream_url": "https://str.vov.gov.vn/vovlive/vov3.sdp_aac/playlist.m3u8",
    },
    {
        "name": "VOV Giao thông Hà Nội",
        "frequency": "FM 91 MHz",
        "stream_url": "https://str.vov.gov.vn/vovlive/vovGTHN.sdp_aac/playlist.m3u8",
    },
    {
        "name": "VOV Giao thông TP.HCM",
        "frequency": "FM 91 MHz",
        "stream_url": "https://str.vov.gov.vn/vovlive/vovGTHCM.sdp_aac/playlist.m3u8",
    },
    {
        "name": "VOV2 - Văn hoá Xã hội",
        "frequency": "FM 96.5 MHz",
        "stream_url": "https://str.vov.gov.vn/vovlive/vov2.sdp_aac/playlist.m3u8",
    },
    {
        "name": "VOV4 - Dân tộc",
        "frequency": "Tiếng các dân tộc",
        "stream_url": "https://audio-lss.vov.vn/live/vov4.m3u8",
    },
    {
        "name": "VOV5 - Đối ngoại",
        "frequency": "FM 105.5 MHz",
        "stream_url": "https://str.vov.gov.vn/vovlive/vov5.sdp_aac/playlist.m3u8",
    },
    {
        "name": "Hải Phòng FM",
        "frequency": "FM 102.2 MHz",
        "stream_url": "https://cdn.thhp.vn/live/285c1421f29d05045909836b37313898e2f/playlist.m3u8",
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed_defaults_once() -> None:
    meta_ref = db.collection(_META_DOC[0]).document(_META_DOC[1])
    if (meta_ref.get().to_dict() or {}).get("seeded"):
        return
    batch = db.batch()
    if not list(db.collection(COLLECTION).limit(1).stream()):
        now = _now()
        for i, station in enumerate(_DEFAULT_STATIONS):
            batch.set(
                db.collection(COLLECTION).document(),
                {
                    **station,
                    "enabled": True,
                    "order": i + 1,
                    "play_count": 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
    batch.set(meta_ref, {"seeded": True}, merge=True)
    batch.commit()


def _sorted(docs) -> list[dict]:
    rows = [{"id": d.id, **(d.to_dict() or {})} for d in docs]
    rows.sort(key=lambda r: (r.get("order", 0), r.get("name", "")))
    return rows


def list_all() -> list[dict]:
    _seed_defaults_once()
    return _sorted(db.collection(COLLECTION).stream())


def list_enabled() -> list[dict]:
    """Shape gọn cho app tài xế."""
    return [
        {
            "id": r["id"],
            "name": r.get("name", ""),
            "frequency": r.get("frequency") or "",
            "streamUrl": r.get("stream_url", ""),
        }
        for r in list_all()
        if r.get("enabled", True)
    ]


def get_station(station_id: str) -> Optional[dict]:
    snap = db.collection(COLLECTION).document(station_id).get()
    return {"id": snap.id, **snap.to_dict()} if snap.exists else None


def create_station(data: dict) -> dict:
    now = _now()
    ref = db.collection(COLLECTION).document()
    ref.set({**data, "play_count": 0, "created_at": now, "updated_at": now})
    return get_station(ref.id)


def update_station(station_id: str, data: dict) -> Optional[dict]:
    ref = db.collection(COLLECTION).document(station_id)
    if not ref.get().exists:
        return None
    ref.update({**data, "updated_at": _now()})
    return get_station(station_id)


def delete_station(station_id: str) -> bool:
    ref = db.collection(COLLECTION).document(station_id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True


def register_play(station_id: str) -> bool:
    """False nếu kênh không còn hoặc đã bị tắt (app hiển thị lỗi, không phát)."""
    ref = db.collection(COLLECTION).document(station_id)
    snap = ref.get()
    if not snap.exists or not (snap.to_dict() or {}).get("enabled", True):
        return False
    ref.update(
        {"play_count": firestore.Increment(1), "last_played_at": _now()}
    )
    return True
