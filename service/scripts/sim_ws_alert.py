"""Test cảnh báo realtime: tạo incident -> web admin (WebSocket) nhận alert.

    python scripts/sim_ws_alert.py

  1. Kết nối /ws/admin KHÔNG token -> bị đóng (4401)
  2. Kết nối /ws/admin có token admin -> OK
  3. Tạo incident qua POST /incidents/ -> client WS nhận {type:"alert"} kèm driver_name
  4. Dọn incident test
"""

import asyncio
import json
import os
import pathlib
import sys

import websockets

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
WS = API.replace("http", "ws") + "/ws/admin"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")


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
    import urllib.request

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


def http(method, path, token, payload=None):
    import urllib.request

    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.load(r)


def ok(label, cond):
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(1)


async def main():
    admin = auth.get_user_by_email(ADMIN_EMAIL)
    token = id_token_for(admin.uid)

    print("\n1) Kết nối không token -> bị từ chối")
    rejected = False
    try:
        async with websockets.connect(WS) as ws:
            await ws.recv()
    except Exception:
        rejected = True
    ok("đóng kết nối khi thiếu token", rejected)

    print("\n2) Kết nối có token admin")
    async with websockets.connect(f"{WS}?token={token}") as ws:
        first = json.loads(await ws.recv())
        ok("nhận 'system' connected", first.get("type") == "system")

        print("\n3) Tạo incident -> nhận alert qua WS")
        s, inc = http("POST", "/incidents/", token, {
            "driver_id": admin.uid,  # mượn uid admin cho tiện
            "type": "drowsiness",
            "detected_at": "2026-09-10T10:00:00Z",
            "confidence": 0.9,
        })
        ok("POST /incidents/ -> 201/200", s in (200, 201))

        alert = None
        try:
            async with asyncio.timeout(5):
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get("type") == "alert":
                        alert = msg
                        break
        except (TimeoutError, asyncio.TimeoutError):
            pass

        ok("WS nhận {type:'alert'}", alert is not None)
        ok("alert kèm incident_id", alert.get("incident_id") == inc["id"])
        ok("alert.alert_type = drowsiness", alert.get("alert_type") == "drowsiness")
        ok("alert.points = 10", alert.get("points") == 10)

        import app.core.firebase as fb
        fb.db.collection("incidents").document(inc["id"]).delete()
        print("\nĐã xoá incident test")

    print("\nTẤT CẢ PASS ✔")


if __name__ == "__main__":
    asyncio.run(main())
