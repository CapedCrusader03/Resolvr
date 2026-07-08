import hashlib
import os
import uuid
import logging
import json
from typing import Any

from resolvr.schemas.models import ParsedDocument
from resolvr.ingestion.text_parser import parse_text_file
from resolvr.ingestion.pdf_parser import parse_selectable_pdf
from resolvr.ingestion.vision_parser import parse_scanned_pdf_with_gemini
from resolvr.ingestion.excel_parser import parse_excel_or_csv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def get_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks of 4KB
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_transactions_from_text_via_llm(raw_text: str) -> list[dict[str, Any]]:
    """Use Gemini to extract a list of structured transactions from raw text content."""
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. Cannot extract transactions via LLM.")
        return []
        
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        prompt = (
            "You are an expert financial auditor. Analyze this raw text content from a document "
            "(like a bank statement, expense report, or diary note) and extract all individual transactions. "
            "Return the list of transactions as a valid JSON object. "
            "Strictly return ONLY the raw JSON object, without markdown formatting or code blocks. "
            "Format the JSON like this:\n"
            "{\n"
            "  \"transactions\": [\n"
            "    {\n"
            "      \"merchant\": \"name of the merchant or vendor (string, or null)\",\n"
            "      \"transaction_date\": \"date in YYYY-MM-DD format (string, or null)\",\n"
            "      \"total_amount\": \"total amount as a float number (number, or null)\",\n"
            "      \"line_items\": [\"list of individual line item descriptions and prices if visible (array of strings)\"],\n"
            "      \"category\": \"inferred expense category like meals, software, travel, etc. (string, or null)\",\n"
            "      \"confidence_score\": \"confidence score between 0.0 and 1.0 (number)\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "text", "text": f"Document text:\n{raw_text}"}
            ]
        )
        
        response = llm.invoke([message])
        response_text = response.content
        if isinstance(response_text, list):
            response_text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response_text
            )
        else:
            response_text = str(response_text)
            
        # Clean markdown code block wraps if any
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        else:
            response_text = response_text.strip()
            
        data = json.loads(response_text)
        txs = data.get("transactions", [])
        
        # Set default values if keys are missing
        for tx in txs:
            tx["ingestion_method"] = "text"
            if "confidence_score" not in tx:
                tx["confidence_score"] = 0.95
        return txs
    except Exception as e:
        logger.error(f"Failed to extract transactions from text via LLM: {e}")
        return []

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
        if GOOGLE_API_KEY:
            logger.info(f"Extracting transactions from text/markdown via LLM...")
            extracted_transactions = extract_transactions_from_text_via_llm(raw_text)
        else:
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
            logger.info(f"Extracting transactions from selectable PDF text via LLM...")
            if GOOGLE_API_KEY:
                extracted_transactions = extract_transactions_from_text_via_llm(raw_text)
                ingestion_method = "ocr"
            else:
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
