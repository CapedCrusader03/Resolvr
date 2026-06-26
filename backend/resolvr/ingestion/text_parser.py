import re
from typing import dict, Any
import logging

logger = logging.getLogger(__name__)

def parse_text_file(file_path: str) -> dict[str, Any]:
    """Parse plain text or markdown file and extract text and basic metadata."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Basic heuristic extraction
        # Look for things like "Total: $123.45" or "Amount: 123.45"
        total_match = re.search(r'(?:total|amount|sum|price)[:\-\s]*\$?\s*(\d+(?:\.\d{2})?)', content, re.IGNORECASE)
        total = float(total_match.group(1)) if total_match else None
        
        # Look for dates in text
        date_match = re.search(r'\b(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]\d{4})\b', content)
        date_str = date_match.group(1) if date_match else None
        
        # Simple merchant heuristic (first non-empty line if it doesn't look like a title)
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        merchant = lines[0][:100] if lines else None
        
        return {
            "raw_text": content,
            "merchant": merchant,
            "transaction_date": date_str,
            "total_amount": total,
            "line_items": [],
            "ingestion_method": "text"
        }
    except Exception as e:
        logger.error(f"Error parsing text file {file_path}: {e}")
        raise e
