from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_active_driver, get_current_admin
from app.models.music import TrackReport, TrackToggle
from app.services import music_service

# Web admin: xem toàn bộ + bật/tắt bài hát.
router = APIRouter(
    prefix="/music",
    tags=["music (web admin)"],
    dependencies=[Depends(get_current_admin)],
)

# App tài xế: tìm nhạc qua backend, báo phát, báo cáo.
self_router = APIRouter(prefix="/music", tags=["music (app tài xế)"])


# ── App tài xế ───────────────────────────────────────────────────────────
@self_router.get("/search")
def search_music(q: str, _: dict = Depends(get_current_active_driver)):
    """Tìm nhạc iTunes qua backend. Chỉ trả về bài đang được admin cho phép."""
    return music_service.search(q)


@self_router.post("/plays/{track_id}")
def register_play(track_id: str, _: dict = Depends(get_current_active_driver)):
    """App gọi khi bấm phát. 403 nếu bài đã bị tắt (kể cả tắt sau khi tìm)."""
    if not music_service.register_play(track_id):
        raise HTTPException(
            status_code=403, detail="Bài hát này đã bị quản trị viên tắt"
        )
    return {"status": "ok"}


@self_router.post("/tracks/{track_id}/report")
def report_track(
    track_id: str,
    payload: TrackReport,
    _: dict = Depends(get_current_active_driver),
):
    track = music_service.report(track_id, payload.reason)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


# ── Web admin ────────────────────────────────────────────────────────────
@router.get("/tracks")
def list_tracks():
    return music_service.list_tracks()


@router.put("/tracks/{track_id}/toggle")
def toggle_track(
    track_id: str,
    payload: TrackToggle,
    admin: dict = Depends(get_current_admin),
):
    track = music_service.set_enabled(
        track_id, payload.enabled, payload.reason, admin["uid"]
    )
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return track
