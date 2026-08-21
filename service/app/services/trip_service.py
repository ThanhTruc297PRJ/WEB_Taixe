from typing import Optional

from app.core.firebase import db
from app.models.trip import TripCreate

COLLECTION = "trips"


def create_trip(trip: TripCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = trip.model_dump()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def get_trip(trip_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(trip_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_trips(driver_id: Optional[str] = None) -> list[dict]:
    query = db.collection(COLLECTION)
    if driver_id:
        query = query.where("driver_id", "==", driver_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def update_trip(trip_id: str, data: dict) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(trip_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(data)
    return {"id": trip_id, **doc_ref.get().to_dict()}


def delete_trip(trip_id: str) -> bool:
    doc_ref = db.collection(COLLECTION).document(trip_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True
