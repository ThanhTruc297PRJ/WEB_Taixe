"""Giả lập app tài xế báo trạng thái kết nối — để test realtime trên web
khi chưa có app mobile.

Chạy từ thư mục service/:

    python scripts/set_presence.py <driver_id> online
    python scripts/set_presence.py <driver_id> driving
    python scripts/set_presence.py <driver_id> offline

Lấy <driver_id> từ web (trang Quản lý tài xế) hoặc Firebase Console.
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401 — khởi tạo firebase_admin
from app.services import driver_service  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("driver_id")
    parser.add_argument("presence", choices=sorted(driver_service.PRESENCE_VALUES))
    args = parser.parse_args()

    result = driver_service.set_presence(args.driver_id, args.presence)
    if result is None:
        print(f"Không tìm thấy tài xế id={args.driver_id}")
        raise SystemExit(1)
    print(f"Đã đặt presence={args.presence} cho {result.get('name', args.driver_id)}")


if __name__ == "__main__":
    main()
