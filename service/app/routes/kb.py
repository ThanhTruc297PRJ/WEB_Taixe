from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from app.models.kb import KbDocumentIn
from app.services import kb_service

router = APIRouter(
    prefix="/kb",
    tags=["knowledge base (web admin)"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/documents")
def list_documents():
    return kb_service.list_documents()


@router.get("/documents/{doc_id}")
def get_document(doc_id: str):
    doc = kb_service.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    return doc


@router.post("/documents", status_code=201)
def create_document(
    payload: KbDocumentIn, admin: dict = Depends(get_current_admin)
):
    return kb_service.create_document(payload, admin["uid"])


@router.put("/documents/{doc_id}")
def update_document(
    doc_id: str, payload: KbDocumentIn, admin: dict = Depends(get_current_admin)
):
    doc = kb_service.update_document(doc_id, payload, admin["uid"])
    if doc is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    if not kb_service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    return {"status": "success"}
