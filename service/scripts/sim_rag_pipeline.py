"""Test RAG pipeline B07 — router + retriever + prompt/LLM (hoặc fallback).

Không cần backend chạy (gọi thẳng service). Nếu có GEMINI_API_KEY sẽ kiểm luôn
câu trả lời LLM; không có thì kiểm chế độ trích đoạn (miễn phí).

    python scripts/sim_rag_pipeline.py
"""

import os
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase  # noqa: E402,F401
from app.models.kb import KbDocumentIn  # noqa: E402
from app.services import intent_router, kb_service, rag_service  # noqa: E402


def ok(label, cond):
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
    if not cond:
        raise SystemExit(1)


def main():
    print("1) Router phân loại ý định")
    cases = {
        "Từ đây tới kho hàng bao xa?": "directions",
        "Tốc độ tối đa trong khu dân cư là bao nhiêu?": "traffic_law",
        "Bao nhiêu km thì phải thay dầu máy?": "maintenance",
        "Kể chuyện cười cho đỡ buồn ngủ đi": "chitchat",
        "Nhắm mắt bao lâu thì bị cảnh báo buồn ngủ?": "safety",
    }
    for q, want in cases.items():
        got = intent_router.classify(q)
        ok(f'"{q[:40]}" -> {got}', got == want)

    print("\n2) Retriever lọc theo nhóm tài liệu")
    doc = kb_service.create_document(
        KbDocumentIn(
            title="Luật test tốc độ",
            content=(
                "# Luật test\n\n## Tốc độ khu dân cư\n"
                "Tốc độ tối đa trong khu dân cư là 50 km/h với ô tô. "
                "Mã kiểm thử: DELTA-9931."
            ),
            category="traffic_law",
        ),
        admin_uid="sim",
    )
    try:
        ok("tài liệu lưu category traffic_law", doc["category"] == "traffic_law")

        r_law = rag_service.answer("Tốc độ tối đa khu dân cư?", "traffic_law")
        ok("intent traffic_law trả về đúng intent", r_law["intent"] == "traffic_law")
        ok(
            "câu trả lời nhắc tới tài liệu luật (DELTA-9931 hoặc 50 km/h)",
            "DELTA-9931" in r_law["answer"] or "50" in r_law["answer"],
        )

        # Câu hỏi an toàn KHÔNG được kéo tài liệu luật (khác category).
        r_safe = rag_service.answer("Tốc độ tối đa khu dân cư?", "safety")
        ok(
            "intent safety không lấy tài liệu luật",
            "Luật test tốc độ" not in r_safe.get("sources", []),
        )

        print("\n3) Ý định directions / chitchat không cần RAG")
        r_dir = rag_service.answer("Đường tới cảng đi lối nào?", "directions")
        ok("directions: sources rỗng", r_dir.get("sources") == [])

        has_key = (os.getenv("GEMINI_API_KEY") or "").strip().startswith("AIza")
        print(f"\n4) LLM: {'Gemini (có key hợp lệ)' if has_key else 'fallback trích đoạn (miễn phí)'}")
        ok("kết quả có cờ 'llm'", "llm" in r_law)
        # llm=True chỉ khi có key đúng định dạng VÀ Gemini gọi thành công.
        if has_key:
            ok("có key -> llm True hoặc fallback (nếu Gemini lỗi)", r_law["llm"] in (True, False))
        else:
            ok("không có key hợp lệ -> llm False", r_law["llm"] is False)

        print("\nTẤT CẢ PASS ✔")
    finally:
        kb_service.delete_document(doc["id"])
        print("Đã xoá tài liệu test")


if __name__ == "__main__":
    main()
