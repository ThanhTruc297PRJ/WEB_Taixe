"""Test luồng: đăng ký -> chưa xác thực email thì KHÔNG duyệt được -> xác
thực -> duyệt được (+ gửi mail, best-effort). Cần backend chạy.

    python scripts/sim_email_verification.py
"""

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
TEST_EMAIL = os.getenv("TEST_DRIVER_EMAIL", "sim-verify@example.com")
_last = None


def _key():
    k = os.getenv("FIREBASE_API_KEY")
    if k:
        return k
    env = pathlib.Path(__file__).resolve().parents[2] / "website" / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("VITE_FIREBASE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("thiếu FIREBASE_API_KEY")


API_KEY = _key()


def token(uid):
    ct = auth.create_custom_token(uid).decode()
    r = urllib.request.urlopen(urllib.request.Request(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}",
        data=json.dumps({"token": ct, "returnSecureToken": True}).encode(),
        headers={"Content-Type": "application/json"}))
    return json.load(r)["idToken"]


def call(method, path, tok, payload=None):
    global _last
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            _last = None
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        d = e.read().decode()
        try:
            d = json.loads(d).get("detail", d)
        except Exception:
            pass
        _last = d
        return e.code, d


def ok(label, cond):
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
    if not cond:
        if _last is not None:
            print(f"    body: {_last}")
        raise SystemExit(1)


def main():
    admin = auth.get_user_by_email(ADMIN_EMAIL)
    atok = token(admin.uid)

    try:
        old = auth.get_user_by_email(TEST_EMAIL)
        auth.delete_user(old.uid)
    except auth.UserNotFoundError:
        pass
    driver = auth.create_user(email=TEST_EMAIL, password="test123456")
    dtok = token(driver.uid)

    try:
        print("1) Đăng ký hồ sơ (chưa xác thực email)")
        s, reg = call("POST", "/drivers/register", dtok,
                      {"name": "Sim Verify", "phone": "0900000099",
                       "license_number": "SIM-VER"})
        ok("201", s == 201)
        ok("email_verified = False lúc đăng ký", reg["email_verified"] is False)

        print("\n2) GET /drivers/me đồng bộ từ Firebase Auth -> vẫn False")
        s, me = call("GET", "/drivers/me", dtok)
        ok("200", s == 200)
        ok("email_verified vẫn False (chưa bấm link)", me["email_verified"] is False)

        print("\n3) Admin duyệt khi CHƯA xác thực -> 400")
        s, _ = call("PUT", f"/drivers/{driver.uid}/approve", atok)
        ok("400 (chưa xác thực thì không duyệt được)", s == 400)
        s, me = call("GET", "/drivers/me", dtok)
        ok("hồ sơ vẫn pending", me["status"] == "pending")

        print("\n4) Giả lập tài xế bấm link xác thực (Admin SDK set email_verified=True)")
        auth.update_user(driver.uid, email_verified=True)

        print("\n5) GET /drivers/me đồng bộ lại -> True")
        s, me = call("GET", "/drivers/me", dtok)
        ok("email_verified đồng bộ thành True", me["email_verified"] is True)

        print("\n6) Admin duyệt lại -> thành công")
        s, approved = call("PUT", f"/drivers/{driver.uid}/approve", atok)
        ok("200", s == 200)
        ok("status = active", approved["status"] == "active")

        print("\nTẤT CẢ PASS ✔")
    finally:
        auth.delete_user(driver.uid)
        app.core.firebase.db.collection("drivers").document(driver.uid).delete()
        print("Đã dọn dữ liệu test")


if __name__ == "__main__":
    main()
