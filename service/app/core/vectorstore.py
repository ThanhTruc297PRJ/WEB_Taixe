import pathlib

import chromadb

# Chroma vector store dùng chung cho RAG (rag_service) và quản lý cơ sở tri thức
# (kb_service). Persist ra service/chroma_store/.
CHROMA_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "chroma_store"

collection = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
).get_or_create_collection("driver_safety_kb")
