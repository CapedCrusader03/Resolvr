import os
import json
import logging
from typing import list
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
import aiofiles

from resolvr.config import UPLOAD_DIR
from resolvr.ingestion.parser_router import ingest_file
from resolvr.ingestion.normalizer import normalize_transaction
from resolvr.memory.structured_store import StructuredStore
from resolvr.memory.semantic_store import SemanticStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

@router.post("")
async def ingest_files(
    files: list[UploadFile] = File(...),
    session_id: str = Form(...)
):
    """Ingest multiple financial files, parse them, index into databases, and stream progress."""
    
    async def progress_stream():
        for file in files:
            filename = file.filename
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            logger.info(f"Ingesting file {filename}...")
            yield f"data: {json.dumps({'status': 'processing', 'file': filename})}\n\n"
            
            # Save file asynchronously
            try:
                async with aiofiles.open(file_path, "wb") as out_file:
                    content = await file.read()
                    await out_file.write(content)
            except Exception as e:
                logger.error(f"Failed to save file {filename}: {e}")
                yield f"data: {json.dumps({'status': 'error', 'file': filename, 'message': f'Save failed: {e}'})}\n\n"
                continue
                
            # Parse file
            try:
                parsed_doc, extracted_txs = ingest_file(file_path)
                
                # Save parsed doc to database
                db_doc = StructuredStore.add_parsed_document(
                    doc_id=parsed_doc.id,
                    filename=parsed_doc.filename,
                    file_type=parsed_doc.file_type,
                    ingestion_method=parsed_doc.ingestion_method,
                    raw_text=parsed_doc.raw_text,
                    file_hash=parsed_doc.hash
                )
                
                # Save transactions to structured SQLite store
                txs_saved = 0
                for tx in extracted_txs:
                    normalized_tx = normalize_transaction(tx, parsed_doc.id)
                    StructuredStore.add_transaction(normalized_tx.dict())
                    txs_saved += 1
                    
                # Index into vector database
                # Split raw text into chunks of e.g. 500 characters for RAG
                text = parsed_doc.raw_text
                if text.strip():
                    chunk_size = 500
                    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
                    SemanticStore.add_document_chunks(
                        doc_id=parsed_doc.id,
                        filename=parsed_doc.filename,
                        text_chunks=chunks
                    )
                    
                yield f"data: {json.dumps({'status': 'done', 'file': filename, 'doc_id': parsed_doc.id, 'transactions_found': txs_saved})}\n\n"
                
            except Exception as e:
                logger.error(f"Failed parsing file {filename}: {e}")
                yield f"data: {json.dumps({'status': 'error', 'file': filename, 'message': f'Parse failed: {e}'})}\n\n"
                
    return StreamingResponse(progress_stream(), media_type="text/event-stream")
