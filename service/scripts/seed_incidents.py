"""Tạo vài sự cố mẫu cho 1 tài xế để test màn hình Incidents Viewer (TASK-C06).

Mỗi sự cố kèm 1 ảnh snapshot PNG (màu đặc, sinh tại chỗ) upload lên Firebase
Storage rồi lưu URL công khai vào document — để Modal chi tiết lấy ảnh trực
tiếp từ Storage CDN như luồng thật (app tài xế sẽ upload ảnh thật).

    python scripts/seed_incidents.py <driver_id>
    python scripts/seed_incidents.py <driver_id> --clear   # xoá sự cố cũ của tài xế này trước

Cần FIREBASE_STORAGE_BUCKET trong .env.
"""

import argparse
import pathlib
import struct
import sys
import urllib.parse
import uuid
import zlib
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from app.services import incident_service  # noqa: E402

# type, điểm, phút trước hiện tại, ghi chú, màu ảnh (RGB)
_SAMPLES = [
    ("drowsiness", 10, 60 * 24 * 3, "Nhắm mắt > 2s khi đang chạy", (245, 158, 11)),
    ("distraction", 5, 60 * 24 * 2, "Nhìn khỏi mặt đường ~3s", (59, 130, 246)),
    ("drowsiness", 12, 60 * 20, "Ngáp liên tục + gật đầu", (217, 119, 6)),
    ("distraction", 7, 60 * 5, "Dùng điện thoại khi lái", (37, 99, 235)),
    ("drowsiness", 15, 30, "PERCLOS cao kéo dài", (180, 83, 9)),
]


def _solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(rgb) * width
    idat = zlib.compress(row * height)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _upload_snapshot(rgb: tuple[int, int, int]) -> str:
    """Upload ảnh lên Storage kèm download token kiểu Firebase, trả URL tải
    công khai qua CDN (giống URL mà Firebase SDK sinh ra ở app tài xế)."""
    if fb.bucket is None:
        raise SystemExit("Chưa cấu hình FIREBASE_STORAGE_BUCKET trong .env")

    name = f"incident_snapshots/seed-{uuid.uuid4().hex}.png"
    token = str(uuid.uuid4())
    blob = fb.bucket.blob(name)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(_solid_png(640, 360, rgb), content_type="image/png")

    encoded = urllib.parse.quote(name, safe="")
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{fb.bucket.name}"
        f"/o/{encoded}?alt=media&token={token}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("driver_id")
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    if args.clear:
        existing = incident_service.list_incidents(args.driver_id)
        for inc in existing:
            incident_service.delete_incident(inc["id"])
        print(f"Đã xoá {len(existing)} sự cố cũ")

    now = datetime.now(timezone.utc)
    for kind, points, minutes_ago, note, rgb in _SAMPLES:
        from app.models.incident import IncidentCreate

        created = incident_service.create_incident(
            IncidentCreate(
                driver_id=args.driver_id,
                type=kind,
                detected_at=now - timedelta(minutes=minutes_ago),
                confidence=round(0.7 + 0.05 * (points % 5), 2),
                points=points,
                snapshot_url=_upload_snapshot(rgb),
                note=note,
            )
        )
        print(f"  + {kind:11} {points:>2}đ  {created['id']}")

    total = sum(s[1] for s in _SAMPLES)
    print(f"Xong. Tổng điểm vi phạm của tài xế: {total}")


if __name__ == "__main__":
    main()
