import asyncio
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.middleware import ip_whitelist_middleware, request_logging_middleware
from app.core.rate_limit import limiter
from app.routes import (
    admin_notifications,
    assistant,
    auth,
    consent,
    drivers,
    incidents,
    inspection,
    kb,
    maintenance,
    music,
    sync,
    trips,
    vehicles,
    websocket,
)
from app.services import reminder_scheduler
from app.services.websocket_manager import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)


@app.on_event("startup")
async def _start_heartbeat_monitor():
    app.state.heartbeat_task = asyncio.create_task(manager.heartbeat_monitor())


@app.on_event("startup")
async def _start_reminder_scheduler():
    # TASK-C10: quét nhắc lịch bảo trì + đăng kiểm tự động chạy nền suốt vòng
    # đời app — không cần cron ngoài. Rút ngắn chu kỳ lúc demo bằng biến môi
    # trường REMINDER_SCAN_INTERVAL_SECONDS.
    interval = int(
        os.getenv(
            "REMINDER_SCAN_INTERVAL_SECONDS",
            reminder_scheduler.DEFAULT_INTERVAL_SECONDS,
        )
    )
    app.state.reminder_task = asyncio.create_task(
        reminder_scheduler.run_forever(interval)
    )


@app.on_event("shutdown")
async def _stop_heartbeat_monitor():
    task = getattr(app.state, "heartbeat_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.on_event("shutdown")
async def _stop_reminder_scheduler():
    task = getattr(app.state, "reminder_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


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


# B04: structured request logging + optional IP whitelist.
app.middleware("http")(request_logging_middleware)
app.middleware("http")(ip_whitelist_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)


app.include_router(auth.router)
app.include_router(consent.router)
# self_router trước router: để GET /drivers/me không bị GET /drivers/{driver_id}
# (admin-gated) bắt mất.
app.include_router(drivers.self_router)
app.include_router(drivers.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)
app.include_router(inspection.router)
app.include_router(trips.router)
app.include_router(incidents.self_router)
app.include_router(incidents.router)
app.include_router(assistant.router)
app.include_router(kb.router)
app.include_router(music.self_router)
app.include_router(music.router)
app.include_router(websocket.router)
app.include_router(sync.router)
app.include_router(admin_notifications.router)


@app.get("/health")
@limiter.exempt
def health(request: Request):
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
def read_root(request: Request):
    return {"status": "success", "message": "Backend Driver Safety đang chạy!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
