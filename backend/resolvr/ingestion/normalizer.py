import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import dict, Any, Optional
import logging

from resolvr.schemas.models import ExtractedTransaction

logger = logging.getLogger(__name__)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Try to parse a variety of date string formats into a datetime object."""
    if not date_str:
        return None
        
    date_str = date_str.strip()
    # Common formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%d %b %Y",
        "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    # Try basic regex match if formatting is slightly off
    try:
        # Match YYYY-MM-DD
        import re
        match = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', date_str)
        if match:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except Exception:
        pass
        
    logger.warning(f"Could not parse date string: {date_str}")
    return None

def normalize_transaction(tx_data: dict[str, Any], source_doc_id: str) -> ExtractedTransaction:
    """Normalize extracted transaction raw fields into a standard ExtractedTransaction schema."""
    tx_id = tx_data.get("id") or str(uuid.uuid4())
    
    # Parse total_amount
    total_amount = None
    raw_amount = tx_data.get("total_amount")
    if raw_amount is not None:
        try:
            # Clean string amount if passed as string
            if isinstance(raw_amount, str):
                cleaned = raw_amount.replace("$", "").replace(",", "").strip()
                total_amount = Decimal(cleaned)
            else:
                total_amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Could not normalize amount {raw_amount}: {e}")
            total_amount = None
            
    # Parse date
    date_val = tx_data.get("transaction_date")
    if isinstance(date_val, str):
        transaction_date = parse_date(date_val)
    elif isinstance(date_val, datetime):
        transaction_date = date_val
    else:
        transaction_date = None
        
    # Process line items
    line_items = tx_data.get("line_items") or []
    if isinstance(line_items, str):
        line_items = [line_items]
        
    # Normalize category
    category = tx_data.get("category")
    if category:
        category = category.strip().capitalize()
        
    return ExtractedTransaction(
        id=tx_id,
        source_doc_id=source_doc_id,
        merchant=tx_data.get("merchant") or "Unknown Merchant",
        transaction_date=transaction_date,
        total_amount=total_amount,
        line_items=line_items,
        category=category or "Uncategorized",
        confidence_score=float(tx_data.get("confidence_score", 0.5)),
        is_duplicate=bool(tx_data.get("is_duplicate", False)),
        reconciliation_status=tx_data.get("reconciliation_status", "unmatched"),
        ingestion_method=tx_data.get("ingestion_method", "text"),
        page_number=tx_data.get("page_number"),
        row_number=tx_data.get("row_number")
    )
