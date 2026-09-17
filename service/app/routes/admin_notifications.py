from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from app.services import admin_notification_service

router = APIRouter(
    prefix="/admin/notifications",
    tags=["admin_notifications"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/")
def get_notifications():
    """Tổng hợp việc cần admin chú ý — cho chuông thông báo trên web."""
    return admin_notification_service.get_summary()
