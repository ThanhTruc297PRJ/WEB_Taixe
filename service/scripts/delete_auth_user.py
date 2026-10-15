"""Xoá tài khoản Firebase Auth theo email (không ảnh hưởng Firestore).

Dùng khi tài xế đăng ký bị gián đoạn: Firebase tạo tài khoản nhưng
backend chưa lưu hồ sơ vào Firestore.

Chạy từ thư mục service/:
    python scripts/delete_auth_user.py email1@gmail.com email2@gmail.com
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401
from firebase_admin import auth


def delete_by_email(email: str) -> None:
    try:
        user = auth.get_user_by_email(email)
        auth.delete_user(user.uid)
        print(f"✓ Đã xoá: {email} (uid={user.uid})")
    except auth.UserNotFoundError:
        print(f"✗ Không tìm thấy: {email}")
    except Exception as e:
        print(f"✗ Lỗi khi xoá {email}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("emails", nargs="+", help="Danh sách email cần xoá")
    args = parser.parse_args()
    for email in args.emails:
        delete_by_email(email.strip())
