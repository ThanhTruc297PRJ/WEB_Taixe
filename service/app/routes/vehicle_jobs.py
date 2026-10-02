from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.security import get_current_active_driver, get_current_admin
from app.services import vehicle_job_service as jobs

# Tài xế báo đã bảo trì / đăng kiểm xong -> admin xác nhận hoặc trả lại.
router = APIRouter(
    prefix="/vehicle-jobs",
    tags=["vehicle jobs (web admin)"],
    dependencies=[Depends(get_current_admin)],
)
self_router = APIRouter(prefix="/vehicle-jobs", tags=["vehicle jobs (app tài xế)"])

_MAX_PHOTO_BYTES = 10 * 1024 * 1024
_MAX_NOTE_CHARS = 1000


def _check_kind(kind: str) -> None:
    if kind not in jobs.KINDS:
        raise HTTPException(status_code=404, detail="Loại lịch không hợp lệ")


def _http(e: jobs.JobError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


# ── App tài xế ───────────────────────────────────────────────────────────
@self_router.get("/mine")
def my_jobs(user: dict = Depends(get_current_active_driver)):
    """Bảo trì + đăng kiểm chưa xong mà tài xế này phụ trách."""
    return jobs.list_for_driver(user["uid"])


@self_router.post("/{kind}/{job_id}/submit")
async def submit_job(
    kind: str,
    job_id: str,
    photo: UploadFile = File(...),
    odometer: int = Form(..., ge=0),
    note: str = Form(""),
    cost: Optional[float] = Form(None, ge=0),
    inspection_fee: Optional[float] = Form(None, ge=0),
    road_fee: Optional[float] = Form(None, ge=0),
    result: Optional[str] = Form(None),
    new_sticker_expiry: Optional[datetime] = Form(None),
    user: dict = Depends(get_current_active_driver),
):
    _check_kind(kind)
    note = note.strip()
    if len(note) > _MAX_NOTE_CHARS:
        raise HTTPException(status_code=422, detail="Ghi chú quá dài")
    if not (photo.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="Tệp đính kèm phải là ảnh")
    photo_bytes = await photo.read()
    if not photo_bytes:
        raise HTTPException(status_code=422, detail="Cần chụp ảnh hoá đơn / tem")
    if len(photo_bytes) > _MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Ảnh quá lớn (tối đa 10MB)")
    try:
        job = jobs.submit(
            kind,
            job_id,
            user["uid"],
            photo_bytes=photo_bytes,
            content_type=photo.content_type,
            odometer=odometer,
            note=note,
            cost=cost,
            inspection_fee=inspection_fee,
            road_fee=road_fee,
            result=result,
            new_sticker_expiry=new_sticker_expiry,
        )
    except jobs.JobError as e:
        raise _http(e)
    await jobs.broadcast_submitted(kind, job, user["uid"])
    return job


# ── Web admin ────────────────────────────────────────────────────────────
class RejectPayload(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


@router.post("/{kind}/{job_id}/confirm")
def confirm_job(kind: str, job_id: str, admin: dict = Depends(get_current_admin)):
    _check_kind(kind)
    try:
        return jobs.confirm(kind, job_id, admin["uid"])
    except jobs.JobError as e:
        raise _http(e)


@router.post("/{kind}/{job_id}/reject")
def reject_job(
    kind: str,
    job_id: str,
    payload: RejectPayload,
    admin: dict = Depends(get_current_admin),
):
    _check_kind(kind)
    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="Nhập lý do trả lại")
    try:
        return jobs.reject(kind, job_id, admin["uid"], reason)
    except jobs.JobError as e:
        raise _http(e)
