from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from app.models.vehicle import VehicleCreate
from app.services import vehicle_service

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/")
def list_vehicles(driver_id: Optional[str] = None):
    return vehicle_service.list_vehicles(driver_id)


@router.post("/")
def create_vehicle(vehicle: VehicleCreate):
    return vehicle_service.create_vehicle(vehicle)


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str):
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.put("/{vehicle_id}")
def update_vehicle(vehicle_id: str, data: dict):
    vehicle = vehicle_service.update_vehicle(vehicle_id, data)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: str):
    if not vehicle_service.delete_vehicle(vehicle_id):
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"status": "success"}
