from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, JSON, ForeignKey, Numeric
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class DBFolder(Base):
    __tablename__ = "folders"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBParsedDocument(Base):
    __tablename__ = "parsed_documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    ingestion_method = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    hash = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions = relationship("DBExtractedTransaction", back_populates="document", cascade="all, delete-orphan")

class DBExtractedTransaction(Base):
    __tablename__ = "extracted_transactions"

    id = Column(String, primary_key=True)
    source_doc_id = Column(String, ForeignKey("parsed_documents.id"), nullable=False)
    merchant = Column(String, nullable=True)
    transaction_date = Column(DateTime, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)  # Decimal amount
    line_items = Column(JSON, nullable=True)  # List of string line items
    category = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0)
    is_duplicate = Column(Boolean, default=False)
    reconciliation_status = Column(String, default="unmatched")  # matched, flagged, unmatched
    ingestion_method = Column(String, default="text")
    page_number = Column(Integer, nullable=True)
    row_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("DBParsedDocument", back_populates="transactions")
    anomalies = relationship("DBAnomalyReport", back_populates="transaction", cascade="all, delete-orphan")

class DBAnomalyReport(Base):
    __tablename__ = "anomaly_reports"

    id = Column(String, primary_key=True)
    transaction_id = Column(String, ForeignKey("extracted_transactions.id"), nullable=False)
    anomaly_type = Column(String, nullable=False)  # math_mismatch, potential_duplicate, low_confidence
    description = Column(String, nullable=False)
    severity = Column(String, default="medium")
    is_resolved = Column(Boolean, default=False)
    resolution_details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transaction = relationship("DBExtractedTransaction", back_populates="anomalies")
