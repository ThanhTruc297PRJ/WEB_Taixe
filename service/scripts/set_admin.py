"""Cấp / thu hồi custom claim `admin` cho 1 user Firebase.

Chạy từ thư mục service/ (cần .env + serviceAccountKey.json như khi chạy app):

    python scripts/set_admin.py admin@example.com
    python scripts/set_admin.py admin@example.com --revoke

Claim chỉ xuất hiện trong ID token sau khi user đăng nhập lại (token cũ đã bị
revoke ở dưới nên lần refresh kế tiếp sẽ nhận claim mới).
"""

import argparse
import pathlib
import sys

# Cho phép `import app...` khi chạy trực tiếp `python scripts/set_admin.py`
# (Python chỉ thêm thư mục scripts/ vào sys.path, không thêm service/).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401 — import để khởi tạo firebase_admin
from firebase_admin import auth  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("--revoke", action="store_true")
    args = parser.parse_args()

    user = auth.get_user_by_email(args.email)
    claims = dict(user.custom_claims or {})
    if args.revoke:
        claims.pop("admin", None)
    else:
        claims["admin"] = True

    auth.set_custom_user_claims(user.uid, claims)
    auth.revoke_refresh_tokens(user.uid)
    print(
        f"{'Đã thu hồi' if args.revoke else 'Đã cấp'} admin cho "
        f"{args.email} (uid={user.uid})"
    )


if __name__ == "__main__":
    main()
