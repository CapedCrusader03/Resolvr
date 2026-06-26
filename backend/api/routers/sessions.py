from fastapi import APIRouter, HTTPException
import uuid
import sqlite3
from typing import list
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("")
def create_session() -> dict[str, str]:
    """Create a new session (thread) ID for LangGraph tracking."""
    session_id = str(uuid.uuid4())
    logger.info(f"Created new LangGraph session: {session_id}")
    return {"session_id": session_id}

@router.get("")
def list_sessions() -> list[str]:
    """Retrieve existing active sessions by querying checkpointer sqlite DB directly."""
    sessions = []
    try:
        # Check LangGraph SQLite database for checkpointer sessions
        conn = sqlite3.connect("state_checkpoints.db")
        cursor = conn.cursor()
        # Query unique threads from checkpoints
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        rows = cursor.fetchall()
        sessions = [row[0] for row in rows]
        conn.close()
    except Exception as e:
        logger.warning(f"Could not read checkpoints database: {e}")
        # Return empty list or a default if DB doesn't exist yet
        sessions = []
        
    return sessions
