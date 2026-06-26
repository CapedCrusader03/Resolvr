from decimal import Decimal, InvalidOperation
from typing import list, Optional, Union
import logging

logger = logging.getLogger(__name__)

def safe_sum(values: list[Union[str, float, Decimal, None]]) -> Decimal:
    """Sum a list of numeric values safely using Decimals to avoid floating point errors."""
    total = Decimal('0.00')
    for val in values:
        if val is None:
            continue
        try:
            if isinstance(val, (float, int)):
                # Convert float through string to prevent precision issues
                total += Decimal(str(val))
            elif isinstance(val, str):
                cleaned = val.replace("$", "").replace(",", "").strip()
                if cleaned:
                    total += Decimal(cleaned)
            elif isinstance(val, Decimal):
                total += val
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Could not convert value {val} to Decimal for safe_sum: {e}")
            
    return total

def safe_subtract(a: Union[str, float, Decimal, None], b: Union[str, float, Decimal, None]) -> Decimal:
    """Subtract b from a safely using Decimals."""
    dec_a = Decimal('0.00')
    dec_b = Decimal('0.00')
    
    try:
        if a is not None:
            dec_a = Decimal(str(a).replace("$", "").replace(",", "").strip())
        if b is not None:
            dec_b = Decimal(str(b).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, ValueError) as e:
        logger.warning(f"Error converting values in safe_subtract: {e}")
        
    return dec_a - dec_b
