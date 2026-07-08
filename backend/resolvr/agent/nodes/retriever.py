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

def rerank_chunks(query: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rate and filter retrieved text chunks using Gemini as a relevance judge."""
    if not chunks or not GOOGLE_API_KEY:
        return chunks
        
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        # Format the chunks for evaluation
        formatted_list = []
        for chunk in chunks:
            formatted_list.append(f"Chunk ID: {chunk['id']}\nText: {chunk['text']}\n---")
        chunks_str = "\n".join(formatted_list)
        
        prompt = (
            "You are a strict financial audit assistant context-reranker.\n"
            "Evaluate the relevance of each of the following text chunks in answering the user's query.\n"
            "Rate each chunk on a scale from 0 to 10:\n"
            "  - 0: Completely irrelevant\n"
            "  - 1-4: Marginally relevant (contains tangential background, but no specific calculations, vendors, or amounts)\n"
            "  - 5-7: Moderately relevant (related to the query topic, matching merchants or categories)\n"
            "  - 8-10: Highly relevant (contains exact transactions, totals, line items, dates, or contract terms matching the query)\n\n"
            f"User Query: '{query}'\n\n"
            f"Chunks to evaluate:\n{chunks_str}\n\n"
            "Return a JSON object containing a list of objects with the chunk ID, the numeric score (0-10), and a brief reason.\n"
            "Return ONLY raw JSON. Do NOT output markdown code blocks or any text other than valid JSON.\n"
            "Format:\n"
            "{\n"
            "  \"scores\": [\n"
            "    {\"id\": \"chunk_id_here\", \"score\": 8, \"reason\": \"explanation\"}\n"
            "  ]\n"
            "}"
        )
        
        response = llm.invoke(prompt)
        raw_content = response.content
        if isinstance(raw_content, list):
            response_text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            ).strip()
        else:
            response_text = str(raw_content).strip()
            
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(response_text)
        scores_map = {item["id"]: item["score"] for item in data.get("scores", []) if "id" in item and "score" in item}
        
        reranked = []
        for chunk in chunks:
            score = scores_map.get(chunk["id"], 5)  # Default to 5
            if score >= 5:
                chunk["score"] = float(score) / 10.0  # Normalize
                reranked.append(chunk)
                
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked
    except Exception as e:
        logger.error(f"Error during context reranking: {e}")
        return chunks

def filter_retrieved_transactions_semantically(query: str, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter retrieved SQL transactions semantically based on the user query context."""
    if not transactions or not GOOGLE_API_KEY:
        return transactions
        
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        # Format transaction summaries for LLM evaluation
        tx_summaries = []
        for tx in transactions:
            tx_summaries.append({
                "id": tx.get("id"),
                "merchant": tx.get("merchant"),
                "category": tx.get("category"),
                "total_amount": float(tx.get("total_amount") or 0.0),
                "description": tx.get("line_items", []) or ""
            })
            
        prompt = (
            "You are a financial audit assistant. Filter the following list of transactions to include "
            f"ONLY those that are conceptually relevant to the user's query: '{query}'.\n\n"
            "Guidelines:\n"
            "1. 'Third party vendors' or '3rd party vendors' refers to any external company, supplier, or service provider (e.g. Uber, Delta, AWS, Starbucks, FedEx). Basically, any normal business transaction is a third-party vendor spend.\n"
            "2. If the user query does not suggest filtering (e.g. 'sum of all transactions'), return all transaction IDs.\n"
            "3. Return the results as a JSON object containing a list of matched transaction IDs. "
            "Strictly return ONLY the raw JSON block without markdown formatting or code blocks.\n\n"
            "Format:\n"
            "{\n"
            "  \"matched_ids\": [\"TX-ID-1\", \"TX-ID-2\"]\n"
            "}\n\n"
            f"Transactions:\n{json.dumps(tx_summaries, indent=2)}"
        )
        
        response = llm.invoke(prompt)
        response_text = response.content
        if isinstance(response_text, list):
            response_text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response_text
            )
        else:
            response_text = str(response_text)
            
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        else:
            response_text = response_text.strip()
            
        data = json.loads(response_text)
        matched_ids = set(data.get("matched_ids", []))
        
        filtered_txs = [tx for tx in transactions if tx.get("id") in matched_ids]
        logger.info(f"Retriever Node: Semantically filtered SQL transactions from {len(transactions)} to {len(filtered_txs)} entries.")
        return filtered_txs
    except Exception as e:
        logger.error(f"Error filtering SQL transactions semantically in retriever: {e}")
        return transactions

def retriever_node(state: AgentState) -> dict[str, Any]:
    """Node 2: Hybrid SQL + Vector retrieval and deduplication."""
    logger.info("Retriever Node: Fetching documents...")
    
    query = state["messages"][-1].content
    intent = state.get("intent", "GENERAL")
    class_params = state.get("classification_params", {})
    session_id = state.get("session_id")
    
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
            
            # Fetch active documents in session to inject context
            from resolvr.memory.structured_store import StructuredStore
            session_docs = StructuredStore.list_documents(session_id)
            doc_list_str = ", ".join([d.filename for d in session_docs])
            
            sql_schema = (
                "Table: parsed_documents\n"
                "Columns:\n"
                "  - id (string, primary key)\n"
                "  - filename (string) -- e.g. 'large_hotel_invoice.pdf'\n"
                "  - file_type (string)\n"
                "  - session_id (string)\n"
                "\n"
                "Table: extracted_transactions\n"
                "Columns:\n"
                "  - id (string, primary key)\n"
                "  - source_doc_id (string, foreign key references parsed_documents.id)\n"
                "  - session_id (string) -- MUST match the session context\n"
                "  - merchant (string, nullable) -- e.g. 'Uber', 'Starbucks', 'AWS'\n"
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
                f"Active uploaded documents in this session: [{doc_list_str}]\n"
                f"User query: '{query}'\n"
                f"Normalized date context: '{normalized_date}' if resolved.\n"
                f"Session context: You MUST filter the query by the current session using: WHERE t.session_id = '{session_id}' (and combine with other filters using AND).\n"
                "Guidelines:\n"
                "1. If the user mentions a merchant or category (e.g. 'Hilton Corporate Dining' or 'SaaS billing'), and it matches one of the active uploaded documents (e.g. 'large_hotel_invoice.pdf' or 'large_saas_billing.csv'), you MUST perform a SQL JOIN between extracted_transactions (t) and parsed_documents (d) on t.source_doc_id = d.id, and filter by d.filename.\n"
                "2. When filtering on file names, use LIKE or direct equals (e.g. d.filename = 'large_hotel_invoice.pdf').\n"
                "3. Select all columns from extracted_transactions (t.*) so the auditor can process individual transactions. Do NOT aggregate or SUM in SQL.\n"
                "Only return the raw SQLite SELECT query. No markdown, no comments, no formatting."
            )
            
            response = llm.invoke(prompt)
            raw_content = response.content
            if isinstance(raw_content, list):
                sql_query = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in raw_content
                ).strip()
            else:
                sql_query = str(raw_content).strip()
            
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
                    "content": f"SQL query returned {len(sql_results)} records. Applying semantic relevance filter..."
                })
                # Semantic filter: narrow the broad SQL pool to only rows matching
                # the user's conceptual intent (e.g. "third party vendors", "flights").
                # This keeps the calculator and reporter free of irrelevant noise.
                sql_results = filter_retrieved_transactions_semantically(query, sql_results)
                thought_log.append({
                    "node": "retriever",
                    "type": "observation",
                    "content": f"Semantic filter retained {len(sql_results)} relevant transactions for downstream processing."
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
        raw_chunks = SemanticStore.semantic_search(query, n_results=5, session_id=session_id)
        # Rerank and filter noisy chunks using LLM-as-a-judge
        vector_results = rerank_chunks(query, raw_chunks)
        thought_log.append({
            "node": "retriever",
            "type": "observation",
            "content": f"Vector search returned {len(raw_chunks)} chunks; reranked down to {len(vector_results)} highly relevant chunks."
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
