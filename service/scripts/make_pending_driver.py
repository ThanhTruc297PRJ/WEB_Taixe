"""Tạo 1 tài xế test ở trạng thái `pending` (chờ duyệt) rồi để nguyên — để xem
/ thử duyệt trên web admin. KHÔNG tự xoá như sim_driver_flow.py.

    python scripts/make_pending_driver.py            # tạo 1 hồ sơ
    python scripts/make_pending_driver.py --clear    # xoá các hồ sơ test đã tạo
"""

import argparse
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from firebase_admin import auth  # noqa: E402
from app.models.driver import DriverRegister  # noqa: E402
from app.services import driver_service  # noqa: E402

PREFIX = "pending-test-"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    if args.clear:
        n = 0
        for u in auth.list_users().iterate_all():
            if u.email and u.email.startswith(PREFIX):
                auth.delete_user(u.uid)
                fb.db.collection("drivers").document(u.uid).delete()
                n += 1
        print(f"Đã xoá {n} hồ sơ test")
        return

    i = 1
    while True:
        email = f"{PREFIX}{i}@example.com"
        try:
            auth.get_user_by_email(email)
            i += 1
        except auth.UserNotFoundError:
            break

    user = auth.create_user(email=email, password="test123456")
    driver_service.register_driver(
        user.uid,
        email,
        DriverRegister(
            name=f"Tài xế test {i}",
            phone=f"09000000{i:02d}",
            license_number=f"TEST-{i:03d}",
        ),
    )
    print(f"Đã tạo hồ sơ chờ duyệt: {email} (uid={user.uid})")
    print("→ Mở web admin, trang 'Quản lý tài xế' để duyệt / từ chối.")


if __name__ == "__main__":
    main()
