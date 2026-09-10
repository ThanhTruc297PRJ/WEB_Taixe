"""Test luồng app tài xế gửi sự cố kèm clip — cần backend chạy ở
http://127.0.0.1:8000 và FIREBASE_STORAGE_BUCKET trong .env.

    python scripts/sim_incident_report.py

  1. Tạo tài xế test + duyệt
  2. POST /incidents/report (multipart: clip + type + detected_at + confidence)
  3. Kiểm tra: 201, có clip_url, points mặc định = 10 (drowsiness)
  4. Tải lại clip_url -> 200
  5. Dọn: xoá incident + file Storage + tài xế
"""

import io
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
TEST_EMAIL = os.getenv("TEST_DRIVER_EMAIL", "sim-incident@example.com")
_last_body = None


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


def _multipart(fields: dict, file_field: str, filename: str, data: bytes) -> tuple:
    boundary = uuid.uuid4().hex
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        buf.write(f"{v}\r\n".encode())
    ctype = mimetypes.guess_type(filename)[0] or "video/mp4"
    buf.write(f"--{boundary}\r\n".encode())
    buf.write(
        f'Content-Disposition: form-data; name="{file_field}"; '
        f'filename="{filename}"\r\n'.encode()
    )
    buf.write(f"Content-Type: {ctype}\r\n\r\n".encode())
    buf.write(data)
    buf.write(f"\r\n--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


def call(method, path, token, body=None, ctype="application/json"):
    global _last_body
    req = urllib.request.Request(
        f"{API}{path}", data=body, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": ctype},
    )
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


def expect(label, got, want):
    ok = got == want
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if not ok:
        if _last_body is not None:
            print(f"    body: {_last_body}")
        raise SystemExit(1)


def main():
    if fb.bucket is None:
        raise SystemExit("Chưa cấu hình FIREBASE_STORAGE_BUCKET trong .env")

    admin = auth.get_user_by_email(ADMIN_EMAIL)
    admin_token = id_token_for(admin.uid)

    try:
        old = auth.get_user_by_email(TEST_EMAIL)
        auth.delete_user(old.uid)
    except auth.UserNotFoundError:
        pass
    driver = auth.create_user(email=TEST_EMAIL, password="test123456")
    db = fb.db
    incident_id = None

    try:
        dtok = id_token_for(driver.uid)
        call("POST", "/drivers/register", dtok, json.dumps(
            {"name": "Sim Incident", "phone": "0900000007",
             "license_number": "SIM-INC"}).encode())
        call("PUT", f"/drivers/{driver.uid}/approve", admin_token)
        time.sleep(1)
        dtok = id_token_for(driver.uid)

        print("\n1) Gửi sự cố kèm clip")
        fake_clip = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 4096  # 4KB giả .mp4
        body, ctype = _multipart(
            {"type": "drowsiness",
             "detected_at": "2026-09-10T09:30:00Z",
             "confidence": "0.88"},
            "clip", "clip.mp4", fake_clip,
        )
        s, inc = call("POST", "/incidents/report", dtok, body, ctype)
        expect("POST /incidents/report", s, 201)
        incident_id = inc["id"]
        expect("driver_id = uid", inc["driver_id"], driver.uid)
        expect("type", inc["type"], "drowsiness")
        expect("points mặc định", inc["points"], 10)
        expect("có clip_url", bool(inc.get("clip_url")), True)
        print(f"    clip_url = {inc['clip_url'][:80]}...")

        print("\n2) Tải lại clip_url")
        with urllib.request.urlopen(inc["clip_url"]) as r:
            downloaded = r.read()
        expect("HTTP 200 + đúng độ dài", len(downloaded), len(fake_clip))

        print("\n3) Sự cố nằm trong danh sách admin")
        s, rows = call("GET", f"/incidents/?driver_id={driver.uid}", admin_token)
        expect("GET /incidents", s, 200)
        expect("có sự cố vừa tạo", incident_id in {x["id"] for x in rows}, True)

        print("\nTẤT CẢ PASS ✔")
    finally:
        if incident_id:
            call("DELETE", f"/incidents/{incident_id}", admin_token)
        for blob in fb.bucket.list_blobs(prefix=f"incident_clips/{driver.uid}/"):
            blob.delete()
        auth.delete_user(driver.uid)
        db.collection("drivers").document(driver.uid).delete()
        print("Đã dọn dữ liệu test")


if __name__ == "__main__":
    main()
