"""Test lịch sử chat cho kiểm duyệt (TASK-C09 SUB-02) — cần backend chạy.

  1. Ghi 1 log qua chat_log_service
  2. Non-admin GET /assistant/logs -> 403
  3. Admin GET /assistant/logs -> thấy log
  4. Admin DELETE /assistant/logs/{id} -> log biến mất
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
from app.services import chat_log_service  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
NONADMIN_EMAIL = "chatlog-na@example.com"


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
    return json.load(
        urllib.request.urlopen(
            urllib.request.Request(
                "https://identitytoolkit.googleapis.com/v1/accounts:"
                f"signInWithCustomToken?key={API_KEY}",
                data=json.dumps(
                    {"token": ct, "returnSecureToken": True}
                ).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
    )["idToken"]


def req(method, path, tok):
    r = urllib.request.Request(
        f"{API}{path}", method=method, headers={"Authorization": f"Bearer {tok}"}
    )
    try:
        with urllib.request.urlopen(r) as x:
            return x.status, json.load(x)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:120]


def ok(label, cond):
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(1)


def main():
    admin = auth.get_user_by_email(ADMIN_EMAIL)
    atok = token(admin.uid)
    try:
        drv = auth.get_user_by_email(NONADMIN_EMAIL)
    except auth.UserNotFoundError:
        drv = auth.create_user(email=NONADMIN_EMAIL, password="test123456")
    dtok = token(drv.uid)

    try:
        print("1) Ghi log qua chat_log_service")
        chat_log_service.create_log(
            "drv-sim", "taixe-sim@example.com",
            "Buồn ngủ khi lái thì phải làm gì?",
            "Dừng xe nghỉ 15–20 phút ở nơi an toàn...",
            ["kb-drowsiness"],
        )
        print("   ok")

        print("\n2) Non-admin GET /assistant/logs -> 403")
        s, _ = req("GET", "/assistant/logs", dtok)
        ok("bị chặn", s == 403)

        print("\n3) Admin GET /assistant/logs")
        s, logs = req("GET", "/assistant/logs", atok)
        ok("200", s == 200)
        mine = [x for x in logs if x.get("email") == "taixe-sim@example.com"]
        ok("thấy log vừa ghi", len(mine) >= 1)
        lid = mine[0]["id"]

        print("\n4) Admin DELETE log")
        s, _ = req("DELETE", f"/assistant/logs/{lid}", atok)
        ok("200", s == 200)
        s, logs2 = req("GET", "/assistant/logs", atok)
        ok("log đã biến mất", lid not in {x["id"] for x in logs2})

        print("\nTẤT CẢ PASS ✔")
    finally:
        auth.delete_user(drv.uid)


if __name__ == "__main__":
    main()
