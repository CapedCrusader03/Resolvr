import logging
import os
from typing import list, dict, Any
from decimal import Decimal
from resolvr.agent.state import AgentState
from resolvr.agent.tools.reparse_source import reparse_document_total
from resolvr.memory.structured_store import StructuredStore

logger = logging.getLogger(__name__)

def solver_node(state: AgentState) -> dict[str, Any]:
    """Node 5: ReAct Loop to resolve data inconsistencies (e.g. math errors, low confidence values)."""
    logger.info("Solver Node: Entering anomaly resolution loop...")
    
    anomalies = state.get("anomalies", [])
    iteration_count = state.get("iteration_count", 0)
    docs = state.get("retrieved_docs", [])
    
    thought_log = []
    thought_log.append({
        "node": "solver",
        "type": "thought",
        "content": f"Solver Node: Evaluating {len(anomalies)} anomalies. Iteration: {iteration_count + 1}/3"
    })
    
    solved_anomalies = state.get("solved_anomalies", []) or []
    remaining_anomalies = []
    
    # Track updates to write back to state
    updated_docs = list(docs)
    
    # Cap loop depth
    if iteration_count >= 3:
        logger.warning("Solver Node: Max ReAct loop iterations reached. Stopping solver.")
        thought_log.append({
            "node": "solver",
            "type": "observation",
            "content": "Max resolution depth reached. Suspending active resolution."
        })
        return {
            "iteration_count": iteration_count + 1,
            "thought_log": thought_log
        }
        
    for anomaly in anomalies:
        if anomaly["anomaly_type"] == "math_mismatch":
            tx_id = anomaly["transaction_id"]
            desc = anomaly["description"]
            raw_record = anomaly.get("raw_record", {})
            source_doc_id = raw_record.get("source_doc_id")
            page_num = raw_record.get("page_number") or 1
            
            # Find the path to the physical document to re-parse
            doc = StructuredStore.get_document(source_doc_id)
            if not doc:
                logger.warning(f"Could not locate document object for ID {source_doc_id}")
                remaining_anomalies.append(anomaly)
                continue
                
            from resolvr.config import UPLOAD_DIR
            file_path = os.path.join(UPLOAD_DIR, doc.filename)
            
            # Run ReAct step
            thought_log.append({
                "node": "solver",
                "type": "thought",
                "content": f"Thought: Anomaly matches 'math_mismatch'. Initiating crop-and-reparse on bottom-third of page {page_num} in '{doc.filename}' to verify the invoice total."
            })
            
            # Check if file exists (might not during tests if using mocks)
            if not os.path.exists(file_path):
                # Mock or skip if file is missing (e.g. in test env)
                logger.warning(f"Document file {file_path} not found. Skipping re-parse.")
                thought_log.append({
                    "node": "solver",
                    "type": "observation",
                    "content": f"Reparse tool failed: file '{doc.filename}' not found on disk."
                })
                remaining_anomalies.append(anomaly)
                continue
                
            try:
                # Call tool
                reparse_result = reparse_document_total(
                    file_path=file_path,
                    page_number=page_num,
                    anomaly_desc=desc
                )
                
                corrected_total = reparse_result.get("total_amount")
                observation = reparse_result.get("observation", "No details provided.")
                
                thought_log.append({
                    "node": "solver",
                    "type": "action",
                    "content": f"Called reparse_document_total(file_path='{doc.filename}', page_num={page_num})"
                })
                thought_log.append({
                    "node": "solver",
                    "type": "observation",
                    "content": f"Gemini reparse result: Corrected Total = ${corrected_total}. Observation: '{observation}'"
                })
                
                # Check if total is resolved
                if corrected_total is not None:
                    # Update database record
                    StructuredStore.update_transaction(
                        tx_id=tx_id,
                        updates={
                            "total_amount": Decimal(str(corrected_total)),
                            "reconciliation_status": "matched",
                            "confidence_score": 0.95
                        }
                    )
                    
                    # Update active state docs list
                    for idx, doc_item in enumerate(updated_docs):
                        if doc_item.get("id") == tx_id:
                            updated_docs[idx]["total_amount"] = Decimal(str(corrected_total))
                            updated_docs[idx]["confidence"] = 0.95
                            updated_docs[idx]["reconciliation_status"] = "matched"
                            
                    # Mark anomaly as solved
                    anomaly["is_resolved"] = True
                    anomaly["resolution_details"] = f"OCR correction applied via reparse tool: ${corrected_total}. Details: {observation}"
                    solved_anomalies.append(anomaly)
                    
                    thought_log.append({
                        "node": "solver",
                        "type": "thought",
                        "content": f"Thought: Anomaly resolved successfully. SQLite record and active transaction states updated with corrected total ${corrected_total}."
                    })
                else:
                    thought_log.append({
                        "node": "solver",
                        "type": "thought",
                        "content": "Thought: Reparse tool did not extract a valid total. Escalating to human review."
                    })
                    remaining_anomalies.append(anomaly)
            except Exception as e:
                logger.error(f"Error during anomaly reparse: {e}")
                thought_log.append({
                    "node": "solver",
                    "type": "observation",
                    "content": f"Reparse tool failed with error: {e}"
                })
                remaining_anomalies.append(anomaly)
        else:
            # For duplicates or other check types, add to remaining list for user warning
            remaining_anomalies.append(anomaly)
            
    return {
        "anomalies": remaining_anomalies,
        "solved_anomalies": solved_anomalies,
        "retrieved_docs": updated_docs,
        "iteration_count": iteration_count + 1,
        "thought_log": thought_log
    }
