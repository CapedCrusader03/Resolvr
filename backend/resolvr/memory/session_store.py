import logging
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)

# Single instance checkpointer
_checkpointer = None

def get_session_checkpointer() -> InMemorySaver:
    """Create and return InMemorySaver checkpointer for LangGraph state."""
    global _checkpointer
    if _checkpointer is None:
        logger.info("Initializing LangGraph InMemorySaver checkpointer")
        _checkpointer = InMemorySaver()
    return _checkpointer
