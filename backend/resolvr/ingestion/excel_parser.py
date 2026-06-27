import pandas as pd
import openpyxl
from typing import Any
import logging
import io
import re

logger = logging.getLogger(__name__)

def parse_excel_or_csv(file_path: str) -> dict[str, Any]:
    """Parse Excel or CSV file and extract table data as text and structured objects.
    Includes fallback heuristics to infer columns for headerless spreadsheets.
    """
    try:
        raw_text_parts = []
        sheets_data = {}
        
        if file_path.endswith('.csv'):
            # Read CSV first to inspect columns
            df = pd.read_csv(file_path)
            
            # Heuristic check if the column names themselves look like data (missing header row)
            looks_like_data = False
            for col in df.columns:
                col_str = str(col).strip().lower()
                # If column name matches YYYY-MM-DD or looks like a decimal amount
                if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', col_str) or re.match(r'^-?\d+(\.\d+)?$', col_str.replace('$', '').replace(',', '').strip()):
                    looks_like_data = True
                    break
            
            if looks_like_data:
                # Reload without treating first row as header
                df = pd.read_csv(file_path, header=None)
                df.columns = [f"col_{i}" for i in range(len(df.columns))]
                
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
            if not rows:
                continue
                
            # Clean keys of the rows
            cleaned_rows = []
            for r in rows:
                cleaned_rows.append({str(k).strip().lower(): v for k, v in r.items()})
                
            keys = list(cleaned_rows[0].keys())
            
            # Check if we have explicit headers
            header_keywords = [
                "merchant", "vendor", "payee", "description", "name", "store",
                "amount", "total", "value", "price", "sum", "cost", "charge",
                "date", "transaction date", "tx_date", "timestamp", "created_at"
            ]
            has_explicit_headers = any(k in header_keywords for k in keys)
            
            inferred_date_col = None
            inferred_amount_col = None
            inferred_merchant_col = None
            
            if not has_explicit_headers:
                # Infer column roles by checking values in first few rows
                for key in keys:
                    sample_vals = [str(r[key]).strip() for r in cleaned_rows[:3] if r.get(key) is not None and pd.notna(r[key])]
                    if not sample_vals:
                        continue
                    
                    # Check if Date
                    if all(re.search(r'\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b', val) for val in sample_vals):
                        inferred_date_col = key
                    # Check if Amount
                    elif all(re.match(r'^-?\d+(\.\d+)?$', val.replace('$', '').replace(',', '').strip()) for val in sample_vals):
                        inferred_amount_col = key
                    # Check if Merchant (default fallback)
                    else:
                        inferred_merchant_col = key
            
            for idx, row in enumerate(cleaned_rows):
                merchant = None
                date_val = None
                amount = None
                
                if has_explicit_headers:
                    # Look for merchant
                    for key in ["merchant", "vendor", "payee", "description", "name", "store"]:
                        if key in row and pd.notna(row[key]):
                            merchant = str(row[key])
                            break
                            
                    # Look for date
                    for key in ["date", "transaction date", "tx_date", "timestamp", "created_at"]:
                        if key in row and pd.notna(row[key]):
                            date_val = row[key]
                            break
                            
                    # Look for amount
                    for key in ["amount", "total", "value", "price", "sum", "cost", "charge"]:
                        if key in row and pd.notna(row[key]):
                            amount_raw = row[key]
                            if isinstance(amount_raw, str):
                                amount_raw = amount_raw.replace("$", "").replace(",", "").strip()
                                try:
                                    amount = float(amount_raw)
                                except ValueError:
                                    pass
                            elif isinstance(amount_raw, (int, float)):
                                amount = float(amount_raw)
                            break
                else:
                    # Use inferred columns
                    if inferred_merchant_col and pd.notna(row.get(inferred_merchant_col)):
                        merchant = str(row[inferred_merchant_col])
                    if inferred_date_col and pd.notna(row.get(inferred_date_col)):
                        date_val = row[inferred_date_col]
                    if inferred_amount_col and pd.notna(row.get(inferred_amount_col)):
                        amount_raw = row[inferred_amount_col]
                        if isinstance(amount_raw, str):
                            amount_raw = amount_raw.replace("$", "").replace(",", "").strip()
                            try:
                                amount = float(amount_raw)
                            except ValueError:
                                pass
                        elif isinstance(amount_raw, (int, float)):
                            amount = float(amount_raw)
                
                # Check if we have some data
                if merchant or amount or date_val:
                    transactions.append({
                        "row_number": idx + 1,
                        "sheet_name": sheet_name,
                        "merchant": merchant,
                        "transaction_date": str(date_val) if pd.notna(date_val) else None,
                        "total_amount": amount,
                        "line_items": [str(row)],
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

