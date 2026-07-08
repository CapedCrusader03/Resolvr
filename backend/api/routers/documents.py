from fastapi import APIRouter
from typing import Any, Optional
from resolvr.memory.structured_store import StructuredStore

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("")
def list_documents(session_id: Optional[str] = None) -> list[dict[str, Any]]:
    """List all parsed documents stored in the database, filtered by session if provided."""
    docs = StructuredStore.list_documents(session_id)
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
