from fastapi import APIRouter
from app.services.analytics_service import (
    get_driver_risk,
    get_drowsiness_by_hour,
)

router = APIRouter()


@router.get("/driver-risk")
def driver_risk():
    return get_driver_risk()


@router.get("/drowsiness-by-hour")
def drowsiness_by_hour():
    return get_drowsiness_by_hour()