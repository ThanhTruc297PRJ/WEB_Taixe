from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routes import (
    assistant,
    auth,
    consent,
    drivers,
    incidents,
    maintenance,
    trips,
    vehicles,
)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)


# Registered before CORSMiddleware below: Starlette wraps middleware in the
# reverse of add-order, so the middleware added *last* ends up outermost.
# This must sit inside CORSMiddleware so the JSONResponse it returns for an
# unhandled exception still passes through CORSMiddleware on the way out —
# otherwise the browser reports a misleading CORS error instead of the
# real 500 (a bare @app.exception_handler(Exception) has this same problem,
# since it's wired into ServerErrorMiddleware, which is always outermost).
@app.middleware("http")
async def catch_unhandled_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(consent.router)
app.include_router(drivers.router)
app.include_router(drivers.self_router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)
app.include_router(trips.router)
app.include_router(incidents.router)
app.include_router(assistant.router)


@app.get("/")
def read_root():
    return {"status": "success", "message": "Backend Driver Safety đang chạy!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
