"""Test tách Bảo trì xe / Đăng kiểm xe + nhắc lịch tự động (TASK-C10).

Không cần backend chạy — gọi thẳng service.

    python scripts/sim_maintenance_inspection.py

  1. Xe có current_odometer_km
  2. Lịch bảo trì gần tới KM (còn 300km, remind_km_before=500) -> due_for_auto_reminder bắt được
  3. Lịch bảo trì còn xa cả ngày lẫn km -> KHÔNG bắt
  4. Đăng kiểm gần hết hạn tem (còn 5 ngày, remind_days_before=15) -> bắt được
  5. Đăng kiểm còn xa -> KHÔNG bắt
  6. run_auto_reminders() không sent được (chưa có fcm_token) nhưng vẫn trả reason đúng, KHÔNG raise
  7. Dọn dữ liệu test
"""

import pathlib
import sys
from datetime import datetime, timedelta, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from app.models.inspection import InspectionCreate  # noqa: E402
from app.models.maintenance import MaintenanceCreate  # noqa: E402
from app.models.vehicle import VehicleCreate  # noqa: E402
from app.services import (  # noqa: E402
    inspection_service,
    maintenance_service,
    vehicle_service,
)


def ok(label, cond):
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(1)


def main():
    now = datetime.now(timezone.utc)
    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(
            plate_number="TEST-C10",
            brand="Test",
            model="Sim",
            current_odometer_km=49_700,
        )
    )
    print("1) Tạo xe với current_odometer_km =", vehicle["current_odometer_km"])
    ok("current_odometer_km lưu đúng", vehicle["current_odometer_km"] == 49_700)

    near_km = None
    far = None
    near_insp = None
    far_insp = None
    next_insp = None
    try:
        print("\n2) Lịch bảo trì gần tới KM (còn 300km trong khi remind_km_before=500)")
        near_km = maintenance_service.create_maintenance(
            MaintenanceCreate(
                vehicle_id=vehicle["id"],
                type="oil_change",
                scheduled_date=now + timedelta(days=60),  # còn xa theo ngày
                due_odometer_km=50_000,  # còn 300km
                remind_km_before=500,
                remind_days_before=7,
            )
        )
        due_ids = {m["id"] for m in maintenance_service.due_for_auto_reminder(now)}
        ok("bắt được nhờ gần tới KM (dù còn xa ngày)", near_km["id"] in due_ids)

        print("\n3) Lịch bảo trì còn xa cả ngày lẫn km -> không bắt")
        far = maintenance_service.create_maintenance(
            MaintenanceCreate(
                vehicle_id=vehicle["id"],
                type="tire",
                scheduled_date=now + timedelta(days=90),
                due_odometer_km=80_000,  # còn rất xa
                remind_km_before=500,
                remind_days_before=7,
            )
        )
        due_ids = {m["id"] for m in maintenance_service.due_for_auto_reminder(now)}
        ok("không bắt lịch còn xa", far["id"] not in due_ids)

        print("\n4) Đăng kiểm gần hết hạn tem (còn 5 ngày, remind_days_before=15)")
        near_insp = inspection_service.create_inspection(
            InspectionCreate(
                vehicle_id=vehicle["id"],
                station="Trạm đăng kiểm 50-03V",
                appointment_at=now + timedelta(days=5),
                old_sticker_expiry=now + timedelta(days=5),
                remind_days_before=15,
                inspection_fee=250_000,
                road_fee=1_560_000,
            )
        )
        due_ids = {i["id"] for i in inspection_service.due_for_auto_reminder(now)}
        ok("bắt được đăng kiểm gần hết hạn tem", near_insp["id"] in due_ids)

        print("\n5) Đăng kiểm còn xa -> không bắt")
        far_insp = inspection_service.create_inspection(
            InspectionCreate(
                vehicle_id=vehicle["id"],
                station="Trạm đăng kiểm 50-03V",
                appointment_at=now + timedelta(days=120),
                old_sticker_expiry=now + timedelta(days=120),
                remind_days_before=15,
            )
        )
        due_ids = {i["id"] for i in inspection_service.due_for_auto_reminder(now)}
        ok("không bắt đăng kiểm còn xa", far_insp["id"] not in due_ids)

        print("\n6) run_auto_reminders() không crash khi chưa có fcm_token")
        results = maintenance_service.run_auto_reminders()
        m_result = next(r for r in results if r["maintenance_id"] == near_km["id"])
        ok("reason = driver_has_no_fcm_token (xe chưa gán tài xế)",
           m_result["reason"] == "driver_has_no_fcm_token")
        ok("sent = False (không raise)", m_result["sent"] is False)

        i_results = inspection_service.run_auto_reminders()
        i_result = next(r for r in i_results if r["inspection_id"] == near_insp["id"])
        ok("đăng kiểm cũng không crash", i_result["sent"] is False)

        print("\n7) Đóng hồ sơ đăng kiểm: Đạt + có hạn tem mới -> tự sinh kỳ sau")
        new_expiry = now + timedelta(days=365)
        outcome = inspection_service.complete_inspection(
            near_insp["id"], "passed", new_expiry
        )
        ok("hồ sơ cũ chuyển done", outcome["closed"]["status"] == "done")
        ok("hồ sơ cũ ghi result=passed", outcome["closed"]["result"] == "passed")
        ok("có sinh hồ sơ kỳ sau", outcome["next"] is not None)
        ok("hồ sơ kỳ sau ở trạng thái pending", outcome["next"]["status"] == "pending")
        ok("hồ sơ kỳ sau chưa có khung giờ hẹn",
           outcome["next"].get("appointment_at") is None)
        next_insp = outcome["next"]

        print("\n8) Đóng hồ sơ Không đạt -> KHÔNG tự sinh kỳ sau")
        far_outcome = inspection_service.complete_inspection(far_insp["id"], "failed", None)
        ok("hồ sơ chuyển done + result=failed", far_outcome["closed"]["result"] == "failed")
        ok("không sinh hồ sơ mới", far_outcome["next"] is None)

        print("\nTẤT CẢ PASS ✔")
    finally:
        for m in (near_km, far):
            if m:
                maintenance_service.delete_maintenance(m["id"])
        for i in (near_insp, far_insp, next_insp):
            if i:
                inspection_service.delete_inspection(i["id"])
        vehicle_service.delete_vehicle(vehicle["id"])
        print("Đã dọn dữ liệu test")


if __name__ == "__main__":
    main()
