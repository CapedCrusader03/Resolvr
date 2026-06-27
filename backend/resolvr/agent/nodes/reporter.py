import logging
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL
from resolvr.agent.state import AgentState

logger = logging.getLogger(__name__)

def reporter_node(state: AgentState) -> dict[str, Any]:
    """Node 6: Synthesize final cited audit report using Gemini."""
    logger.info("Reporter Node: Synthesizing final report...")
    
    query = state["messages"][-1].content
    docs = state.get("retrieved_docs", [])
    calc_result = state.get("calculation_result")
    anomalies = state.get("anomalies", [])
    solved = state.get("solved_anomalies", [])
    citations = state.get("citations", [])
    
    thought_log = []
    thought_log.append({
        "node": "reporter",
        "type": "thought",
        "content": "Compiling retrieved facts, math results, and anomaly history into final cited response."
    })
    
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. Using basic reporter fallback.")
        ans = f"Calculated Total: ${calc_result or 'N/A'}. (Detailed reporting requires GOOGLE_API_KEY)"
        return {
            "final_answer": ans,
            "thought_log": thought_log
        }
        
    try:
        # Construct detailed context for the reporter LLM
        context_parts = []
        
        # Add math result
        if calc_result is not None:
            context_parts.append(f"CALCULATED MATHEMATICAL TOTAL: ${calc_result}")
            
        # Add transactions context
        transactions = [d for d in docs if d.get("type") == "transaction"]
        if transactions:
            context_parts.append("EXTRACTED TRANSACTIONS TO CITE:")
            for tx in transactions:
                line_desc = (
                    f"- ID: {tx['id']}, Merchant: {tx['merchant']}, Amount: ${tx['total_amount']}, "
                    f"Date: {tx['date']}, Category: {tx['category']}, File: {tx['filename']}, "
                    f"Page: {tx.get('page_number') or 'N/A'}, Row: {tx.get('row_number') or 'N/A'}, "
                    f"Status: {tx.get('reconciliation_status')}"
                )
                context_parts.append(line_desc)
                
        # Add raw text chunks context
        chunks = [d for d in docs if d.get("type") == "text_chunk"]
        if chunks:
            context_parts.append("RELEVANT TEXT CHUNKS RETRIEVED:")
            for c in chunks:
                context_parts.append(f"- From File {c['filename']} (Page {c.get('page_number') or 'N/A'}):\n\"\"\"\n{c['text'][:300]}...\n\"\"\"")
                
        # Add solved anomalies
        if solved:
            context_parts.append("RESOLVED ANOMALIES (OCR CORRECTIONS APPLIED):")
            for s in solved:
                context_parts.append(f"- Transaction ID: {s['transaction_id']}, Corrected: {s['resolution_details']}")
                
        # Add unresolved anomalies
        if anomalies:
            context_parts.append("WARNING - UNRESOLVED ANOMALIES / CONFLICTING DATA:")
            for a in anomalies:
                context_parts.append(f"- {a['anomaly_type'].upper()}: {a['description']} (Severity: {a['severity']})")
                
        context_str = "\n\n".join(context_parts)
        
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        prompt = (
            "You are a relentless agentic financial auditor. Reconcile data and draft a professional "
            "financial Q&A report response to the user's query.\n\n"
            f"User Query: '{query}'\n\n"
            f"Auditor Context:\n{context_str}\n\n"
            "Guidelines:\n"
            "1. Give a direct, accurate answer to the user's query immediately.\n"
            "2. If math/summing was requested, cite the exact total amount calculated (${calc_result}).\n"
            "3. Cite every source document filename, page, and row number (for Excel/CSV) inline or at the bottom. "
            "Format file citations as clickable markdown links where the link text is just the filename. e.g. [receipt.pdf](file://receipt.pdf).\n"
            "4. Mention if any OCR errors were corrected during the ReAct loop.\n"
            "5. Explicitly list any unresolved warnings or discrepancies (e.g. potential duplicate charges found in different documents, missing details, low confidence metrics) in a dedicated 'Auditor Notes / Discrepancies' section.\n"
            "6. Keep your tone objective, professional, and audit-focused. Do not hallucinate values. "
            "If the retrieved documents contain no relevant transactions, state that clearly."
        )
        
        response = llm.invoke(prompt)
        # response.content may be a list of parts in newer google-genai SDK versions
        raw_content = response.content
        if isinstance(raw_content, list):
            final_answer = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            ).strip()
        else:
            final_answer = str(raw_content).strip()
        
        thought_log.append({
            "node": "reporter",
            "type": "observation",
            "content": "Final report generated with citations and anomaly notes."
        })
        
        return {
            "final_answer": final_answer,
            "thought_log": thought_log
        }
    except Exception as e:
        logger.error(f"Error in reporter node: {e}")
        return {
            "final_answer": f"Audit calculations completed with total: ${calc_result or 'N/A'}. (Report synthesis failed: {e})",
            "thought_log": thought_log + [{"node": "reporter", "type": "observation", "content": f"Reporter error: {e}"}]
        }
