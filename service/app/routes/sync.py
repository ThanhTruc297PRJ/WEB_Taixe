from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.offline_sync import OfflineSyncRequest, OfflineSyncResult
from app.services.offline_sync_service import sync_offline_incidents

router = APIRouter(prefix="/sync", tags=["Offline Sync"])


@router.post("/offline", response_model=OfflineSyncResult)
def sync_offline_data(
    payload: OfflineSyncRequest,
    user: dict = Depends(get_current_user),
):
    return sync_offline_incidents(payload)