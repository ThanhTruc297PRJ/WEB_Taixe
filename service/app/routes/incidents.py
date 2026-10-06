from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.security import get_current_active_driver, get_current_admin
from app.models.incident import IncidentCreate
from app.services import incident_service

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    dependencies=[Depends(get_current_admin)],
)

# App tài xế tự gửi sự cố (kèm clip). Chỉ cần tài khoản đã được duyệt.
self_router = APIRouter(prefix="/incidents", tags=["incidents (app tài xế)"])

_MAX_CLIP_BYTES = 30 * 1024 * 1024  # 30MB — clip 480p ~10s thường 1-3MB


@self_router.post("/report", status_code=201)
async def report_incident(
    clip: UploadFile = File(...),
    type: str = Form("drowsiness"),
    detected_at: str = Form(...),
    confidence: Optional[float] = Form(None),
    note: Optional[str] = Form(None),
    user: dict = Depends(get_current_active_driver),
):
    data = await clip.read()
    if not data:
        raise HTTPException(status_code=422, detail="Clip rỗng")
    if len(data) > _MAX_CLIP_BYTES:
        raise HTTPException(status_code=413, detail="Clip quá lớn")
    try:
        incident = incident_service.report_from_driver(
            uid=user["uid"],
            incident_type=type,
            detected_at=detected_at,
            confidence=confidence,
            note=(note or '').strip()[:500] or None,
            clip_bytes=data,
            content_type=clip.content_type,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    await incident_service.broadcast_incident(incident)
    return incident


# ── Web admin ────────────────────────────────────────────────────────────
@router.get("/")
def list_incidents(driver_id: Optional[str] = None):
    return incident_service.list_incidents(driver_id)


@router.post("/")
async def create_incident(incident: IncidentCreate):
    result = incident_service.create_incident(incident)
    await incident_service.broadcast_incident(result)
    return result


@router.get("/{incident_id}")
def get_incident(incident_id: str):
    incident = incident_service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.delete("/{incident_id}")
def delete_incident(incident_id: str):
    if not incident_service.delete_incident(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "success"}
