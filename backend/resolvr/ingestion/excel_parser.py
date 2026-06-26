import pandas as pd
import openpyxl
from typing import Any
import logging
import io

logger = logging.getLogger(__name__)

def parse_excel_or_csv(file_path: str) -> dict[str, Any]:
    """Parse Excel or CSV file and extract table data as text and structured objects."""
    try:
        raw_text_parts = []
        sheets_data = {}
        
        if file_path.endswith('.csv'):
            # Read CSV
            df = pd.read_csv(file_path)
            sheets_data["default"] = df.to_dict(orient="records")
            
            # Create text representation for RAG
            buf = io.StringIO()
            df.to_string(buf)
            raw_text_parts.append(f"--- CSV File ---\n{buf.getvalue()}")
        else:
            # Read Excel (multi-sheet support)
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                sheets_data[sheet_name] = df.to_dict(orient="records")
                
                buf = io.StringIO()
                df.to_string(buf)
                raw_text_parts.append(f"--- Sheet: {sheet_name} ---\n{buf.getvalue()}")
                
        raw_text = "\n\n".join(raw_text_parts)
        
        # Analyze data columns to find transaction attributes
        transactions = []
        for sheet_name, rows in sheets_data.items():
            for idx, row in enumerate(rows):
                # Clean keys
                cleaned_row = {str(k).strip().lower(): v for k, v in row.items()}
                
                # Heuristic mapping for merchant, date, amount
                merchant = None
                date_val = None
                amount = None
                line_items = []
                
                # Look for merchant
                for key in ["merchant", "vendor", "payee", "description", "name", "store"]:
                    if key in cleaned_row and pd.notna(cleaned_row[key]):
                        merchant = str(cleaned_row[key])
                        break
                        
                # Look for date
                for key in ["date", "transaction date", "tx_date", "timestamp", "created_at"]:
                    if key in cleaned_row and pd.notna(cleaned_row[key]):
                        date_val = cleaned_row[key]
                        break
                        
                # Look for amount
                for key in ["amount", "total", "value", "price", "sum", "cost", "charge"]:
                    if key in cleaned_row and pd.notna(cleaned_row[key]):
                        amount_raw = cleaned_row[key]
                        # Clean if it is string like "$12.50"
                        if isinstance(amount_raw, str):
                            amount_raw = amount_raw.replace("$", "").replace(",", "").strip()
                            try:
                                amount = float(amount_raw)
                            except ValueError:
                                pass
                        elif isinstance(amount_raw, (int, float)):
                            amount = float(amount_raw)
                        break
                
                # Check if we have some data
                if merchant or amount or date_val:
                    transactions.append({
                        "row_number": idx + 1,
                        "sheet_name": sheet_name,
                        "merchant": merchant,
                        "transaction_date": str(date_val) if pd.notna(date_val) else None,
                        "total_amount": amount,
                        "line_items": [str(cleaned_row)],
                        "confidence_score": 0.9,
                        "ingestion_method": "table_extract"
                    })
                    
        return {
            "raw_text": raw_text,
            "extracted_transactions": transactions,
            "ingestion_method": "table_extract"
        }
    except Exception as e:
        logger.error(f"Error parsing Excel/CSV file {file_path}: {e}")
        raise e
