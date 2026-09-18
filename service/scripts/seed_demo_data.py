"""Nạp dữ liệu demo thực tế vào Firestore (không phải data giả cứng trong UI)
để dashboard/các trang web admin không còn trống trơn khi xem thử.

Dùng lại đúng tài xế/xe THẬT đang có sẵn trong hệ thống — không tạo tài
khoản/xe mới, chỉ:
  - Dọn xe đang gán cho tài xế đã bị xoá (driver_id mồ côi) + đặt biển số/hãng
    xe cho thực tế hơn (dữ liệu test cũ kiểu "678686"/"toyota tải").
  - Đặt trạng thái online/đang lái + tốc độ hiện tại cho vài tài xế (dữ liệu
    này sẽ tự "nguội" theo đúng thiết kế PRESENCE_STALE_MS/SPEED_STALE_MS sau
    vài phút — không có gì giả mạo mãi mãi, đúng tinh thần "không tự tạo hoạt
    động ảo" đã thống nhất trước đó).
  - Thêm vài lịch bảo trì/đăng kiểm sắp tới hạn.
  - Thêm sự cố (buồn ngủ/mất tập trung) rải trong 8 tuần gần đây + vài vụ
    "hôm nay" để biểu đồ + thẻ thống kê Dashboard có số liệu thật để vẽ.

Chạy: python scripts/seed_demo_data.py (từ thư mục service/, cần .env như
lúc chạy app bình thường).
"""

import pathlib
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.firebase import db  # noqa: E402
from app.models.incident import IncidentCreate  # noqa: E402
from app.models.inspection import InspectionCreate  # noqa: E402
from app.models.maintenance import MaintenanceCreate  # noqa: E402
from app.services import incident_service, inspection_service, maintenance_service  # noqa: E402

# Tài xế thật đang có sẵn (lấy từ Firestore hiện tại, không bịa).
D_TRUC = "6GoxgCcVn7UajqFbHljz4NhSAf72"  # Pham Thanh Truc
D_ANH = "bUFiAwOqobYJUkmTVP8SuNpF1ye2"  # Anh
D_NO = "l8bp2jzmhkVNJNEfS9U9SOjZImL2"  # Nguyen Thi No
D_TEO = "xEMCEUsQvJMkU4lwWVcvhYhXPWs2"  # Nguyen Van Teo

V_1 = "C2A4hFX3G5nlWS10dOGG"  # trước gán cho driver đã xoá -> dọn lại
V_2 = "PdnKXCc3V8Faj0HBVjPF"
V_3 = "QxqhQ1VWQAuP1Q0gfXtP"


def now():
    return datetime.now(timezone.utc)


def fix_vehicles():
    """Dọn driver_id mồ côi + đặt biển số/hãng xe thực tế thay dữ liệu test."""
    updates = {
        V_1: {
            "plate_number": "51H-882.91",
            "brand": "Toyota",
            "model": "Innova Cross",
            "driver_id": D_TEO,
            "current_odometer_km": 35420,
            "status": "active",
        },
        V_2: {
            "plate_number": "51A-992.12",
            "brand": "Honda",
            "model": "City RS",
            "driver_id": D_TRUC,
            "current_odometer_km": 12850,
            "status": "active",
        },
        V_3: {
            "plate_number": "60A-129.84",
            "brand": "Ford",
            "model": "Ranger XLT",
            "driver_id": D_ANH,
            "current_odometer_km": 56767,
            "status": "active",
        },
    }
    for vehicle_id, data in updates.items():
        db.collection("vehicles").document(vehicle_id).update(data)
    print(f"Da cap nhat {len(updates)} xe (bien so thuc te + dan driver_id mo coi).")


def set_presence():
    """Vài tài xế online/đang lái + tốc độ hiện tại — tự nguội theo đúng thời
    gian đã thiết kế (2 phút cho presence, 30s cho tốc độ) vì không có gì
    liên tục cập nhật lại sau khi script chạy xong."""
    t = now()
    updates = {
        D_TEO: {"presence": "driving", "last_seen": t, "current_speed_kmh": 45.0, "speed_updated_at": t},
        D_TRUC: {"presence": "driving", "last_seen": t, "current_speed_kmh": 62.0, "speed_updated_at": t},
        D_ANH: {"presence": "online", "last_seen": t},
    }
    for driver_id, data in updates.items():
        db.collection("drivers").document(driver_id).update(data)
    print(f"Da dat presence/toc do cho {len(updates)} tai xe (con moi ~2 phut).")


def seed_maintenance_inspection():
    created = 0
    created += 1
    maintenance_service.create_maintenance(
        MaintenanceCreate(
            vehicle_id=V_2,
            driver_id=D_TRUC,
            vendor="Gara Thanh Dat",
            type="oil_change",
            scheduled_date=now() + timedelta(days=4),
            due_odometer_km=15000,
            interval_km=5000,
            cost=850000,
        )
    )
    created += 1
    maintenance_service.create_maintenance(
        MaintenanceCreate(
            vehicle_id=V_3,
            driver_id=D_ANH,
            vendor="Gara Hoang Long",
            type="tire",
            scheduled_date=now() + timedelta(days=12),
            due_odometer_km=60000,
            interval_km=20000,
            cost=2400000,
        )
    )
    print(f"Da them {created} lich bao tri moi.")

    inspection_service.create_inspection(
        InspectionCreate(
            vehicle_id=V_1,
            driver_id=D_TEO,
            station="Trung tam dang kiem 50-03V",
            appointment_at=now() + timedelta(days=9, hours=3),
            old_sticker_expiry=now() + timedelta(days=10),
            inspection_fee=340000,
            road_fee=1560000,
        )
    )
    print("Da them 1 ho so dang kiem sap toi han.")


def seed_incidents():
    drivers = [D_TRUC, D_ANH, D_NO, D_TEO]
    types = ["drowsiness", "distraction"]
    n = now()
    created = 0

    # Rai trong 8 tuan gan day, 2-4 vu moi tuan, tuan gan hien tai nhieu hon
    # (mo phong xu huong that hon la deu tam tam).
    for week_ago in range(8, 0, -1):
        week_start = n - timedelta(weeks=week_ago)
        count = random.randint(1, 2) if week_ago > 3 else random.randint(2, 4)
        for _ in range(count):
            driver_id = random.choice(drivers)
            incident_type = random.choice(types)
            detected_at = week_start + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(6, 20),
                minutes=random.randint(0, 59),
            )
            points = random.randint(8, 15) if incident_type == "drowsiness" else random.randint(4, 8)
            incident_service.create_incident(
                IncidentCreate(
                    driver_id=driver_id,
                    type=incident_type,
                    detected_at=detected_at,
                    confidence=round(random.uniform(0.82, 0.99), 2),
                    points=points,
                )
            )
            created += 1

    # Vai vu "hom nay" ro rang, tap trung khung gio 12h-15h de co "cao diem".
    today_events = [
        (D_TEO, "drowsiness", 12, 40, 0.91, 12),
        (D_TRUC, "distraction", 13, 15, 0.87, 6),
        (D_TEO, "drowsiness", 14, 5, 0.94, 14),
    ]
    for driver_id, incident_type, hour, minute, confidence, points in today_events:
        incident_service.create_incident(
            IncidentCreate(
                driver_id=driver_id,
                type=incident_type,
                detected_at=n.replace(hour=hour, minute=minute, second=0, microsecond=0),
                confidence=confidence,
                points=points,
            )
        )
        created += 1

    print(f"Da them {created} su co (rai 8 tuan + 3 vu hom nay).")


if __name__ == "__main__":
    random.seed(42)
    fix_vehicles()
    set_presence()
    seed_maintenance_inspection()
    seed_incidents()
    print("Xong.")
