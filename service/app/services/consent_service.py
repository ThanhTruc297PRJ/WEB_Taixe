from datetime import datetime, timezone

from app.core.firebase import db
from app.models.consent import ConsentCreate

COLLECTION = "consents"


def _doc_id(user_id: str, consent_type: str) -> str:
    return f"{user_id}_{consent_type}"


def upsert_consent(user_id: str, consent: ConsentCreate) -> dict:
    doc_id = _doc_id(user_id, consent.consent_type)
    data = {
        "user_id": user_id,
        "consent_type": consent.consent_type,
        "accepted": consent.accepted,
        "updated_at": datetime.now(timezone.utc),
    }
    db.collection(COLLECTION).document(doc_id).set(data)
    return {"id": doc_id, **data}


def list_consents(user_id: str) -> list[dict]:
    docs = db.collection(COLLECTION).where("user_id", "==", user_id).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]
