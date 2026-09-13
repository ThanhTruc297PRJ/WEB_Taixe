"""Gửi email nghiệp vụ (không phải email xác thực — cái đó Firebase Auth tự
gửi sẵn, miễn phí, không cần code gì). Dùng để báo "đăng ký thành công" sau
khi admin duyệt.

Dùng Gmail SMTP (miễn phí) — cần 1 tài khoản Gmail đã bật xác thực 2 lớp +
"Mật khẩu ứng dụng" (App Password, KHÔNG phải mật khẩu Gmail thường). Đặt vào
service/.env:

    SMTP_USER=your_company@gmail.com
    SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # App Password 16 ký tự

Chưa cấu hình thì bỏ qua (log cảnh báo), KHÔNG raise — không được để lỗi gửi
mail làm hỏng luồng duyệt tài khoản.
"""

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Optional

_log = logging.getLogger("driver_monitoring.email")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Driver Monitor")


def _configured() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD)


def send_email(to_email: str, subject: str, body_text: str) -> bool:
    """Gửi 1 email text đơn giản. Trả False (không raise) nếu chưa cấu hình
    SMTP hoặc gửi lỗi — caller không nên coi đây là lỗi nghiêm trọng."""
    if not to_email:
        return False
    if not _configured():
        _log.warning(
            "Chưa cấu hình SMTP_USER/SMTP_PASSWORD trong .env — bỏ qua gửi "
            "email tới %s: %s",
            to_email,
            subject,
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.set_content(body_text)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        _log.exception("Gửi email thất bại tới %s", to_email)
        return False


def send_registration_approved(to_email: Optional[str], driver_name: str) -> bool:
    if not to_email:
        return False
    body = (
        f"Chào {driver_name},\n\n"
        "Hồ sơ đăng ký tài xế của bạn đã được quản trị viên DUYỆT.\n"
        "Bạn có thể mở lại ứng dụng và đăng nhập để bắt đầu sử dụng.\n\n"
        "Trân trọng,\nDriver Monitor"
    )
    return send_email(to_email, "Tài khoản tài xế đã được duyệt", body)
