import logging
import json
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL
from resolvr.agent.state import AgentState
from resolvr.agent.tools.sql_query import execute_structured_query
from resolvr.agent.tools.date_normalizer import parse_relative_date
from resolvr.memory.semantic_store import SemanticStore

logger = logging.getLogger(__name__)

def retriever_node(state: AgentState) -> dict[str, Any]:
    """Node 2: Hybrid SQL + Vector retrieval and deduplication."""
    logger.info("Retriever Node: Fetching documents...")
    
    query = state["messages"][-1].content
    intent = state.get("intent", "GENERAL")
    class_params = state.get("classification_params", {})
    
    thought_log = []
    thought_log.append({
        "node": "retriever",
        "type": "thought",
        "content": f"Initiating hybrid search for intent '{intent}'."
    })
    
    sql_results = []
    vector_results = []
    
    # 1. SQL Path (for structured numeric & date queries)
    if intent in ["SUM", "FILTER", "RECONCILE", "ANOMALY_CHECK"] and GOOGLE_API_KEY:
        try:
            # Let's normalize any date filter mentioned in classification
            date_filter = class_params.get("date_filter")
            normalized_date = ""
            if date_filter:
                normalized_date = parse_relative_date(date_filter)
                
            llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.0
            )
            
            sql_schema = (
                "Table: extracted_transactions\n"
                "Columns:\n"
                "  - id (string, primary key)\n"
                "  - source_doc_id (string, foreign key)\n"
                "  - merchant (string, nullable)\n"
                "  - transaction_date (datetime, nullable)\n"
                "  - total_amount (numeric/decimal, nullable)\n"
                "  - line_items (json array of strings, nullable)\n"
                "  - category (string, nullable)\n"
                "  - confidence_score (float)\n"
                "  - is_duplicate (boolean)\n"
                "  - reconciliation_status (string) -- 'matched', 'unmatched', 'flagged'\n"
                "  - page_number (integer, nullable)\n"
                "  - row_number (integer, nullable)\n"
            )
            
            prompt = (
                f"You are the SQL generator for an agentic financial auditor.\n"
                f"Database schema:\n{sql_schema}\n"
                f"User query: '{query}'\n"
                f"Normalized date context: '{normalized_date}' if resolved.\n"
                "Generate a valid SQLite SELECT query to fetch transactions matching this query. "
                "Do NOT sum or aggregate in SQL; select individual rows so we can audit them. "
                "Select all columns (*). "
                "Only return the raw SQLite SELECT query. No markdown, no comments, no formatting."
            )
            
            response = llm.invoke(prompt)
            sql_query = response.content.strip()
            
            # Clean markdown code blocks from SQL response
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].split("```")[0].strip()
                
            thought_log.append({
                "node": "retriever",
                "type": "action",
                "content": f"Generated SQL query: {sql_query}"
            })
            
            sql_results = execute_structured_query(sql_query)
            
            # If an error row is returned, clear it and log it
            if sql_results and "error" in sql_results[0]:
                logger.error(f"SQL execution error in retriever: {sql_results[0]['error']}")
                thought_log.append({
                    "node": "retriever",
                    "type": "observation",
                    "content": f"SQL execution error: {sql_results[0]['error']}"
                })
                sql_results = []
            else:
                thought_log.append({
                    "node": "retriever",
                    "type": "observation",
                    "content": f"SQL query returned {len(sql_results)} records."
                })
        except Exception as e:
            logger.error(f"Error in SQL retrieval: {e}")
            thought_log.append({
                "node": "retriever",
                "type": "observation",
                "content": f"SQL path failed: {e}."
            })
            
    # 2. Vector Path (for fuzzy, conceptual recall)
    try:
        vector_results = SemanticStore.semantic_search(query, n_results=5)
        thought_log.append({
            "node": "retriever",
            "type": "observation",
            "content": f"Vector search returned {len(vector_results)} chunks from ChromaDB."
        })
    except Exception as e:
        logger.error(f"Error in vector retrieval: {e}")
        thought_log.append({
            "node": "retriever",
            "type": "observation",
            "content": f"Vector search failed: {e}."
        })
        
    # 3. Merge and Deduplicate Hybrid Results
    # Create final list of records
    merged_docs = []
    seen_tx_ids = set()
    
    # Add structured SQL transactions first
    for tx in sql_results:
        tx_id = tx.get("id")
        if tx_id:
            seen_tx_ids.add(tx_id)
            # Fetch doc name
            from resolvr.memory.structured_store import StructuredStore
            doc = StructuredStore.get_document(tx["source_doc_id"])
            filename = doc.filename if doc else "unknown_doc"
            
            merged_docs.append({
                "type": "transaction",
                "id": tx_id,
                "merchant": tx.get("merchant"),
                "total_amount": tx.get("total_amount"),
                "date": tx.get("transaction_date"),
                "category": tx.get("category"),
                "page_number": tx.get("page_number"),
                "row_number": tx.get("row_number"),
                "filename": filename,
                "confidence": tx.get("confidence_score", 0.5),
                "is_duplicate": tx.get("is_duplicate", False),
                "reconciliation_status": tx.get("reconciliation_status"),
                "line_items": tx.get("line_items"),
                "source_doc_id": tx["source_doc_id"],
                "raw_record": tx
            })
            
    # Add vector chunks that don't overlap with SQL transactions
    for chunk in vector_results:
        meta = chunk.get("metadata", {})
        doc_id = meta.get("source_doc_id")
        filename = meta.get("filename", "unknown_doc")
        
        # Check if the chunk text contains information we already have, or just add as context
        merged_docs.append({
            "type": "text_chunk",
            "id": chunk.get("id"),
            "text": chunk.get("text"),
            "filename": filename,
            "source_doc_id": doc_id,
            "page_number": meta.get("page_number"),
            "score": chunk.get("score", 0.0)
        })
        
    # Build list of citations
    citations = []
    seen_citations = set()
    for doc in merged_docs:
        cite_key = (doc.get("source_doc_id"), doc.get("page_number"), doc.get("row_number"))
        if cite_key not in seen_citations:
            seen_citations.add(cite_key)
            citations.append({
                "source_doc_id": doc.get("source_doc_id"),
                "filename": doc.get("filename"),
                "page_number": doc.get("page_number"),
                "row_number": doc.get("row_number"),
                "confidence": doc.get("confidence", 0.9) if doc.get("type") == "transaction" else doc.get("score", 0.5)
            })
            
    thought_log.append({
        "node": "retriever",
        "type": "thought",
        "content": f"Merged hybrid results: {len(merged_docs)} total elements with {len(citations)} source citations."
    })
    
    return {
        "retrieved_docs": merged_docs,
        "citations": citations,
        "thought_log": thought_log
    }
