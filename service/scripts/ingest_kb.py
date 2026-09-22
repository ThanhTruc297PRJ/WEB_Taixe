"""Ingest markdown knowledge base files into the Chroma vector store.

Run manually whenever files under knowledge_base/ change:
    python scripts/ingest_kb.py
"""

import pathlib
import re

import chromadb

KB_DIR = pathlib.Path(__file__).resolve().parent.parent / "knowledge_base"
CHROMA_DIR = pathlib.Path(__file__).resolve().parent.parent / "chroma_store"

SECTION_SPLIT = re.compile(r"\n(?=## )")

# Tên file (không đuôi) -> category mà rag_service._retrieve() lọc theo
# INTENT_CATEGORY (xem intent_router.py). File không có trong danh sách này
# mặc định thuộc "safety".
FILE_CATEGORIES = {
    "traffic_law": "traffic_law",
    "vehicle_manual": "vehicle_manual",
}


def chunk_markdown(text: str, source: str, category: str) -> list[dict]:
    title, _, body = text.strip().partition("\n")
    title = title.lstrip("# ").strip()

    chunks = []
    for i, section in enumerate(SECTION_SPLIT.split(body.strip())):
        section = section.strip()
        if not section:
            continue
        chunks.append(
            {
                "id": f"{source}-{i}",
                "text": f"{title}\n{section}",
                "source": source,
                "title": title,
                "category": category,
            }
        )
    return chunks


def main():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection("driver_safety_kb")

    md_files = sorted(KB_DIR.glob("*.md"))
    all_chunks = []
    for md_file in md_files:
        source = md_file.stem
        category = FILE_CATEGORIES.get(source, "safety")
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, source, category)
        all_chunks.extend(chunks)
        print(f"{md_file.name}: {len(chunks)} chunks [{category}]")

    if not all_chunks:
        print(f"No markdown files found in {KB_DIR}")
        return

    collection.upsert(
        ids=[c["id"] for c in all_chunks],
        documents=[c["text"] for c in all_chunks],
        metadatas=[
            {"source": c["source"], "title": c["title"], "category": c["category"]}
            for c in all_chunks
        ],
    )
    print(f"Ingested {len(all_chunks)} chunks from {len(md_files)} files into {CHROMA_DIR}")


if __name__ == "__main__":
    main()
