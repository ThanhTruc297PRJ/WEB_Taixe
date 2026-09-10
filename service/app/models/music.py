from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MusicTrack(BaseModel):
    """Một bài hát đã từng xuất hiện trong app (tài xế tìm hoặc nghe).

    Doc id = iTunes trackId. `enabled=False` -> tài xế không tìm/nghe được nữa.
    """

    id: str
    title: str
    artist: str
    preview_url: str
    artwork_url: Optional[str] = None
    explicit: bool = False
    enabled: bool = True
    source: str = "itunes"
    disabled_reason: Optional[str] = None
    disabled_by: Optional[str] = None
    disabled_at: Optional[datetime] = None
    play_count: int = 0
    report_count: int = 0
    reported: bool = False
    last_report_reason: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_played_at: Optional[datetime] = None


class TrackToggle(BaseModel):
    enabled: bool
    reason: Optional[str] = None


class TrackReport(BaseModel):
    reason: Optional[str] = None
