import pytest
import os
import tempfile
import pandas as pd

from resolvr.ingestion.text_parser import parse_text_file
from resolvr.ingestion.excel_parser import parse_excel_or_csv

def test_parse_text_file():
    # Create temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False, encoding="utf-8") as tmp:
        tmp.write("Store: Starbucks Coffee\nDate: 2025-06-12\nTotal: $12.50\nThanks for visiting!")
        tmp_path = tmp.name
        
    try:
        result = parse_text_file(tmp_path)
        assert result["merchant"] == "Store: Starbucks Coffee"
        assert result["transaction_date"] == "2025-06-12"
        assert result["total_amount"] == 12.50
        assert result["ingestion_method"] == "text"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_parse_csv_file():
    # Create temporary CSV file
    df = pd.DataFrame([
        {"merchant": "Uber Trips", "date": "2025-06-14", "amount": "$15.80"},
        {"merchant": "AWS Cloud", "date": "2025-06-01", "amount": 120.00}
    ])
    
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w+", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        df.to_csv(tmp_path, index=False)
        result = parse_excel_or_csv(tmp_path)
        
        assert "extracted_transactions" in result
        txs = result["extracted_transactions"]
        assert len(txs) == 2
        
        # Verify row 1 mapping
        assert txs[0]["merchant"] == "Uber Trips"
        assert txs[0]["total_amount"] == 15.80
        
        # Verify row 2 mapping
        assert txs[1]["merchant"] == "AWS Cloud"
        assert txs[1]["total_amount"] == 120.00
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
