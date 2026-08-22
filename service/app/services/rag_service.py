import pathlib

import anthropic
import chromadb

CHROMA_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "chroma_store"

_collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(
    "driver_safety_kb"
)
_claude = None


def _get_claude() -> anthropic.Anthropic:
    global _claude
    if _claude is None:
        _claude = anthropic.Anthropic()
    return _claude


SYSTEM_PROMPT = (
    "Bạn là trợ lý an toàn lái xe của hệ thống Driver Safety Monitoring. "
    "Trả lời dựa trên ngữ cảnh được cung cấp bên dưới. Nếu ngữ cảnh không "
    "đủ thông tin để trả lời, hãy nói rõ là bạn không có thông tin đó thay "
    "vì suy đoán. Trả lời ngắn gọn, bằng tiếng Việt."
)


def answer(question: str, n_results: int = 4) -> dict:
    results = _collection.query(query_texts=[question], n_results=n_results)
    documents = results["documents"][0] if results["documents"] else []
    sources = [meta["source"] for meta in results["metadatas"][0]] if results["metadatas"] else []

    context = "\n\n---\n\n".join(documents) if documents else "(không tìm thấy tài liệu liên quan)"

    reply = _get_claude().messages.create(
        model="claude-sonnet-5",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Ngữ cảnh:\n{context}\n\nCâu hỏi: {question}",
            }
        ],
    )

    return {
        "answer": reply.content[0].text,
        "sources": sorted(set(sources)),
    }
