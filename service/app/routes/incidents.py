from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from app.models.incident import IncidentCreate
from app.services import incident_service

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/")
def list_incidents(driver_id: Optional[str] = None):
    return incident_service.list_incidents(driver_id)


@router.post("/")
def create_incident(incident: IncidentCreate):
    return incident_service.create_incident(incident)


@router.get("/{incident_id}")
def get_incident(incident_id: str):
    incident = incident_service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
