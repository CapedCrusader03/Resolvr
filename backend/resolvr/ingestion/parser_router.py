import hashlib
import os
import uuid
import logging
from typing import Any

from resolvr.schemas.models import ParsedDocument
from resolvr.ingestion.text_parser import parse_text_file
from resolvr.ingestion.pdf_parser import parse_selectable_pdf
from resolvr.ingestion.vision_parser import parse_scanned_pdf_with_gemini
from resolvr.ingestion.excel_parser import parse_excel_or_csv

logger = logging.getLogger(__name__)

def get_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks of 4KB
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ingest_file(file_path: str) -> tuple[ParsedDocument, list[dict[str, Any]]]:
    """Determine MIME/file type, route to the correct parser, and return parsed results."""
    filename = os.path.basename(file_path)
    file_type = os.path.splitext(filename)[1].lower()
    
    file_hash = get_file_hash(file_path)
    doc_id = str(uuid.uuid4())
    
    logger.info(f"Routing file {filename} (extension: {file_type}). Hash: {file_hash}")
    
    raw_text = ""
    extracted_transactions: list[dict[str, Any]] = []
    ingestion_method = "plain_text"
    
    if file_type in [".txt", ".md"]:
        result = parse_text_file(file_path)
        raw_text = result["raw_text"]
        extracted_transactions.append({
            "merchant": result["merchant"],
            "transaction_date": result["transaction_date"],
            "total_amount": result["total_amount"],
            "line_items": result["line_items"],
            "ingestion_method": "text"
        })
        ingestion_method = "plain_text"
        
    elif file_type in [".xlsx", ".xls", ".csv"]:
        result = parse_excel_or_csv(file_path)
        raw_text = result["raw_text"]
        extracted_transactions = result["extracted_transactions"]
        ingestion_method = "table_extract"
        
    elif file_type == ".pdf":
        result = parse_selectable_pdf(file_path)
        if result.get("is_scanned", False):
            # Fallback to Vision API
            logger.info(f"File {filename} is scanned PDF. Invoking Vision Parser...")
            vision_result = parse_scanned_pdf_with_gemini(file_path)
            raw_text = vision_result["raw_text"]
            extracted_transactions = vision_result["extracted_transactions"]
            ingestion_method = "vision"
        else:
            raw_text = result["raw_text"]
            # For selectable PDFs, we can extract text but we still need Gemini to extract 
            # structured transactions out of the raw text if no spreadsheet extraction exists.
            # We'll trigger normalizer/solver steps later, or we can use Gemini to parse the raw text.
            # In our hybrid state machine, let's treat the raw text as the source for retrieval.
            # To populate SQLite immediately for queries, let's parse raw text with Gemini API.
            logger.info(f"Extracting transactions from selectable PDF text via LLM...")
            try:
                # We'll extract structured transactions from selectable text using Gemini
                vision_result = parse_scanned_pdf_with_gemini(file_path)
                extracted_transactions = vision_result["extracted_transactions"]
                ingestion_method = "ocr" # marked as ocr/selectable
            except Exception as e:
                logger.error(f"Failed structured extraction on selectable PDF: {e}")
                # Fallback to empty transaction list, agent can retrieve from ChromaDB later
                extracted_transactions = []
                ingestion_method = "plain_text"
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
        
    # Create ParsedDocument Pydantic model
    parsed_doc = ParsedDocument(
        id=doc_id,
        filename=filename,
        file_type=file_type,
        ingestion_method=ingestion_method,
        raw_text=raw_text,
        hash=file_hash
    )
    
    # Attach source doc id to transactions
    for tx in extracted_transactions:
        tx["source_doc_id"] = doc_id
        
    return parsed_doc, extracted_transactions
