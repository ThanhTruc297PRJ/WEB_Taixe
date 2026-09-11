"""Nạp các file knowledge_base/*.md vào Firestore `kb_documents` + Chroma.

Dùng 1 lần để chuyển KB từ file markdown sang quản lý qua web admin. Sau đó
admin thêm/sửa trực tiếp trên web, không cần ingest_kb.py nữa.

    python scripts/seed_kb.py            # nạp (bỏ qua file đã có title trùng)
    python scripts/seed_kb.py --clear    # xoá sạch kb_documents + chunk trong Chroma
"""

import argparse
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from app.core.vectorstore import collection  # noqa: E402
from app.models.kb import KbDocumentIn  # noqa: E402
from app.services import kb_service  # noqa: E402

KB_DIR = pathlib.Path(__file__).resolve().parent.parent / "knowledge_base"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    if args.clear:
        n = 0
        for d in fb.db.collection(kb_service.COLLECTION).stream():
            kb_service.delete_document(d.id)
            n += 1
        print(f"Đã xoá {n} tài liệu")
        return

    existing_titles = {
        d.get("title") for d in kb_service.list_documents()
    }
    created = 0
    for md in sorted(KB_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        title = text.strip().partition("\n")[0].lstrip("# ").strip() or md.stem
        if title in existing_titles:
            print(f"  bỏ qua (đã có): {title}")
            continue
        doc = kb_service.create_document(
            KbDocumentIn(title=title, content=text), admin_uid="seed"
        )
        created += 1
        print(f"  + {title}  ({doc['chunks']} chunk)")

    print(f"\nXong. Tạo {created} tài liệu. Chroma hiện có {collection.count()} chunk.")


if __name__ == "__main__":
    main()
