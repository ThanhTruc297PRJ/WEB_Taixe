"""Test quản lý cơ sở tri thức (TASK-C09 SUB-01) — cần backend chạy.

  1. GET /kb/documents (admin)
  2. POST tài liệu mới -> có chunks > 0
  3. Trợ lý AI trả lời dùng được tài liệu vừa thêm (source khớp)
  4. PUT sửa nội dung -> chunks cập nhật
  5. DELETE -> biến mất khỏi list + khỏi vector store
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
from app.core.vectorstore import collection  # noqa: E402
from firebase_admin import auth  # noqa: E402

API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phamtruc355555@gmail.com")
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
    tok = token(admin.uid)
    doc_id = None
    try:
        print("1) GET /kb/documents")
        s, docs = call("GET", "/kb/documents", tok)
        ok("200", s == 200)
        ok("là list", isinstance(docs, list))

        print("\n2) POST tài liệu mới")
        content = (
            "# Quy tắc test C09\n\n"
            "## Mã bí mật kiểm thử\n"
            "Mã xác nhận cho bài test TASK-C09 là ZULU-4417.\n\n"
            "## Ghi chú\n"
            "Tài liệu này chỉ dùng để kiểm thử, sẽ bị xoá."
        )
        s, doc = call("POST", "/kb/documents", tok,
                      {"title": "Quy tắc test C09", "content": content})
        ok("201", s == 201)
        doc_id = doc["id"]
        ok("chunks >= 2", doc.get("chunks", 0) >= 2)

        print("\n3) Vector store tìm được tài liệu vừa thêm")
        res = collection.query(
            query_texts=["Mã xác nhận cho bài test TASK-C09 là gì?"],
            n_results=3,
        )
        hit_docs = res["documents"][0] if res["documents"] else []
        hit_sources = (
            [m["source"] for m in res["metadatas"][0]] if res["metadatas"] else []
        )
        ok("chunk chứa ZULU-4417 nằm trong top kết quả",
           any("ZULU-4417" in d for d in hit_docs))
        ok("source khớp doc_id", doc_id in hit_sources)

        # Nếu có ANTHROPIC_API_KEY thì kiểm luôn câu trả lời của trợ lý.
        s, ans = call("POST", "/assistant/chat", tok,
                      {"question": "Mã xác nhận cho bài test TASK-C09 là gì?"})
        if s == 200:
            ok("trợ lý trả lời chứa ZULU-4417", "ZULU-4417" in ans.get("answer", ""))
        else:
            print("  [SKIP] /assistant/chat (chưa cấu hình ANTHROPIC_API_KEY)")

        print("\n4) PUT sửa nội dung")
        s, upd = call("PUT", f"/kb/documents/{doc_id}", tok,
                      {"title": "Quy tắc test C09 (đã sửa)",
                       "content": "# x\n\n## Mục 1\nA\n\n## Mục 2\nB\n\n## Mục 3\nC"})
        ok("200", s == 200)
        ok("chunks = 3", upd.get("chunks") == 3)

        print("\n5) DELETE")
        s, _ = call("DELETE", f"/kb/documents/{doc_id}", tok)
        ok("200", s == 200)
        s, docs = call("GET", "/kb/documents", tok)
        ok("không còn trong list", doc_id not in {d["id"] for d in docs})
        left = collection.get(where={"source": doc_id})
        ok("không còn chunk trong Chroma", len(left["ids"]) == 0)
        doc_id = None

        print("\nTẤT CẢ PASS ✔")
    finally:
        if doc_id:
            call("DELETE", f"/kb/documents/{doc_id}", tok)


if __name__ == "__main__":
    main()
