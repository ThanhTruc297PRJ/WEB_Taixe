"""RAG Retriever + Prompt Builder + gọi LLM (TASK-B07 SUB-02/03).

LLM: Google Gemini (gói free). Nếu chưa đặt GEMINI_API_KEY thì degrade sang chế
độ "chỉ trích đoạn tài liệu" — vẫn chạy, không tốn tiền, không cần key.
"""

import logging
import os

from app.core.vectorstore import collection
from app.services.intent_router import INTENT_CATEGORY

_log = logging.getLogger("driver_monitoring.rag")
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_model = None
_model_tried = False


def _get_model():
    """Lazy init — chỉ khi có GEMINI_API_KEY. Hỗ trợ cả format cũ (AIza...)
    lẫn format mới (AQ...) của Google AI Studio."""
    global _model, _model_tried
    if _model_tried:
        return _model
    _model_tried = True

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(_GEMINI_MODEL)
    except Exception as e:  # noqa: BLE001
        _log.warning("Không khởi tạo được Gemini: %s", e)
        _model = None
    return _model


_BASE_RULES = (
    "Bạn là trợ lý an toàn lái xe của hệ thống Driver Safety Monitoring. "
    "Trả lời ngắn gọn, bằng tiếng Việt, giọng thân thiện. "
    "Không suy đoán ngoài thông tin được cung cấp."
)

# Prompt builder theo từng ý định (SUB-03).
_INTENT_PROMPT = {
    "safety": (
        _BASE_RULES
        + " Dựa vào NGỮ CẢNH bên dưới để trả lời câu hỏi về an toàn lái xe "
        "(buồn ngủ, mất tập trung, quyền riêng tư). Nếu ngữ cảnh không đủ, "
        "nói rõ là chưa có thông tin."
    ),
    "traffic_law": (
        _BASE_RULES
        + " Trả lời câu hỏi về luật/quy định giao thông DỰA HOÀN TOÀN vào "
        "NGỮ CẢNH (trích dẫn quy định). Không có trong ngữ cảnh thì nói chưa "
        "có thông tin, khuyên tài xế tra cứu văn bản chính thức."
    ),
    "maintenance": (
        _BASE_RULES
        + " Trả lời câu hỏi về bảo trì/kỹ thuật xe dựa vào NGỮ CẢNH (cẩm nang "
        "xe). Nếu là việc cần thợ, khuyên mang xe tới gara."
    ),
    "directions": (
        _BASE_RULES
        + " Người dùng đang hỏi đường/vị trí. Nói rõ trợ lý không hỗ trợ chỉ "
        "đường; hướng dẫn họ dùng tính năng Bản đồ trong ứng dụng. Nhắc không "
        "thao tác điện thoại khi đang lái."
    ),
    "chitchat": (
        _BASE_RULES
        + " Người dùng chỉ muốn trò chuyện cho đỡ buồn ngủ. Trả lời vui vẻ, "
        "ngắn, và nhắc nhẹ về việc tập trung lái xe. KHÔNG cần ngữ cảnh."
    ),
}


# Khoảng cách vector lớn hơn ngưỡng này -> coi như không liên quan (bỏ đoạn).
_RELEVANCE_MAX_DISTANCE = 1.3


def _retrieve(question: str, category: str | None, n_results: int):
    kwargs = {
        "query_texts": [question],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if category:
        kwargs["where"] = {"category": category}
    res = collection.query(**kwargs)
    docs = res["documents"][0] if res.get("documents") else []
    metas = res["metadatas"][0] if res.get("metadatas") else []
    dists = res["distances"][0] if res.get("distances") else [0] * len(docs)

    kept = [
        (d, m)
        for d, m, dist in zip(docs, metas, dists)
        if dist <= _RELEVANCE_MAX_DISTANCE
    ]
    docs = [d for d, _ in kept]
    sources = sorted({(m.get("title") or m.get("source")) for _, m in kept if m})
    return docs, sources


def answer(question: str, intent: str = "safety", n_results: int = 4) -> dict:
    category = INTENT_CATEGORY.get(intent, "safety")
    use_rag = category is not None

    docs, sources = ([], [])
    if use_rag:
        docs, sources = _retrieve(question, category, n_results)

    model = _get_model()

    if model is not None:
        try:
            context = "\n\n---\n\n".join(docs) if docs else "(không có)"
            system = _INTENT_PROMPT.get(intent, _INTENT_PROMPT["safety"])
            prompt = (
                f"{system}\n\nNGỮ CẢNH:\n{context}\n\nCÂU HỎI: {question}"
                if use_rag
                else f"{system}\n\nCÂU HỎI: {question}"
            )
            reply = model.generate_content(prompt)
            text = (reply.text or "").strip()
            if text:
                return {
                    "answer": text,
                    "sources": sources,
                    "intent": intent,
                    "llm": True,
                }
        except Exception as e:  # noqa: BLE001
            _log.warning("Gọi Gemini lỗi (%s) — dùng chế độ trích đoạn.", e)

    # Chưa cấu hình LLM / LLM lỗi -> chế độ trích đoạn (miễn phí).
    return _fallback_answer(intent, docs, sources)


def _fallback_answer(intent: str, docs: list[str], sources: list[str]) -> dict:
    note = (
        "⚠️ Chưa dùng được LLM (thiếu GEMINI_API_KEY) — đang ở chế độ trích "
        "tài liệu. Lấy key miễn phí tại aistudio.google.com/apikey.\n\n"
    )
    if intent == "chitchat":
        msg = (
            "Chào bạn! Mình là trợ lý an toàn lái xe. Bạn cứ tập trung lái, cần "
            "hỏi gì về an toàn / luật giao thông / bảo trì xe thì nhắn mình nhé."
        )
    elif intent == "directions":
        msg = (
            "Mình không hỗ trợ chỉ đường. Bạn dùng mục Bản đồ trong ứng dụng, và "
            "nhớ đừng thao tác điện thoại khi đang lái."
        )
    elif not docs:
        msg = (
            "Chưa tìm thấy tài liệu liên quan. Thử hỏi cụ thể hơn về buồn ngủ, "
            "mất tập trung, luật giao thông hoặc bảo trì xe."
        )
    else:
        body = "\n\n".join(f"• {d.strip()}" for d in docs[:3])
        msg = f"Đoạn tài liệu liên quan nhất:\n\n{body}"
    return {"answer": note + msg, "sources": sources, "intent": intent, "llm": False}
