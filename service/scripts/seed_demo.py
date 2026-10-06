"""Tạo / xoá dữ liệu mẫu cho demo — mỗi trang web admin có tối thiểu 20 bản ghi.

    python scripts/seed_demo.py          # tạo (dừng nếu đã có dữ liệu mẫu)
    python scripts/seed_demo.py --clean  # xoá sạch toàn bộ dữ liệu mẫu

Mọi bản ghi tạo ra đều có `demo: true` (tài liệu cơ sở tri thức: updated_by
"DEMO_SEED"); tài khoản đăng nhập dùng email @demo.local. --clean chỉ xoá
những thứ đó, không đụng dữ liệu thật.

Tài xế mẫu đăng nhập được app: demo.taixe01@demo.local … demo.taixe20@demo.local,
mật khẩu chung DEMO_PASSWORD bên dưới.
"""

import random
import sys
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from firebase_admin import auth as firebase_auth  # noqa: E402

from app.core.firebase import bucket, db  # noqa: E402
from app.models.kb import KbDocumentIn  # noqa: E402
from app.services import kb_service  # noqa: E402
from scripts.demo_kb import DEMO_KB  # noqa: E402

DEMO_PASSWORD = "Demo@123456"
EMAIL_DOMAIN = "demo.local"
KB_AUTHOR = "DEMO_SEED"
DEMO_ADMIN = "DEMO_SEED"
PROOF_PREFIX = "job_proofs/demo/"
COLLECTIONS = [
    "drivers",
    "vehicles",
    "incidents",
    "driver_reports",
    "maintenance_schedules",
    "vehicle_inspections",
]

rng = random.Random(20261006)  # cố định -> chạy lại ra cùng bộ dữ liệu
NOW = datetime.now(timezone.utc)


def ago(days: float = 0, hours: float = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours)


def ahead(days: float) -> datetime:
    return NOW + timedelta(days=days)


# ── Dữ liệu nguồn ────────────────────────────────────────────────────────
NAMES = [
    "Nguyễn Văn Hùng", "Trần Minh Tuấn", "Lê Quốc Bảo", "Phạm Đức Thịnh",
    "Hoàng Văn Nam", "Vũ Thành Long", "Đặng Hữu Phước", "Bùi Anh Khoa",
    "Đỗ Trọng Nghĩa", "Ngô Văn Sơn", "Dương Minh Trí", "Lý Hoàng Phúc",
    "Phan Văn Dũng", "Trịnh Quang Huy", "Huỳnh Tấn Lộc", "Mai Xuân Trường",
    "Võ Thanh Tâm", "Tạ Đình Khải", "Châu Văn Lợi", "Lâm Gia Hưng",
]
# 15 hoạt động, 2 chờ duyệt, 2 đã khoá (inactive), 1 bị từ chối.
STATUSES = ["active"] * 15 + ["pending", "pending", "inactive", "inactive", "rejected"]
# Số sự cố mỗi tài xế (buồn ngủ, mất tập trung) -> phân bố đủ 4 mức vi phạm
# với ngưỡng mặc định 10 / 22 / 30 điểm (buồn ngủ 10đ, mất tập trung 5đ).
INCIDENT_PLAN = [
    (0, 0), (0, 1), (0, 1), (0, 0), (0, 1), (0, 0),  # bình thường
    (1, 0), (0, 2), (1, 1), (1, 1),  # nhắc nhở
    (2, 1), (2, 0), (2, 1),  # cảnh cáo
    (3, 1), (4, 0),  # đình chỉ
    None, None,  # chờ duyệt: chưa chạy xe
    (4, 2), (3, 2),  # đã khoá
    None,  # bị từ chối
]
VEHICLES = [
    ("Toyota", "Vios"), ("Toyota", "Innova"), ("Hyundai", "Accent"), ("Hyundai", "County"),
    ("Ford", "Transit"), ("Kia", "Morning"), ("Mitsubishi", "Xpander"), ("Isuzu", "QKR"),
    ("Hino", "XZU"), ("Toyota", "Fortuner"), ("Hyundai", "Solati"), ("Ford", "Ranger"),
    ("Kia", "Carnival"), ("Thaco", "Ollin"), ("Suzuki", "Carry Pro"), ("Toyota", "Hiace"),
    ("Mazda", "BT-50"), ("Hyundai", "Porter"), ("Isuzu", "N-Series"), ("VinFast", "VF 8"),
]
PROVINCES = ["29", "30", "51", "50", "43", "92", "15", "37", "65", "36"]
VENDORS = [
    "Gara Thành Đạt", "Toyota Bến Thành", "Hyundai Phạm Hùng", "Ô tô Minh Phát",
    "Ford Thủ Đô", "Gara Hưng Thịnh", "Isuzu An Lạc",
]
STATIONS = [
    "Trạm đăng kiểm 50-05V (TP.HCM)", "Trạm đăng kiểm 29-01S (Hà Nội)",
    "Trạm đăng kiểm 51-02D (TP.HCM)", "Trạm đăng kiểm 43-01D (Đà Nẵng)",
    "Trạm đăng kiểm 15-02D (Hải Phòng)",
]
MAINT_TYPES = {
    "oil_change": (450_000, 950_000),
    "tire": (2_400_000, 8_500_000),
    "brake": (800_000, 2_600_000),
    "battery": (1_500_000, 3_200_000),
    "other": (300_000, 4_500_000),
}
REPORT_NOTES = [
    "Xe bị xịt lốp sau bên phải tại km 45 cao tốc TP.HCM – Trung Lương",
    "Đèn báo nhiệt độ nước làm mát sáng, đã dừng xe ở trạm dừng nghỉ",
    "Kẹt xe kéo dài hơn 1 tiếng ở cầu Phú Mỹ, giao hàng có thể trễ",
    "Va quẹt nhẹ gương chiếu hậu với xe máy, hai bên đã thống nhất",
    "Điều hoà không mát, khách phản ánh trong xe nóng",
    "Đường ngập sâu ở Nguyễn Hữu Cảnh, xin đổi lộ trình",
    "Cần gạt nước bên lái bị kẹt, mưa lớn khó quan sát",
    "Khách hàng hẹn lại giờ nhận hàng sang chiều mai",
    "Xe đề khó vào buổi sáng, nghi ắc quy yếu",
    "Phát hiện dầu rỉ dưới gầm xe khi đỗ qua đêm",
    "Bị CSGT kiểm tra giấy tờ, mọi thứ hợp lệ, trễ 20 phút",
    "Đèn cốt bên phải bị cháy bóng",
    "Tiếng kêu lạ ở bánh trước khi phanh",
    "Trạm thu phí không nhận thẻ ETC, phải trả tiền mặt",
    "Hàng bị ướt một phần do mưa tạt khi bốc xếp",
    "Xe phía trước rơi vật liệu xây dựng, đã tránh kịp",
    "Đường đèo Bảo Lộc sương mù dày, chạy chậm",
    "Cảm biến lùi không báo, cần kiểm tra",
    "Chìa khoá dự phòng bị mất, xin cấp lại",
    "Hết hạn bảo hiểm trách nhiệm dân sự vào cuối tháng",
]


# ── Tiện ích ─────────────────────────────────────────────────────────────
def has_demo_data() -> bool:
    return any(
        list(db.collection(c).where("demo", "==", True).limit(1).stream()) for c in COLLECTIONS
    )


def upload_proof_image(label: str) -> str:
    """Ảnh hoá đơn / tem giả (nền trắng, chữ đen) cho lịch đang chờ xác nhận."""
    import cv2
    import numpy as np

    img = np.full((480, 360, 3), 255, np.uint8)
    cv2.rectangle(img, (12, 12), (348, 468), (60, 60, 60), 2)
    lines = [label, "DEMO", "So tien: xxx.xxx d", NOW.strftime("%d/%m/%Y")]
    for i, text in enumerate(lines):
        cv2.putText(img, text, (30, 80 + i * 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (30, 30, 30), 2)
    ok, buf = cv2.imencode(".jpg", img)
    name = f"{PROOF_PREFIX}{uuid.uuid4().hex}.jpg"
    token = str(uuid.uuid4())
    blob = bucket.blob(name)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(buf.tobytes(), content_type="image/jpeg")
    encoded = urllib.parse.quote(name, safe="")
    return f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded}?alt=media&token={token}"


def plate() -> str:
    return f"{rng.choice(PROVINCES)}{rng.choice('ABCDGH')}-{rng.randint(100, 999)}.{rng.randint(10, 99)}"


# ── Tạo ──────────────────────────────────────────────────────────────────
def seed_drivers() -> list[dict]:
    drivers = []
    for i, (name, status) in enumerate(zip(NAMES, STATUSES), start=1):
        email = f"demo.taixe{i:02d}@{EMAIL_DOMAIN}"
        try:
            user = firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            user = firebase_auth.create_user(
                email=email, password=DEMO_PASSWORD, display_name=name, email_verified=True
            )
        firebase_auth.set_custom_user_claims(user.uid, {"approved": True} if status == "active" else {})

        submitted = ago(days=rng.randint(40, 120))
        presence, last_seen, speed = "offline", ago(days=rng.uniform(0.5, 5)), 0.0
        if status == "active" and i <= 4:
            presence, last_seen, speed = "driving", NOW, float(rng.randint(35, 75))
        elif status == "active" and i <= 7:
            presence, last_seen = "online", NOW
        doc = {
            "demo": True,
            "name": name,
            "email": email,
            "phone": f"09{rng.randint(10_000_000, 99_999_999)}",
            "license_number": f"{rng.choice(['B2', 'C', 'D'])}-{rng.randint(10000, 99999)}",
            "status": status,
            "email_verified": status != "pending" or i % 2 == 0,
            "submitted_at": submitted,
            "approved_at": submitted + timedelta(hours=3) if status in ("active", "inactive") else None,
            "approved_by": DEMO_ADMIN if status in ("active", "inactive") else None,
            "reject_reason": "Ảnh bằng lái bị mờ, không đọc được số" if status == "rejected" else None,
            "presence": presence,
            "last_seen": last_seen if status != "pending" else None,
            "current_speed_kmh": speed,
            "speed_updated_at": NOW if speed else None,
            "fcm_token": None,
        }
        db.collection("drivers").document(user.uid).set(doc)
        drivers.append({"id": user.uid, **doc, "plan": INCIDENT_PLAN[i - 1]})
    return drivers


def seed_vehicles(drivers: list[dict]) -> list[dict]:
    active = [d for d in drivers if d["status"] == "active"]
    statuses = ["active"] * 16 + ["maintenance"] * 3 + ["inactive"]
    vehicles = []
    for i, ((brand, model), status) in enumerate(zip(VEHICLES, statuses)):
        driver_id = active[i]["id"] if i < len(active) and status == "active" else None
        doc = {
            "demo": True,
            "plate_number": plate(),
            "brand": brand,
            "model": model,
            "year": rng.randint(2016, 2024),
            "status": status,
            "driver_id": driver_id,
            "current_odometer_km": rng.randint(18, 260) * 1000 + rng.randint(0, 999),
            "note": None,
        }
        ref = db.collection("vehicles").document()
        ref.set(doc)
        vehicles.append({"id": ref.id, **doc})
    return vehicles


def incident_time() -> datetime:
    # 70% trong 30 ngày gần nhất; giờ dồn vào khung dễ buồn ngủ (1–5h, 13–15h).
    days = rng.uniform(0, 30) if rng.random() < 0.7 else rng.uniform(30, 88)
    hour = rng.choice([1, 2, 3, 3, 4, 4, 5, 13, 14, 14, 15, 22, 23] + list(range(6, 22)))
    t = (NOW - timedelta(days=days)).astimezone(timezone(timedelta(hours=7)))
    t = t.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))
    return min(t, NOW).astimezone(timezone.utc)


def seed_incidents(drivers: list[dict]) -> int:
    n = 0
    for d in drivers:
        if not d["plan"]:
            continue
        drowsy, distract = d["plan"]
        for kind, count, points in (("drowsiness", drowsy, 10), ("distraction", distract, 5)):
            for _ in range(count):
                db.collection("incidents").add({
                    "demo": True,
                    "driver_id": d["id"],
                    "trip_id": None,
                    "type": kind,
                    "points": points,
                    "confidence": round(rng.uniform(0.72, 0.98), 2),
                    "detected_at": incident_time(),
                    "snapshot_url": None,
                    "clip_url": None,
                    "note": None,
                })
                n += 1
    return n


def seed_driver_reports(drivers: list[dict]) -> int:
    reporters = [d for d in drivers if d["status"] in ("active", "inactive")]
    for i, note in enumerate(REPORT_NOTES):
        created = ago(days=rng.uniform(0, 25), hours=rng.uniform(0, 12))
        resolved = i >= 6  # 6 báo cáo mới, 14 đã xử lý
        db.collection("driver_reports").add({
            "demo": True,
            "driver_id": reporters[i % len(reporters)]["id"],
            "note": note,
            "photo_url": None,
            "status": "resolved" if resolved else "new",
            "created_at": created,
            "resolved_at": created + timedelta(hours=rng.uniform(0.5, 6)) if resolved else None,
            "resolved_by": DEMO_ADMIN if resolved else None,
        })
    return len(REPORT_NOTES)


def seed_maintenance(vehicles: list[dict]) -> int:
    # (trạng thái, số ngày so với hôm nay của ngày hẹn)
    plan = (
        [("done", -rng.randint(5, 175)) for _ in range(12)]
        + [("pending", rng.randint(2, 6)) for _ in range(3)]  # sắp tới hạn (chuông)
        + [("pending", rng.randint(15, 60)) for _ in range(3)]
        + [("overdue", -rng.randint(2, 12)) for _ in range(3)]
        + [("awaiting", -rng.randint(0, 3)) for _ in range(2)]
        + [("rejected", rng.randint(1, 4))]
    )
    proof = None
    with_driver = [v for v in vehicles if v["driver_id"]]
    for i, (state, offset) in enumerate(plan):
        v = vehicles[i % len(vehicles)]
        if state == "awaiting" and not v["driver_id"]:
            v = with_driver[i % len(with_driver)]  # cần tài xế đứng tên báo cáo
        mtype = list(MAINT_TYPES)[i % len(MAINT_TYPES)]
        low, high = MAINT_TYPES[mtype]
        cost = round(rng.randint(low, high), -4)
        scheduled = NOW + timedelta(days=offset)
        km = v["current_odometer_km"]
        doc = {
            "demo": True,
            "vehicle_id": v["id"],
            "driver_id": None,
            "vendor": rng.choice(VENDORS),
            "type": mtype,
            "scheduled_date": scheduled,
            "status": "pending",
            "odometer": None,
            "interval_km": 5000 if mtype == "oil_change" else None,
            "due_odometer_km": km + rng.randint(200, 3000) if mtype == "oil_change" else None,
            "remind_days_before": 7,
            "remind_km_before": 500,
            "cost": None,
            "note": None,
        }
        if state == "done":
            doc.update({
                "status": "done", "cost": cost, "odometer": km - rng.randint(500, 20000),
                "confirmed_at": scheduled, "confirmed_by": DEMO_ADMIN, "due_odometer_km": None,
            })
        elif state == "awaiting":
            proof = proof or upload_proof_image("HOA DON GARA")
            doc.update({
                "status": "awaiting_confirmation",
                "driver_submission": {
                    "photo_url": proof, "odometer": km + rng.randint(50, 400), "cost": cost,
                    "note": "Đã làm xong, gara thay thêm lọc gió" if i % 2 else None,
                    "submitted_by": v["driver_id"], "submitted_at": ago(hours=rng.uniform(1, 30)),
                },
            })
        elif state == "rejected":
            doc["rejection"] = {
                "reason": "Ảnh hoá đơn bị mờ, chụp lại giúp mình",
                "rejected_by": DEMO_ADMIN,
                "rejected_at": ago(days=1),
                "submission": None,
            }
        db.collection("maintenance_schedules").add(doc)
    return len(plan)


def seed_inspections(vehicles: list[dict]) -> int:
    plan = (
        [("passed", -rng.randint(10, 170)) for _ in range(9)]
        + [("failed", -rng.randint(20, 60))]
        + [("pending", rng.randint(5, 14)) for _ in range(3)]  # sắp hết hạn (chuông)
        + [("pending", rng.randint(30, 200)) for _ in range(3)]
        + [("overdue", -rng.randint(1, 10)) for _ in range(2)]
        + [("awaiting", -rng.randint(0, 2)) for _ in range(2)]
    )
    proof = None
    with_driver = [v for v in vehicles if v["driver_id"]]
    for i, (state, offset) in enumerate(plan):
        v = vehicles[(i * 3) % len(vehicles)]
        if state == "awaiting" and not v["driver_id"]:
            v = with_driver[i % len(with_driver)]  # cần tài xế đứng tên báo cáo
        expiry = NOW + timedelta(days=offset)
        fee = rng.choice([340_000, 560_000])
        road = rng.choice([1_560_000, 2_160_000, 3_240_000])
        doc = {
            "demo": True,
            "vehicle_id": v["id"],
            "driver_id": None,
            "station": rng.choice(STATIONS),
            "appointment_at": expiry - timedelta(days=rng.randint(2, 7), hours=-9) if state != "pending" or offset < 15 else None,
            "old_sticker_expiry": expiry,
            "status": "pending",
            "result": None,
            "remind_days_before": 15,
            "inspection_fee": None,
            "road_fee": None,
            "note": None,
        }
        if state in ("passed", "failed"):
            doc.update({
                "status": "done", "result": state, "inspection_fee": fee,
                "road_fee": road if state == "passed" else None,
                "confirmed_at": expiry - timedelta(days=3), "confirmed_by": DEMO_ADMIN,
                "note": "Trượt do đèn pha lệch, hẹn kiểm lại" if state == "failed" else None,
            })
        elif state == "awaiting":
            proof = proof or upload_proof_image("TEM DANG KIEM")
            doc.update({
                "status": "awaiting_confirmation",
                "driver_submission": {
                    "photo_url": proof, "odometer": v["current_odometer_km"] + rng.randint(30, 300),
                    "result": "passed", "inspection_fee": fee, "road_fee": road,
                    "new_sticker_expiry": expiry + timedelta(days=365), "note": None,
                    "submitted_by": v["driver_id"], "submitted_at": ago(hours=rng.uniform(2, 20)),
                },
            })
        db.collection("vehicle_inspections").add(doc)
    return len(plan)


def seed_kb() -> int:
    for article in DEMO_KB:
        created = kb_service.create_document(KbDocumentIn(**article), KB_AUTHOR)
        db.collection(kb_service.COLLECTION).document(created["id"]).update({"demo": True})
    return len(DEMO_KB)


# ── Xoá ──────────────────────────────────────────────────────────────────
def clean() -> None:
    for c in COLLECTIONS:
        docs = list(db.collection(c).where("demo", "==", True).stream())
        for d in docs:
            d.reference.delete()
        print(f"  {c:24} xoá {len(docs)}")
    kb_docs = list(db.collection(kb_service.COLLECTION).where("demo", "==", True).stream())
    for d in kb_docs:
        kb_service.delete_document(d.id)
    print(f"  {'kb_documents':24} xoá {len(kb_docs)}")
    users = 0
    for i in range(1, len(NAMES) + 1):
        try:
            u = firebase_auth.get_user_by_email(f"demo.taixe{i:02d}@{EMAIL_DOMAIN}")
        except firebase_auth.UserNotFoundError:
            continue
        firebase_auth.delete_user(u.uid)
        users += 1
    print(f"  {'tài khoản đăng nhập':24} xoá {users}")
    blobs = list(bucket.list_blobs(prefix=PROOF_PREFIX)) if bucket else []
    for b in blobs:
        b.delete()
    print(f"  {'ảnh mẫu':24} xoá {len(blobs)}")


def main() -> None:
    if "--clean" in sys.argv:
        print("Xoá dữ liệu mẫu…")
        clean()
        print("Xong.")
        return
    if has_demo_data():
        print("Đã có dữ liệu mẫu — chạy `python scripts/seed_demo.py --clean` trước nếu muốn tạo lại.")
        return
    print("Tạo dữ liệu mẫu…")
    drivers = seed_drivers()
    print(f"  tài xế              {len(drivers)}")
    vehicles = seed_vehicles(drivers)
    print(f"  xe                  {len(vehicles)}")
    print(f"  sự cố an toàn       {seed_incidents(drivers)}")
    print(f"  báo cáo từ tài xế   {seed_driver_reports(drivers)}")
    print(f"  lịch bảo trì        {seed_maintenance(vehicles)}")
    print(f"  hồ sơ đăng kiểm     {seed_inspections(vehicles)}")
    print(f"  tài liệu tri thức   {seed_kb()}")
    print(f"Xong. Tài xế mẫu đăng nhập: demo.taixe01@{EMAIL_DOMAIN} … mật khẩu {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
