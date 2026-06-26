import logging
from contextlib import contextmanager
from typing import Generator, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from decimal import Decimal
from datetime import datetime

from resolvr.config import DATABASE_URL
from resolvr.memory.orm_models import Base, DBParsedDocument, DBExtractedTransaction, DBAnomalyReport

logger = logging.getLogger(__name__)

# Create Engine and SessionMaker
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def init_db() -> None:
    """Initialize database and create tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise e
    finally:
        session.close()

class StructuredStore:
    """Class to manage database operations for documents and transactions."""
    
    @staticmethod
    def add_parsed_document(
        doc_id: str,
        filename: str,
        file_type: str,
        ingestion_method: str,
        raw_text: str,
        file_hash: str
    ) -> DBParsedDocument:
        with get_db() as db:
            # Check if document already exists
            existing = db.query(DBParsedDocument).filter(DBParsedDocument.hash == file_hash).first()
            if existing:
                logger.info(f"Document with hash {file_hash} already exists: {existing.filename}")
                return existing
            
            db_doc = DBParsedDocument(
                id=doc_id,
                filename=filename,
                file_type=file_type,
                ingestion_method=ingestion_method,
                raw_text=raw_text,
                hash=file_hash
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
            return db_doc

    @staticmethod
    def get_document(doc_id: str) -> Optional[DBParsedDocument]:
        with get_db() as db:
            return db.query(DBParsedDocument).filter(DBParsedDocument.id == doc_id).first()

    @staticmethod
    def list_documents() -> list[DBParsedDocument]:
        with get_db() as db:
            return db.query(DBParsedDocument).all()

    @staticmethod
    def add_transaction(tx_data: dict[str, Any]) -> DBExtractedTransaction:
        with get_db() as db:
            # Convert decimal total_amount
            total_amount = tx_data.get("total_amount")
            if total_amount is not None:
                total_amount = Decimal(str(total_amount))
                
            db_tx = DBExtractedTransaction(
                id=tx_data["id"],
                source_doc_id=tx_data["source_doc_id"],
                merchant=tx_data.get("merchant"),
                transaction_date=tx_data.get("transaction_date"),
                total_amount=total_amount,
                line_items=tx_data.get("line_items"),
                category=tx_data.get("category"),
                confidence_score=tx_data.get("confidence_score", 0.0),
                is_duplicate=tx_data.get("is_duplicate", False),
                reconciliation_status=tx_data.get("reconciliation_status", "unmatched"),
                ingestion_method=tx_data.get("ingestion_method", "text"),
                page_number=tx_data.get("page_number"),
                row_number=tx_data.get("row_number")
            )
            db.add(db_tx)
            return db_tx

    @staticmethod
    def update_transaction(tx_id: str, updates: dict[str, Any]) -> Optional[DBExtractedTransaction]:
        with get_db() as db:
            db_tx = db.query(DBExtractedTransaction).filter(DBExtractedTransaction.id == tx_id).first()
            if not db_tx:
                return None
                
            for key, val in updates.items():
                if key == "total_amount" and val is not None:
                    val = Decimal(str(val))
                setattr(db_tx, key, val)
                
            db.commit()
            db.refresh(db_tx)
            return db_tx

    @staticmethod
    def get_transaction(tx_id: str) -> Optional[DBExtractedTransaction]:
        with get_db() as db:
            return db.query(DBExtractedTransaction).filter(DBExtractedTransaction.id == tx_id).first()

    @staticmethod
    def list_transactions() -> list[DBExtractedTransaction]:
        with get_db() as db:
            return db.query(DBExtractedTransaction).all()

    @staticmethod
    def add_anomaly(anomaly_data: dict[str, Any]) -> DBAnomalyReport:
        with get_db() as db:
            db_anomaly = DBAnomalyReport(
                id=anomaly_data["id"],
                transaction_id=anomaly_data["transaction_id"],
                anomaly_type=anomaly_data["anomaly_type"],
                description=anomaly_data["description"],
                severity=anomaly_data.get("severity", "medium"),
                is_resolved=anomaly_data.get("is_resolved", False),
                resolution_details=anomaly_data.get("resolution_details")
            )
            db.add(db_anomaly)
            return db_anomaly

    @staticmethod
    def execute_read_query(sql_query: str) -> list[dict[str, Any]]:
        """Safely executes a read-only SQL query against the SQLite database."""
        # Clean query
        query_stripped = sql_query.strip().upper()
        
        # Verify it is a SELECT statement and doesn't contain forbidden keywords
        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE"]
        
        if not query_stripped.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for security reasons.")
            
        for word in forbidden:
            # Match boundary word to prevent false alarms on column names containing words
            import re
            if re.search(r'\b' + word + r'\b', query_stripped):
                raise ValueError(f"Query contains forbidden keyword: {word}")
                
        with get_db() as db:
            result = db.execute(text(sql_query))
            keys = list(result.keys())
            rows = []
            for row in result.fetchall():
                row_dict = {}
                for idx, val in enumerate(row):
                    # Handle decimal and datetime conversions to serializable formats
                    if isinstance(val, Decimal):
                        row_dict[keys[idx]] = float(val)
                    elif isinstance(val, datetime):
                        row_dict[keys[idx]] = val.isoformat()
                    else:
                        row_dict[keys[idx]] = val
                rows.append(row_dict)
            return rows
