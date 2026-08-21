from typing import Optional

from app.core.firebase import db
from app.models.driver import DriverCreate

COLLECTION = "drivers"


def create_driver(driver: DriverCreate) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    data = driver.model_dump()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


def get_driver(driver_id: str) -> Optional[dict]:
    doc = db.collection(COLLECTION).document(driver_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def list_drivers() -> list[dict]:
    return [{"id": doc.id, **doc.to_dict()} for doc in db.collection(COLLECTION).stream()]


def update_driver(driver_id: str, data: dict) -> Optional[dict]:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return None
    doc_ref.update(data)
    return {"id": driver_id, **doc_ref.get().to_dict()}


def delete_driver(driver_id: str) -> bool:
    doc_ref = db.collection(COLLECTION).document(driver_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True
