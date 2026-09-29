"""Nhạc giải trí cho tài xế — có kiểm duyệt từ web admin.

Luồng: app KHÔNG gọi thẳng iTunes nữa mà gọi `GET /music/search`. Backend tìm
hộ trên iTunes, lưu mỗi bài vào collection `music_tracks` (doc id = trackId),
rồi CHỈ trả về những bài `enabled=True`. Admin xem toàn bộ danh sách trên web
và gạt tắt bài không cho nghe; bài `explicit` bị tắt sẵn.
"""

from datetime import datetime, timezone
from typing import Optional

import httpx

from firebase_admin import firestore

from app.core.firebase import db

COLLECTION = "music_tracks"
_ITUNES_URL = "https://itunes.apple.com/search"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_song(doc_dict: dict, track_id: str) -> dict:
    """Shape gọn cho app tài xế."""
    return {
        "id": track_id,
        "title": doc_dict.get("title", ""),
        "artist": doc_dict.get("artist", ""),
        "audioUrl": doc_dict.get("preview_url", ""),
        "artworkUrl": doc_dict.get("artwork_url"),
    }


def search(query: str) -> list[dict]:
    """Tìm trên iTunes, cập nhật `music_tracks`, trả về các bài đang bật."""
    query = (query or "").strip()
    if not query:
        return []

    try:
        resp = httpx.get(
            _ITUNES_URL,
            params={"term": query, "media": "music", "limit": 25},
            timeout=10.0,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except (httpx.HTTPError, ValueError):
        return []

    items = [r for r in results if r.get("previewUrl") and r.get("trackId")]
    if not items:
        return []

    refs = [db.collection(COLLECTION).document(str(r["trackId"])) for r in items]
    existing = {snap.id: snap for snap in db.get_all(refs)}

    batch = db.batch()
    songs: list[dict] = []
    for r in items:
        track_id = str(r["trackId"])
        ref = db.collection(COLLECTION).document(track_id)
        explicit = r.get("trackExplicitness") == "explicit"
        meta = {
            "title": r.get("trackName") or "Không rõ tiêu đề",
            "artist": r.get("artistName") or "Không rõ ca sĩ",
            "preview_url": r["previewUrl"],
            "artwork_url": r.get("artworkUrl100"),
            "explicit": explicit,
        }
        snap = existing.get(track_id)
        if snap is not None and snap.exists:
            current = snap.to_dict() or {}
            batch.update(ref, meta)
            enabled = current.get("enabled", True)
            merged = {**current, **meta}
        else:
            enabled = not explicit
            merged = {
                **meta,
                "enabled": enabled,
                "source": "itunes",
                "disabled_reason": (
                    "Nội dung explicit (tự động tắt)" if explicit else None
                ),
                "disabled_by": None,
                "disabled_at": _now() if explicit else None,
                "play_count": 0,
                "report_count": 0,
                "reported": False,
                "last_report_reason": None,
                "first_seen_at": _now(),
                "last_played_at": None,
            }
            batch.set(ref, merged)
        if enabled:
            songs.append(_to_song(merged, track_id))

    batch.commit()
    return songs


def list_tracks() -> list[dict]:
    """Toàn bộ bài hát (kể cả đã tắt) — cho web admin."""
    return [
        {"id": doc.id, **doc.to_dict()}
        for doc in db.collection(COLLECTION).stream()
    ]


def set_enabled(
    track_id: str, enabled: bool, reason: Optional[str], admin_uid: str
) -> Optional[dict]:
    ref = db.collection(COLLECTION).document(track_id)
    if not ref.get().exists:
        return None
    ref.update(
        {
            "enabled": enabled,
            "disabled_reason": None if enabled else (reason or "Quản trị viên tắt"),
            "disabled_by": None if enabled else admin_uid,
            "disabled_at": None if enabled else _now(),
        }
    )
    return {"id": track_id, **ref.get().to_dict()}


def register_play(track_id: str) -> bool:
    """App gọi khi tài xế bấm phát. Trả False nếu bài đã bị tắt / không tồn tại
    (route -> 403) để chặn cả trường hợp bài bị tắt sau khi tài xế đã tìm."""
    ref = db.collection(COLLECTION).document(track_id)
    snap = ref.get()
    if not snap.exists or snap.to_dict().get("enabled") is False:
        return False
    ref.update(
        {
            "play_count": firestore.Increment(1),
            "last_played_at": _now(),
        }
    )
    return True


def list_reported() -> list[dict]:
    """Bài hát bị tài xế báo cáo, chờ admin xem xét — cho chuông thông báo web."""
    return [t for t in list_tracks() if t.get("reported")]


def report(track_id: str, reason: Optional[str], driver_id: str) -> Optional[dict]:
    """Tài xế báo cáo bài hát không phù hợp — vừa cộng dồn số liệu trên track
    (cho hiển thị nhanh ở bảng), vừa lưu riêng từng lượt báo cáo (ai báo, lúc
    nào, lý do gì) vào subcollection để admin xem lại chi tiết."""
    ref = db.collection(COLLECTION).document(track_id)
    if not ref.get().exists:
        return None
    ref.update(
        {
            "reported": True,
            "report_count": firestore.Increment(1),
            "last_report_reason": reason,
        }
    )
    ref.collection("reports").document().set(
        {"driver_id": driver_id, "reason": reason, "reported_at": _now()}
    )
    return {"id": track_id, **ref.get().to_dict()}


def list_track_reports(track_id: str) -> list[dict]:
    """Chi tiết từng lượt báo cáo của 1 bài hát — mới nhất trước."""
    docs = (
        db.collection(COLLECTION)
        .document(track_id)
        .collection("reports")
        .order_by("reported_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]
