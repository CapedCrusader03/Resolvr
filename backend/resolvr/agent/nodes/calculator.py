import logging
from typing import Any
from decimal import Decimal
from resolvr.agent.state import AgentState
from resolvr.agent.tools.safe_math import safe_sum

logger = logging.getLogger(__name__)

def calculator_node(state: AgentState) -> dict[str, Any]:
    """Node 3: Calculate sums or differences on retrieved transactions using safe decimal math."""
    logger.info("Calculator Node: Performing math calculations...")
    
    docs = state.get("retrieved_docs", [])
    intent = state.get("intent", "GENERAL")
    
    thought_log = []
    thought_log.append({
        "node": "calculator",
        "type": "thought",
        "content": f"Processing calculations for intent: '{intent}'"
    })
    
    # Filter transaction records
    transactions = [d for d in docs if d.get("type") == "transaction"]
    
    calculation_result = None
    
    if intent in ["SUM", "RECONCILE"]:
        amounts = [tx.get("total_amount") for tx in transactions]
        logger.info(f"Extracting total_amounts for sum: {amounts}")
        
        calculation_result = safe_sum(amounts)
        
        thought_log.append({
            "node": "calculator",
            "type": "action",
            "content": f"Summed {len(amounts)} transaction amounts: {list(map(str, [a for a in amounts if a is not None]))}"
        })
        thought_log.append({
            "node": "calculator",
            "type": "observation",
            "content": f"Safe sum result: ${calculation_result}"
        })
    else:
        thought_log.append({
            "node": "calculator",
            "type": "thought",
            "content": "No calculation required for this intent."
        })
        
    return {
        "calculation_result": calculation_result,
        "thought_log": thought_log
    }
