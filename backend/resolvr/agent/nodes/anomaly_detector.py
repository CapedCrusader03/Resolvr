import logging
import uuid
from typing import Any
from decimal import Decimal
from resolvr.agent.state import AgentState
from resolvr.agent.tools.safe_math import safe_sum

logger = logging.getLogger(__name__)

def anomaly_detector_node(state: AgentState) -> dict[str, Any]:
    """Node 4: Audit transactions for mathematical consistency and potential duplicates."""
    logger.info("Anomaly Detector Node: Running audit checks...")
    
    docs = state.get("retrieved_docs", [])
    thought_log = []
    thought_log.append({
        "node": "anomaly_detector",
        "type": "thought",
        "content": "Analyzing retrieved transactions for anomalies."
    })
    
    transactions = [d for d in docs if d.get("type") == "transaction"]
    anomalies = []
    
    for tx in transactions:
        tx_id = tx["id"]
        merchant = tx.get("merchant") or "Unknown"
        total = tx.get("total_amount")
        if total is not None:
            total = Decimal(str(total))
        line_items = tx.get("line_items") or []
        if isinstance(line_items, str):
            try:
                import json
                line_items = json.loads(line_items)
            except Exception:
                line_items = [line_items]
        filename = tx.get("filename", "unknown")
        
        # Check 1: Math Consistency
        # Some line items are like "Item 1: $10.00" or just "10.00".
        # Let's see if we can parse amounts out of line items and check sum.
        # If line items exist, try parsing amounts from them.
        if line_items and total is not None:
            item_amounts = []
            for item in line_items:
                # Match dollar/numeric amounts like "$10.00" or " 12.50" or "9.99"
                import re
                match = re.search(r'\$?\s*(\d+\.\d{2})\b', item)
                if match:
                    try:
                        item_amounts.append(Decimal(match.group(1)))
                    except Exception:
                        pass
            
            if item_amounts:
                items_sum = safe_sum(item_amounts)
                # Verify total matches line items sum (within 0.05 tolerance)
                if abs(total - items_sum) > Decimal('0.05'):
                    desc = f"Math mismatch in {filename}: document total is ${total}, but line items sum to ${items_sum}."
                    logger.warning(desc)
                    anomalies.append({
                        "id": str(uuid.uuid4()),
                        "transaction_id": tx_id,
                        "anomaly_type": "math_mismatch",
                        "description": desc,
                        "severity": "high",
                        "is_resolved": False,
                        "raw_record": tx.get("raw_record")
                    })
                    
        # Check 2: Low Confidence Score
        confidence = tx.get("confidence", 1.0)
        if confidence < 0.70:
            desc = f"Low confidence score ({confidence}) in parsing details from {filename}."
            anomalies.append({
                "id": str(uuid.uuid4()),
                "transaction_id": tx_id,
                "anomaly_type": "low_confidence",
                "description": desc,
                "severity": "medium",
                "is_resolved": False,
                "raw_record": tx.get("raw_record")
            })
            
    # Check 3: Cross-document duplicate checks (within 5 mins threshold)
    # Check if there are transactions with matching merchant and amount that are close in date
    for idx, tx1 in enumerate(transactions):
        for tx2 in transactions[idx+1:]:
            m1 = tx1.get("merchant")
            m2 = tx2.get("merchant")
            a1 = tx1.get("total_amount")
            a2 = tx2.get("total_amount")
            d1 = tx1.get("date")
            d2 = tx2.get("date")
            
            # Simple match of merchant and amount
            if m1 and m2 and m1.lower() == m2.lower() and a1 == a2 and a1 is not None:
                is_dup = False
                desc = ""
                
                if tx1["source_doc_id"] != tx2["source_doc_id"]:
                    is_dup = True
                    desc = f"Potential duplicate transaction found: ${a1} at '{m1}' matches across {tx1.get('filename')} and {tx2.get('filename')}."
                elif d1 and d2:
                    try:
                        from dateutil.parser import parse as parse_datetime
                        dt1 = parse_datetime(str(d1))
                        dt2 = parse_datetime(str(d2))
                        if abs((dt1 - dt2).total_seconds()) <= 300: # 5 minutes
                            is_dup = True
                            desc = f"Potential duplicate transaction found: ${a1} at '{m1}' within a 5-minute window in {tx1.get('filename')}."
                    except Exception:
                        pass
                
                if is_dup:
                    anomalies.append({
                        "id": str(uuid.uuid4()),
                        "transaction_id": tx1["id"],
                        "anomaly_type": "potential_duplicate",
                        "description": desc,
                        "severity": "medium",
                        "is_resolved": False,
                        "raw_record": tx1.get("raw_record")
                    })
                    
    if anomalies:
        logger.warning(f"Detected {len(anomalies)} anomalies in transactions.")
        thought_log.append({
            "node": "anomaly_detector",
            "type": "action",
            "content": f"Flagged {len(anomalies)} data anomalies. Routing to messy_solver node."
        })
        for a in anomalies:
            thought_log.append({
                "node": "anomaly_detector",
                "type": "observation",
                "content": f"Anomaly ({a['anomaly_type']}): {a['description']}"
            })
    else:
        thought_log.append({
            "node": "anomaly_detector",
            "type": "observation",
            "content": "No mathematical or duplicate anomalies detected. Data is consistent."
        })
        
    return {
        "anomalies": anomalies,
        "thought_log": thought_log
    }
