"""Test end-to-end luồng đăng ký + duyệt tài xế — KHÔNG cần app mobile.

Chạy từ thư mục service/ (cần backend đang chạy ở http://127.0.0.1:8000):

    python scripts/sim_driver_flow.py

Script sẽ:
  1. Tạo 1 tài khoản Firebase test cho tài xế
  2. Lấy ID token cho tài xế + cho admin (mint custom token -> đổi qua REST)
  3. Gọi thật các endpoint: /register, /me, /presence, /approve, /reject
  4. Xoá tài khoản test

Cần biến FIREBASE_API_KEY (khoá web) — mặc định lấy từ website/.env.
"""

import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401 — khởi tạo firebase_admin
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
TEST_EMAIL = os.getenv("TEST_DRIVER_EMAIL", "sim-driver@example.com")


def _web_api_key() -> str:
    key = os.getenv("FIREBASE_API_KEY")
    if key:
        return key
    env = pathlib.Path(__file__).resolve().parents[2] / "website" / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("VITE_FIREBASE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("Không tìm thấy FIREBASE_API_KEY / website/.env")


API_KEY = _web_api_key()


def id_token_for(uid: str) -> str:
    """Mint custom token cho uid rồi đổi lấy ID token (giả lập app đăng nhập)."""
    custom = auth.create_custom_token(uid).decode()
    body = json.dumps({"token": custom, "returnSecureToken": True}).encode()
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:"
        f"signInWithCustomToken?key={API_KEY}"
    )
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    return json.load(urllib.request.urlopen(req))["idToken"]


def call(method: str, path: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    global _last_body
    try:
        with urllib.request.urlopen(req) as r:
            _last_body = None
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        try:
            detail = json.loads(detail).get("detail", detail)
        except Exception:
            pass
        _last_body = detail
        return e.code, detail


_last_body = None


def expect(label: str, got, want):
    ok = got == want
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}: got {got}, want {want}")
    if not ok:
        if _last_body is not None:
            print(f"    body: {_last_body}")
        raise SystemExit(1)


def main():
    admin = auth.get_user_by_email(ADMIN_EMAIL)
    if admin.custom_claims is None or admin.custom_claims.get("admin") is not True:
        raise SystemExit(f"{ADMIN_EMAIL} chưa có quyền admin (chạy set_admin.py)")
    admin_token = id_token_for(admin.uid)

    # tài khoản tài xế test — xoá nếu còn sót từ lần trước
    try:
        old = auth.get_user_by_email(TEST_EMAIL)
        auth.delete_user(old.uid)
    except auth.UserNotFoundError:
        pass
    driver = auth.create_user(email=TEST_EMAIL, password="test123456")
    print(f"Tạo tài xế test: {TEST_EMAIL} (uid={driver.uid})")

    try:
        dtok = id_token_for(driver.uid)

        print("\n1) Đăng ký hồ sơ")
        s, b = call("POST", "/drivers/register", dtok,
                    {"name": "Sim Driver", "phone": "0900000001",
                     "license_number": "SIM-001"})
        expect("POST /register", s, 201)

        print("\n2) Đăng ký lần 2 -> 409")
        s, _ = call("POST", "/drivers/register", dtok,
                    {"name": "x", "phone": "y", "license_number": "z"})
        expect("POST /register (trùng)", s, 409)

        print("\n3) GET /me -> pending")
        s, b = call("GET", "/drivers/me", dtok)
        expect("status", b.get("status"), "pending")

        print("\n4) Tài xế pending gọi /presence -> 403")
        s, _ = call("PUT", f"/drivers/{driver.uid}/presence", dtok,
                    {"presence": "online"})
        expect("PUT /presence khi pending", s, 403)

        print("\n5) Admin duyệt")
        s, b = call("PUT", f"/drivers/{driver.uid}/approve", admin_token)
        expect("POST /approve", s, 200)
        expect("status sau duyệt", b.get("status"), "active")
        expect("approved_by", b.get("approved_by"), admin.uid)

        print("\n6) Tài xế lấy token mới, gọi /presence -> 200")
        time.sleep(1)
        dtok = id_token_for(driver.uid)  # token mới có claim approved
        s, _ = call("PUT", f"/drivers/{driver.uid}/presence", dtok,
                    {"presence": "driving"})
        expect("PUT /presence khi active", s, 200)

        print("\n7) Admin từ chối")
        s, b = call("PUT", f"/drivers/{driver.uid}/reject", admin_token,
                    {"reason": "Bằng lái không hợp lệ"})
        expect("PUT /reject", s, 200)
        expect("status", b.get("status"), "rejected")

        print("\n8) Lấy token mới (không còn claim approved) -> /presence 403")
        time.sleep(1)
        dtok = id_token_for(driver.uid)
        s, _ = call("PUT", f"/drivers/{driver.uid}/presence", dtok,
                    {"presence": "online"})
        expect("PUT /presence sau khi bị từ chối", s, 403)

        print("\n9) Đăng ký lại sau khi bị từ chối -> 201")
        s, _ = call("POST", "/drivers/register", dtok,
                    {"name": "Sim Driver 2", "phone": "0900000002",
                     "license_number": "SIM-002"})
        expect("POST /register lại", s, 201)

        print("\nTẤT CẢ PASS ✔")
    finally:
        auth.delete_user(driver.uid)
        db = app.core.firebase.db
        db.collection("drivers").document(driver.uid).delete()
        print(f"Đã xoá tài xế test {driver.uid}")


if __name__ == "__main__":
    main()
