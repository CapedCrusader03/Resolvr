import logging
from typing import Any
from resolvr.memory.structured_store import StructuredStore

logger = logging.getLogger(__name__)

def execute_structured_query(sql_query: str) -> list[dict[str, Any]]:
    """Safe tool interface to execute custom SELECT SQL queries on the transaction database."""
    logger.info(f"Executing SQL via tool: {sql_query}")
    try:
        results = StructuredStore.execute_read_query(sql_query)
        logger.info(f"SQL execution returned {len(results)} rows.")
        return results
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return [{"error": str(e)}]
