from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from app.services.analytics_service import (
    get_driver_risk,
    get_drowsiness_by_hour,
)

# Dữ liệu rủi ro theo từng tài xế — chỉ admin được xem.
router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("/driver-risk")
def driver_risk():
    return get_driver_risk()


@router.get("/drowsiness-by-hour")
def drowsiness_by_hour():
    return get_drowsiness_by_hour()
