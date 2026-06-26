from fastapi import APIRouter
from typing import list, dict, Any
from resolvr.memory.structured_store import StructuredStore

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("")
def list_documents() -> list[dict[str, Any]]:
    """List all parsed documents stored in the database."""
    docs = StructuredStore.list_documents()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "ingestion_method": doc.ingestion_method,
            "created_at": doc.created_at.isoformat()
        }
        for doc in docs
    ]
