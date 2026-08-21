from fastapi import APIRouter, HTTPException

from app.models.driver import DriverCreate
from app.services import driver_service

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/")
def list_drivers():
    return driver_service.list_drivers()


@router.post("/")
def create_driver(driver: DriverCreate):
    return driver_service.create_driver(driver)


@router.get("/{driver_id}")
def get_driver(driver_id: str):
    driver = driver_service.get_driver(driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}")
def update_driver(driver_id: str, data: dict):
    driver = driver_service.update_driver(driver_id, data)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.delete("/{driver_id}")
def delete_driver(driver_id: str):
    if not driver_service.delete_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"status": "success"}
