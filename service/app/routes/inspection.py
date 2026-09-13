from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from app.models.inspection import InspectionComplete, InspectionCreate
from app.services import inspection_service

router = APIRouter(
    prefix="/inspections",
    tags=["vehicle inspections"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/")
def list_inspections(vehicle_id: Optional[str] = None):
    return inspection_service.list_inspections(vehicle_id)


@router.post("/")
def create_inspection(inspection: InspectionCreate):
    return inspection_service.create_inspection(inspection)


@router.get("/{inspection_id}")
def get_inspection(inspection_id: str):
    inspection = inspection_service.get_inspection(inspection_id)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.put("/{inspection_id}")
def update_inspection(inspection_id: str, data: dict):
    inspection = inspection_service.update_inspection(inspection_id, data)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.delete("/{inspection_id}")
def delete_inspection(inspection_id: str):
    if not inspection_service.delete_inspection(inspection_id):
        raise HTTPException(status_code=404, detail="Inspection not found")
    return {"status": "success"}


@router.post("/{inspection_id}/complete")
def complete_inspection(inspection_id: str, payload: InspectionComplete):
    """Đóng hồ sơ kèm kết quả Đạt/Không đạt; Đạt + có ngày hết hạn tem mới ->
    tự sinh hồ sơ kỳ tiếp theo."""
    result = inspection_service.complete_inspection(
        inspection_id, payload.result, payload.new_sticker_expiry
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.post("/{inspection_id}/notify")
def notify_inspection(inspection_id: str):
    result = inspection_service.notify_inspection(inspection_id)
    if result["reason"] in ("inspection_not_found", "vehicle_not_found"):
        raise HTTPException(status_code=404, detail=result["reason"])
    return result
