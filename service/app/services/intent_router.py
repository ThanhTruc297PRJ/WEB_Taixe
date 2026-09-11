"""RAG Router — phân loại ý định câu hỏi của tài xế (TASK-B07 SUB-01).

Dùng khớp từ khoá (miễn phí, không gọi LLM). 4 nhóm:
  - directions   : hỏi đường / vị trí  -> không RAG, hướng dẫn dùng bản đồ
  - traffic_law  : hỏi luật giao thông -> RAG trên tài liệu category 'traffic_law'
  - maintenance  : hỏi bảo trì / xe    -> RAG trên category 'vehicle_manual'
  - chitchat     : trò chuyện / giải trí-> trả lời thẳng, không RAG
  - safety       : mặc định (buồn ngủ, mất tập trung, consent...) -> RAG 'safety'
"""

import re
import unicodedata

# Ý định -> category tài liệu để retriever lọc (None = không RAG).
INTENT_CATEGORY = {
    "directions": None,
    "traffic_law": "traffic_law",
    "maintenance": "vehicle_manual",
    "chitchat": None,
    "safety": "safety",
}

# Thứ tự = ưu tiên khi hoà điểm (intent đứng trước thắng).
_KEYWORDS = {
    "traffic_law": [
        "luật giao thông", "quy định giao thông", "tốc độ tối đa",
        "giới hạn tốc độ", "biển báo", "vạch kẻ đường", "làn đường",
        "vượt đèn đỏ", "đèn đỏ", "nồng độ cồn", "bị phạt", "mức phạt",
        "vi phạm giao thông", "bằng lái", "giấy phép lái xe", "nghị định",
        "được phép", "có được phép",
    ],
    "maintenance": [
        "bảo trì", "bảo dưỡng", "thay dầu", "thay nhớt", "thay lốp",
        "vỏ xe", "ắc quy", "má phanh", "phanh xe", "hệ thống phanh",
        "động cơ", "máy xe", "đèn xe", "điều hoà xe", "định kỳ",
        "xe bị hư", "xe hỏng", "sửa xe", "cẩm nang xe", "gara",
    ],
    "directions": [
        "chỉ đường", "đường đi", "đường tới", "đường đến", "bao xa",
        "cách bao nhiêu km", "lộ trình", "quãng đường bao", "đường nào",
        "rẽ trái", "rẽ phải", "ngã tư", "ngã ba", "bản đồ", "định vị",
        "địa chỉ", "gần nhất", "đi lối nào", "làm sao tới", "làm sao đến",
    ],
    "chitchat": [
        "kể chuyện", "chuyện cười", "kể chuyện cười", "buồn quá", "chán quá",
        "tâm sự", "nói chuyện phiếm", "làm quen", "buồn ngủ quá kể",
        "hello", "xin chào", "chào bạn", "chào trợ lý", "bạn là ai",
        "bạn tên gì", "bạn khoẻ không", "khoẻ không",
    ],
}


def _fold(text: str) -> str:
    """Bỏ dấu tiếng Việt + hạ chữ thường — khớp cả khi tài xế gõ không dấu."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    no_mark = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_mark.replace("đ", "d")


_KEYWORDS_FOLDED = {
    intent: [_fold(w) for w in words] for intent, words in _KEYWORDS.items()
}


def classify(question: str) -> str:
    q = " " + re.sub(r"\s+", " ", _fold(question).strip()) + " "
    scores = {intent: 0 for intent in _KEYWORDS_FOLDED}
    for intent, words in _KEYWORDS_FOLDED.items():
        for w in words:
            if w in q:
                scores[intent] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "safety"
