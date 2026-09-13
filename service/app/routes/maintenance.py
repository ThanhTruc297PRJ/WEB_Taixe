from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from app.models.maintenance import MaintenanceCreate
from app.services import maintenance_service, reminder_scheduler

router = APIRouter(
    prefix="/maintenance",
    tags=["maintenance"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("/scan-reminders")
def scan_reminders():
    """Quét + gửi nhắc bảo trì/đăng kiểm NGAY, không chờ chu kỳ nền — dùng để
    demo/kiểm thử nhắc tự động (TASK-C10)."""
    return reminder_scheduler.run_scan_once()


@router.get("/")
def list_maintenance(vehicle_id: Optional[str] = None):
    return maintenance_service.list_maintenance(vehicle_id)


@router.post("/")
def create_maintenance(maintenance: MaintenanceCreate):
    return maintenance_service.create_maintenance(maintenance)


@router.get("/{maintenance_id}")
def get_maintenance(maintenance_id: str):
    maintenance = maintenance_service.get_maintenance(maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance


@router.put("/{maintenance_id}")
def update_maintenance(maintenance_id: str, data: dict):
    maintenance = maintenance_service.update_maintenance(maintenance_id, data)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance


@router.delete("/{maintenance_id}")
def delete_maintenance(maintenance_id: str):
    if not maintenance_service.delete_maintenance(maintenance_id):
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return {"status": "success"}


@router.post("/{maintenance_id}/notify")
def notify_maintenance(maintenance_id: str):
    result = maintenance_service.notify_maintenance(maintenance_id)
    if result["reason"] in ("maintenance_not_found", "vehicle_not_found"):
        raise HTTPException(status_code=404, detail=result["reason"])
    return result
