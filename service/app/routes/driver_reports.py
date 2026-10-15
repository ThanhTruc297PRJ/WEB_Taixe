from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.security import get_current_active_driver, get_current_admin
from app.services import driver_report_service

router = APIRouter(
    prefix="/driver-reports",
    tags=["driver reports"],
    dependencies=[Depends(get_current_admin)],
)

self_router = APIRouter(prefix="/driver-reports", tags=["driver reports (app tài xế)"])

_MAX_PHOTO_BYTES = 10 * 1024 * 1024
_MAX_NOTE_CHARS = 1000


# ── App tài xế ───────────────────────────────────────────────────────────
@self_router.post("/", status_code=201)
async def create_report(
    note: str = Form(""),
    photo: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    user: dict = Depends(get_current_active_driver),
):
    note = note.strip()
    photo_bytes = await photo.read() if photo else None
    if not note and not photo_bytes:
        raise HTTPException(status_code=422, detail="Cần nhập mô tả hoặc đính kèm ảnh")
    if len(note) > _MAX_NOTE_CHARS:
        raise HTTPException(status_code=422, detail="Mô tả quá dài")
    if photo_bytes:
        if not (photo.content_type or "").startswith("image/"):
            raise HTTPException(status_code=415, detail="Tệp đính kèm phải là ảnh")
        if len(photo_bytes) > _MAX_PHOTO_BYTES:
            raise HTTPException(status_code=413, detail="Ảnh quá lớn (tối đa 10MB)")
    try:
        report = driver_report_service.create_report(
            user["uid"], note, photo_bytes, photo.content_type if photo else None,
            latitude=latitude, longitude=longitude,
            address=(address or "").strip() or None,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    await driver_report_service.broadcast_report(report)
    return report


# ── Web admin ────────────────────────────────────────────────────────────
@router.get("/")
def list_reports():
    return driver_report_service.list_reports()


@router.put("/{report_id}/resolve")
def resolve_report(report_id: str, admin: dict = Depends(get_current_admin)):
    report = driver_report_service.resolve_report(report_id, admin["uid"])
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
