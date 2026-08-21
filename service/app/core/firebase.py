import firebase_admin
from firebase_admin import credentials, firestore, storage

from app.core.config import settings

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    options = (
        {"storageBucket": settings.FIREBASE_STORAGE_BUCKET}
        if settings.FIREBASE_STORAGE_BUCKET
        else {}
    )
    firebase_admin.initialize_app(cred, options)

db = firestore.client()
bucket = storage.bucket() if settings.FIREBASE_STORAGE_BUCKET else None
