from fastapi import FastAPI

from app.core.config import settings
from app.core.firebase import db
from app.routes import auth, consent, drivers, incidents, trips

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.include_router(auth.router)
app.include_router(consent.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(incidents.router)


@app.get("/")
def read_root():
    return {"status": "success", "message": "Backend Driver Safety đang chạy!"}


@app.get("/test-firestore")
def test_firestore():
    # Ghi thử 1 bản ghi kiểm tra lên Firestore
    doc_ref = db.collection("system_logs").document("health_check")
    doc_ref.set({
        "status": "connected",
        "message": "Firebase Admin SDK kết nối thành công!",
    })

    # Đọc lại bản ghi vừa ghi
    doc = doc_ref.get()
    return {
        "status": "OK",
        "firestore_data": doc.to_dict()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
