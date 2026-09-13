"""Quét nhắc lịch bảo trì + đăng kiểm tự động, chạy nền trong tiến trình
backend (giống heartbeat_monitor của websocket_manager) — không cần cron
ngoài. TASK-C10.

Mỗi chu kỳ: quét toàn bộ lịch bảo trì (theo ngày HOẶC theo km, cái nào tới
trước) và đăng kiểm (theo ngày hết hạn tem) còn "pending" và chưa nhắc trong
24h gần nhất, rồi gửi FCM cho tài xế phụ trách.
"""

import asyncio
import logging

from app.services import inspection_service, maintenance_service

_log = logging.getLogger("driver_monitoring.reminder")

# 6 tiếng/lần là đủ cho lịch tính theo ngày; đặt biến môi trường
# REMINDER_SCAN_INTERVAL_SECONDS để rút ngắn lúc demo/kiểm thử.
DEFAULT_INTERVAL_SECONDS = 6 * 60 * 60


def run_scan_once() -> dict:
    """Chạy 1 lần quét — dùng cho vòng lặp nền và cho endpoint quét thủ công
    (POST /maintenance/scan-reminders) khi demo không muốn chờ chu kỳ thật."""
    maintenance_results = maintenance_service.run_auto_reminders()
    inspection_results = inspection_service.run_auto_reminders()
    sent = sum(1 for r in maintenance_results + inspection_results if r.get("sent"))
    _log.info(
        "Quét nhắc lịch: %d bảo trì + %d đăng kiểm tới hạn, gửi thành công %d",
        len(maintenance_results),
        len(inspection_results),
        sent,
    )
    return {
        "maintenance": maintenance_results,
        "inspections": inspection_results,
        "sent": sent,
    }


async def run_forever(interval_seconds: int = DEFAULT_INTERVAL_SECONDS):
    while True:
        try:
            run_scan_once()
        except Exception:
            _log.exception("Lỗi khi quét nhắc lịch bảo trì/đăng kiểm")
        await asyncio.sleep(interval_seconds)
