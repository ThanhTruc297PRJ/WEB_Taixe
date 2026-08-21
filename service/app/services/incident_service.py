from typing import Optional

from app.core.firebase import db
from app.models.incident import IncidentCreate

COLLECTION = "incidents"


def create_incident(incident: IncidentCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = incident.model_dump()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def get_incident(incident_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(incident_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_incidents(driver_id: Optional[str] = None) -> list[dict]:
    query = db.collection(COLLECTION)
    if driver_id:
        query = query.where("driver_id", "==", driver_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]
