from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from app.models.trip import TripCreate
from app.services import trip_service

router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/")
def list_trips(driver_id: Optional[str] = None):
    return trip_service.list_trips(driver_id)


@router.post("/")
def create_trip(trip: TripCreate):
    return trip_service.create_trip(trip)


@router.get("/{trip_id}")
def get_trip(trip_id: str):
    trip = trip_service.get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.put("/{trip_id}")
def update_trip(trip_id: str, data: dict):
    trip = trip_service.update_trip(trip_id, data)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.delete("/{trip_id}")
def delete_trip(trip_id: str):
    if not trip_service.delete_trip(trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"status": "success"}
