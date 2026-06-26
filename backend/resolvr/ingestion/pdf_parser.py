import logging
import PyPDF2
from typing import Any


logger = logging.getLogger(__name__)

def parse_selectable_pdf(file_path: str) -> dict[str, Any]:
    """Extract text from a selectable PDF using PyPDF2.
    If the PDF has no text (is scanned), return indicators so we route to vision parser.
    """
    try:
        raw_text_parts = []
        is_scanned = True
        
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text() or ""
                if text.strip():
                    is_scanned = False
                raw_text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                
        raw_text = "\n".join(raw_text_parts)
        
        if is_scanned or len(raw_text.strip()) < 50:
            logger.info(f"PDF {file_path} appears to be scanned or empty. Marking for vision parser.")
            return {
                "raw_text": "",
                "is_scanned": True,
                "ingestion_method": "scanned"
            }
            
        return {
            "raw_text": raw_text,
            "is_scanned": False,
            "ingestion_method": "plain_text"
        }
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        # Return scanned so it falls back to vision parser in case of parsing crash
        return {
            "raw_text": "",
            "is_scanned": True,
            "ingestion_method": "scanned"
        }
