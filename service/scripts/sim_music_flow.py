"""Test end-to-end kiểm duyệt nhạc — cần backend chạy ở http://127.0.0.1:8000.

    python scripts/sim_music_flow.py

  1. Tạo tài xế test + duyệt (để có claim approved)
  2. Tài xế GET /music/search  -> danh sách bài đang bật
  3. Admin GET /music/tracks   -> thấy các bài vừa được ghi
  4. Tài xế POST /music/plays/{id} -> 200
  5. Admin tắt 1 bài            -> tài xế play lại -> 403, search không còn bài đó
  6. Admin bật lại + tài xế báo cáo bài -> reported=True
  7. Dọn dữ liệu test
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

import app.core.firebase  # noqa: E402,F401
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
TEST_EMAIL = os.getenv("TEST_DRIVER_EMAIL", "sim-music@example.com")


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
_last_body = None


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


def call(method, path, token, payload=None):
    global _last_body
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
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
    db = app.core.firebase.db
    seen_ids = []

    try:
        dtok = id_token_for(driver.uid)
        call("POST", "/drivers/register", dtok,
             {"name": "Sim Music", "phone": "0900000009",
              "license_number": "SIM-MUS"})
        call("PUT", f"/drivers/{driver.uid}/approve", admin_token)
        time.sleep(1)
        dtok = id_token_for(driver.uid)

        print("\n1) Tài xế tìm nhạc")
        s, songs = call("GET", "/music/search?q=lofi", dtok)
        expect("GET /music/search", s, 200)
        if not songs:
            raise SystemExit("iTunes không trả kết quả — thử lại sau")
        print(f"    {len(songs)} bài đang bật")
        seen_ids = [x["id"] for x in songs]
        target = seen_ids[0]

        print("\n2) Admin xem toàn bộ danh sách")
        s, tracks = call("GET", "/music/tracks", admin_token)
        expect("GET /music/tracks", s, 200)
        ids = {t["id"] for t in tracks}
        expect("bài vừa tìm có trong danh sách admin", target in ids, True)

        print("\n3) Tài xế bấm phát")
        s, _ = call("POST", f"/music/plays/{target}", dtok)
        expect("POST /music/plays", s, 200)

        print("\n4) Admin tắt bài đó")
        s, t = call("PUT", f"/music/tracks/{target}/toggle", admin_token,
                    {"enabled": False, "reason": "Test tắt"})
        expect("PUT toggle off", s, 200)
        expect("enabled", t.get("enabled"), False)

        print("\n5) Tài xế phát lại -> 403")
        s, _ = call("POST", f"/music/plays/{target}", dtok)
        expect("POST /music/plays (đã tắt)", s, 403)

        print("\n6) Tìm lại -> bài đã tắt không còn")
        s, songs2 = call("GET", "/music/search?q=lofi", dtok)
        expect("target bị loại khỏi kết quả",
               target in {x["id"] for x in songs2}, False)

        print("\n7) Admin bật lại")
        s, t = call("PUT", f"/music/tracks/{target}/toggle", admin_token,
                    {"enabled": True})
        expect("enabled", t.get("enabled"), True)

        print("\n8) Tài xế báo cáo bài")
        s, t = call("POST", f"/music/tracks/{target}/report", dtok,
                    {"reason": "Lời bài hát không phù hợp"})
        expect("POST report", s, 200)
        expect("reported", t.get("reported"), True)

        print("\nTẤT CẢ PASS ✔")
    finally:
        auth.delete_user(driver.uid)
        db.collection("drivers").document(driver.uid).delete()
        for tid in seen_ids:
            db.collection("music_tracks").document(tid).delete()
        print(f"Đã xoá tài xế test + {len(seen_ids)} bài nhạc test")


if __name__ == "__main__":
    main()
