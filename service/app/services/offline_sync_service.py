from app.core.firebase import db
from app.models.offline_sync import OfflineSyncRequest


COLLECTION_NAME = "incidents"


def sync_offline_incidents(payload: OfflineSyncRequest):
    inserted = 0
    skipped_duplicate = 0

    for incident in payload.incidents:
        doc_ref = db.collection(COLLECTION_NAME).document(incident.event_id)

        existing = doc_ref.get()

        if existing.exists:
            skipped_duplicate += 1
            continue

        data = incident.model_dump()
        data["detected_at"] = incident.detected_at

        doc_ref.set(data)
        inserted += 1

    return {
        "total_received": len(payload.incidents),
        "inserted": inserted,
        "skipped_duplicate": skipped_duplicate,
    }