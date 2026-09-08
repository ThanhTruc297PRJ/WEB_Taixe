import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger("driver_monitoring.api")


def get_client_ip(request: Request) -> str:
    """Return client IP; trust X-Forwarded-For only when explicitly enabled."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


async def ip_whitelist_middleware(request: Request, call_next):
    if not settings.IP_WHITELIST_ENABLED:
        return await call_next(request)

    # Keep health endpoint accessible to container/orchestrator health checks.
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = get_client_ip(request)
    if client_ip not in settings.IP_WHITELIST:
        logger.warning("Blocked request from non-whitelisted IP: %s", client_ip)
        return JSONResponse(status_code=403, content={"detail": "IP address is not allowed"})

    return await call_next(request)


async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    client_ip = get_client_ip(request)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "%s %s -> 500 ip=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            client_ip,
            duration_ms,
            request_id,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s ip=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        client_ip,
        duration_ms,
        request_id,
    )
    return response
