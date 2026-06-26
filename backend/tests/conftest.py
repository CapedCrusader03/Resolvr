import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import chromadb

# Set temporary databases for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CHROMA_PERSIST_DIR"] = "./test_chroma_store"
os.environ["GOOGLE_API_KEY"] = "mock_key"

from resolvr.memory.orm_models import Base
from resolvr.memory.structured_store import SessionLocal, engine

@pytest.fixture(scope="function", autouse=True)
def test_db():
    """Create in-memory SQLite tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
