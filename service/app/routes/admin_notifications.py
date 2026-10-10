from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_admin
from app.services import admin_notification_service

router = APIRouter(
    prefix="/admin/notifications",
    tags=["admin_notifications"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/")
def get_notifications(limit: int = Query(5, ge=1, le=500)):
    """Tổng hợp việc cần admin chú ý. Chuông lấy 5 mục/nhóm; trang Thông báo
    gọi kèm `limit` lớn để lấy toàn bộ danh sách."""
    return admin_notification_service.get_summary(limit)
