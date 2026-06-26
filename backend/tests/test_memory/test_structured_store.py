import pytest
from decimal import Decimal
from datetime import datetime

from resolvr.memory.structured_store import StructuredStore

def test_add_parsed_document():
    doc = StructuredStore.add_parsed_document(
        doc_id="doc-123",
        filename="test.pdf",
        file_type=".pdf",
        ingestion_method="plain_text",
        raw_text="This is a test document text.",
        file_hash="hash-123"
    )
    assert doc.id == "doc-123"
    assert doc.filename == "test.pdf"
    assert doc.hash == "hash-123"
    
    # Test duplicate prevention (returns existing)
    duplicate = StructuredStore.add_parsed_document(
        doc_id="doc-456",
        filename="other.pdf",
        file_type=".pdf",
        ingestion_method="plain_text",
        raw_text="Different text.",
        file_hash="hash-123"
    )
    assert duplicate.id == "doc-123" # Returns original

def test_add_and_get_transaction():
    # Insert document parent first
    StructuredStore.add_parsed_document(
        doc_id="doc-123",
        filename="test.pdf",
        file_type=".pdf",
        ingestion_method="plain_text",
        raw_text="Text.",
        file_hash="hash-123"
    )
    
    tx = StructuredStore.add_transaction({
        "id": "tx-123",
        "source_doc_id": "doc-123",
        "merchant": "Apple Store",
        "transaction_date": datetime(2025, 6, 15),
        "total_amount": 999.00,
        "line_items": ["Macbook: $999.00"],
        "category": "Technology",
        "confidence_score": 0.95
    })
    
    assert tx.id == "tx-123"
    assert tx.total_amount == Decimal("999.00")
    
    fetched = StructuredStore.get_transaction("tx-123")
    assert fetched is not None
    assert fetched.merchant == "Apple Store"

def test_update_transaction():
    StructuredStore.add_parsed_document(
        doc_id="doc-123",
        filename="test.pdf",
        file_type=".pdf",
        ingestion_method="plain_text",
        raw_text="Text.",
        file_hash="hash-123"
    )
    
    StructuredStore.add_transaction({
        "id": "tx-123",
        "source_doc_id": "doc-123",
        "merchant": "Apple Store",
        "total_amount": 999.00
    })
    
    updated = StructuredStore.update_transaction("tx-123", {
        "total_amount": 1050.00,
        "reconciliation_status": "matched"
    })
    
    assert updated is not None
    assert updated.total_amount == Decimal("1050.00")
    assert updated.reconciliation_status == "matched"

def test_execute_read_query():
    StructuredStore.add_parsed_document(
        doc_id="doc-123",
        filename="test.pdf",
        file_type=".pdf",
        ingestion_method="plain_text",
        raw_text="Text.",
        file_hash="hash-123"
    )
    
    StructuredStore.add_transaction({
        "id": "tx-123",
        "source_doc_id": "doc-123",
        "merchant": "Uber",
        "total_amount": 15.50
    })
    
    # Valid SELECT
    rows = StructuredStore.execute_read_query("SELECT merchant, total_amount FROM extracted_transactions")
    assert len(rows) == 1
    assert rows[0]["merchant"] == "Uber"
    assert rows[0]["total_amount"] == 15.50
    
    # Invalid query checks (DML block)
    with pytest.raises(ValueError):
        StructuredStore.execute_read_query("DROP TABLE extracted_transactions")
        
    with pytest.raises(ValueError):
        StructuredStore.execute_read_query("INSERT INTO extracted_transactions VALUES ('1', '2', '3')")
