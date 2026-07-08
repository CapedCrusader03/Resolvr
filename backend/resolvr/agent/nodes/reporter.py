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
    
    # --- Empty-context guard ---
    # If the retriever found nothing, do NOT call the LLM — it will hallucinate.
    # Return a direct, honest answer based purely on what the system knows.
    transactions = [d for d in docs if d.get("type") == "transaction"]
    chunks = [d for d in docs if d.get("type") == "text_chunk"]
    has_data = bool(transactions or chunks or anomalies or (calc_result is not None and calc_result != 0))
    
    if not has_data:
        thought_log.append({
            "node": "reporter",
            "type": "observation",
            "content": "No matching transactions or text chunks found in the uploaded documents. Returning a factual no-match response."
        })
        no_match_answer = (
            f"No matching records were found in your uploaded documents for the query: **\"{query}\"**.\n\n"
            "The audit system searched all transactions and text content in your session's documents "
            "and found no entries that match this query.\n\n"
            "**If you believe this is incorrect**, please verify:\n"
            "- The document containing this data has been uploaded in the current session\n"
            "- The merchant name or category may be spelled differently in the document\n"
            "- Try rephrasing the query using terms that appear in the actual document"
        )
        return {
            "final_answer": no_match_answer,
            "thought_log": thought_log
        }

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
        if chunks:
            context_parts.append("RELEVANT TEXT CHUNKS RETRIEVED:")
            for c in chunks:
                context_parts.append(
                    f"- From File {c['filename']} (Page {c.get('page_number') or 'N/A'}):\n\"\"\"\n{c['text'][:300]}...\n\"\"\""
                )
                
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
            "You are a grounded financial auditor. Your ONLY job is to summarize the data "
            "provided in the Auditor Context below. You MUST NOT invent, assume, or infer any "
            "information that is not explicitly present in the context.\n\n"
            "STRICT RULES — VIOLATION IS NOT ACCEPTABLE:\n"
            "- You may ONLY reference filenames, row numbers, amounts, and merchants that appear "
            "verbatim in the Auditor Context.\n"
            "- If no transactions are in the context, say 'No matching records found' — do NOT invent any.\n"
            "- Do NOT mention OCR corrections unless one is explicitly listed in the context.\n"
            "- Do NOT invent discrepancies, duplicates, or audit warnings that are not in the context.\n"
            "- Do NOT add confidence metrics, methodology sections, or notes unless grounded in the context.\n\n"
            f"User Query: '{query}'\n\n"
            f"Auditor Context (treat this as the ONLY source of truth):\n{context_str}\n\n"
            "Response Guidelines:\n"
            "1. Answer the user's query directly using only the context above.\n"
            "2. If a mathematical total was calculated, state it clearly.\n"
            "3. Cite each source transaction using the exact filename, page, and row from the context. "
            "Format as markdown links: [filename](file://filename).\n"
            "4. List any OCR corrections or anomalies ONLY if they appear in the context.\n"
            "5. If the context is insufficient to fully answer the query, say so explicitly — "
            "do NOT fill gaps with invented information."
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
