from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from decimal import Decimal

def add_thoughts(left: Optional[list[dict[str, Any]]], right: Optional[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Accumulate thoughts in list instead of overwriting."""
    return (left or []) + (right or [])

class AgentState(TypedDict):
    # Chat message history (accumulates queries and final reports)
    messages: Annotated[list, add_messages]
    
    # Session identifier
    session_id: str
    
    # Query intent: SUM, FILTER, RECONCILE, ANOMALY_CHECK, GENERAL
    intent: str
    
    # List of retrieved documents and transactions (merged results)
    retrieved_docs: list[dict[str, Any]]
    
    # Final calculated result (Decimal)
    calculation_result: Optional[Decimal]
    
    # Detected anomalies
    anomalies: list[dict[str, Any]]
    
    # Resolved anomalies
    solved_anomalies: list[dict[str, Any]]
    
    # Citation links for frontend
    citations: list[dict[str, Any]]
    
    # Thought trace to feed the live debugger panel
    thought_log: Annotated[list[dict[str, Any]], add_thoughts]
    
    # Current loop safety counter
    iteration_count: int
    
    # Final answer text
    final_answer: str
