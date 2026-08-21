from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.consent import ConsentCreate
from app.services import consent_service

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/")
def submit_consent(
    consent: ConsentCreate,
    user: dict = Depends(get_current_user),
):
    return consent_service.upsert_consent(user["uid"], consent)


@router.get("/")
def get_my_consents(user: dict = Depends(get_current_user)):
    return consent_service.list_consents(user["uid"])
