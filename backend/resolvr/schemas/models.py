from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional

class ExtractedTransaction(BaseModel):
    id: str = Field(..., description="UUID of the transaction")
    source_doc_id: str = Field(..., description="UUID of the parent document")
    merchant: Optional[str] = Field(None, description="Inferred merchant name")
    transaction_date: Optional[datetime] = Field(None, description="Inferred transaction date/time")
    total_amount: Optional[Decimal] = Field(None, description="Inferred transaction total amount (exact Decimal)")
    line_items: Optional[list[str]] = Field(None, description="Inferred line item text descriptions")
    category: Optional[str] = Field(None, description="Inferred expense category")
    confidence_score: float = Field(0.0, description="Inferred confidence score between 0.0 and 1.0")
    is_duplicate: bool = Field(False, description="Flag indicating if the transaction is a suspected duplicate")
    reconciliation_status: str = Field("unmatched", description="Reconciliation status: unmatched, matched, flagged")
    ingestion_method: str = Field("text", description="Method used to ingest: text, ocr, table, vision")
    page_number: Optional[int] = Field(None, description="Page number where transaction was found (1-indexed)")
    row_number: Optional[int] = Field(None, description="Row number if parsed from excel/csv (1-indexed)")

class ParsedDocument(BaseModel):
    id: str = Field(..., description="UUID of the document")
    filename: str = Field(..., description="Original filename of the document")
    file_type: str = Field(..., description="File extension: .pdf, .xlsx, .txt, etc.")
    ingestion_method: str = Field(..., description="Primary ingestion method: plain_text, table_extract, ocr, vision")
    raw_text: str = Field(..., description="Extracted raw text content of the document")
    hash: str = Field(..., description="SHA-256 hash of the file content to detect duplicates")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnomalyReport(BaseModel):
    id: str = Field(..., description="UUID of the anomaly")
    transaction_id: str = Field(..., description="Transaction ID with the anomaly")
    anomaly_type: str = Field(..., description="Type: math_mismatch, potential_duplicate, low_confidence")
    description: str = Field(..., description="Human readable description of the anomaly")
    severity: str = Field("medium", description="Severity level: low, medium, high")
    is_resolved: bool = Field(False, description="Whether the anomaly has been resolved by the ReAct loop")
    resolution_details: Optional[str] = Field(None, description="Details of how the anomaly was resolved")

class CitationRef(BaseModel):
    file_id: str
    filename: str
    page_number: Optional[int] = None
    row_number: Optional[int] = None
    confidence: float

class ThoughtEvent(BaseModel):
    node: str = Field(..., description="Name of the agent graph node")
    type: str = Field(..., description="Type of event: thought, action, observation")
    content: str = Field(..., description="Text content of the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: user, assistant")
    content: str = Field(..., description="Text content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
