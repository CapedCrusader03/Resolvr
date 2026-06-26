import logging
from langgraph.checkpoint.sqlite import SqliteSaver

logger = logging.getLogger(__name__)

# Single instance checkpointer
_checkpointer = None

def get_session_checkpointer() -> SqliteSaver:
    """Create and return SqliteSaver checkpointer for LangGraph state."""
    global _checkpointer
    if _checkpointer is None:
        logger.info("Initializing LangGraph SqliteSaver checkpointer at backend/state_checkpoints.db")
        # Initialize checkpointer database file
        _checkpointer = SqliteSaver.from_conn_string("state_checkpoints.db")
    return _checkpointer
