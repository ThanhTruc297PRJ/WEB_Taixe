"""E2E toàn luồng sự cố buồn ngủ — biên bản kiểm thử TASK-C08 SUB-01.

Giả lập đúng đường đi của app tài xế (KHÔNG cần Android/emulator):

  tài xế đăng ký -> admin duyệt
  -> web admin mở WebSocket /ws/admin
  -> app tài xế: POST /incidents/report (multipart: clip 10s giả)
       -> backend upload clip lên Storage + tạo incident (points=10)
       -> backend broadcast -> WebSocket
  -> web admin nhận {type:"alert"} (khớp incident_id)
  -> clip_url tải được, incident nằm trong danh sách admin

Cần: backend chạy http://127.0.0.1:8000, FIREBASE_STORAGE_BUCKET trong .env.

    python scripts/sim_e2e.py
"""

import asyncio
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

import websockets

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
WS = API.replace("http", "ws") + "/ws/admin"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
TEST_EMAIL = os.getenv("TEST_DRIVER_EMAIL", "sim-e2e@example.com")
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


def _multipart(fields: dict, name: str, filename: str, data: bytes):
    boundary = uuid.uuid4().hex
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        buf.write(f"{v}\r\n".encode())
    ctype = mimetypes.guess_type(filename)[0] or "video/mp4"
    buf.write(f"--{boundary}\r\n".encode())
    buf.write(
        f'Content-Disposition: form-data; name="{name}"; '
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
    good = got == want
    print(f"  [{'OK ' if good else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if not good:
        if _last_body is not None:
            print(f"    body: {_last_body}")
        raise SystemExit(1)


async def main():
    if fb.bucket is None:
        raise SystemExit("Chưa cấu hình FIREBASE_STORAGE_BUCKET trong .env")

    admin = auth.get_user_by_email(ADMIN_EMAIL)
    if not (admin.custom_claims or {}).get("admin"):
        raise SystemExit(f"{ADMIN_EMAIL} chưa có quyền admin")
    admin_token = id_token_for(admin.uid)

    try:
        old = auth.get_user_by_email(TEST_EMAIL)
        auth.delete_user(old.uid)
    except auth.UserNotFoundError:
        pass
    driver = auth.create_user(email=TEST_EMAIL, password="test123456")
    incident_id = None

    try:
        print("1) Tài xế đăng ký + admin duyệt")
        dtok = id_token_for(driver.uid)
        s, _ = call("POST", "/drivers/register", dtok, json.dumps(
            {"name": "E2E Driver", "phone": "0900000123",
             "license_number": "E2E-01"}).encode())
        expect("POST /drivers/register", s, 201)
        s, _ = call("PUT", f"/drivers/{driver.uid}/approve", admin_token)
        expect("PUT approve", s, 200)
        time.sleep(1)
        dtok = id_token_for(driver.uid)

        print("\n2) Web admin mở WebSocket /ws/admin")
        async with websockets.connect(f"{WS}?token={admin_token}") as ws:
            first = json.loads(await ws.recv())
            expect("nhận 'system connected'", first.get("type"), "system")

            print("\n3) App tài xế: POST /incidents/report (clip 10s giả)")
            clip = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 200_000  # ~200KB
            body, ctype = _multipart(
                {"type": "drowsiness",
                 "detected_at": "2026-09-10T10:45:00Z",
                 "confidence": "0.92"},
                "clip", "clip.mp4", clip)
            s, inc = call("POST", "/incidents/report", dtok, body, ctype)
            expect("POST /incidents/report", s, 201)
            incident_id = inc["id"]
            expect("driver_id = uid", inc["driver_id"], driver.uid)
            expect("points = 10", inc["points"], 10)
            expect("có clip_url", bool(inc.get("clip_url")), True)

            print("\n4) Web admin nhận cảnh báo realtime")
            alert = None
            try:
                async with asyncio.timeout(6):
                    while True:
                        m = json.loads(await ws.recv())
                        if m.get("type") == "alert":
                            alert = m
                            break
            except (TimeoutError, asyncio.TimeoutError):
                pass
            expect("WS nhận {type:'alert'}", alert is not None, True)
            expect("alert.incident_id khớp", alert["incident_id"], incident_id)
            expect("alert.driver_name", alert["driver_name"], "E2E Driver")
            expect("alert.severity", alert["severity"], "medium")

        print("\n5) Clip tải được từ Storage CDN")
        with urllib.request.urlopen(inc["clip_url"]) as r:
            expect("HTTP 200 + đúng độ dài", len(r.read()), len(clip))

        print("\n6) Incident nằm trong danh sách web admin")
        s, rows = call("GET", f"/incidents/?driver_id={driver.uid}", admin_token)
        expect("GET /incidents", s, 200)
        expect("có incident vừa tạo", incident_id in {x["id"] for x in rows}, True)

        print("\n════ E2E TOÀN LUỒNG: PASS ✔ ════")
    finally:
        if incident_id:
            call("DELETE", f"/incidents/{incident_id}", admin_token)
        for blob in fb.bucket.list_blobs(prefix=f"incident_clips/{driver.uid}/"):
            blob.delete()
        auth.delete_user(driver.uid)
        fb.db.collection("drivers").document(driver.uid).delete()
        print("Đã dọn dữ liệu test")


if __name__ == "__main__":
    asyncio.run(main())
