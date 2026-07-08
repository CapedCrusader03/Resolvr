import json
import logging
from datetime import datetime
from typing import Any, Optional
from resolvr.memory.semantic_store import get_chroma_client, get_embedding_function

logger = logging.getLogger(__name__)

class SemanticCache:
    """Session-scoped semantic query cache using ChromaDB."""
    
    @classmethod
    def get_cache_collection(cls):
        """Get or create the collection for query caches."""
        client = get_chroma_client()
        emb_fn = get_embedding_function()
        if emb_fn:
            return client.get_or_create_collection(name="query_cache", embedding_function=emb_fn)
        else:
            return client.get_or_create_collection(name="query_cache")

    @classmethod
    def check_cache(cls, query: str, session_id: str) -> Optional[dict[str, Any]]:
        """Check the cache for a semantically similar query in the current session.
        
        Returns the cached answer and citations if similarity meets the threshold (distance <= 0.08).
        """
        try:
            collection = cls.get_cache_collection()
            
            # Query ChromaDB with session_id filter
            results = collection.query(
                query_texts=[query],
                n_results=1,
                where={"session_id": session_id}
            )
            
            if results and "documents" in results and results["documents"] and results["documents"][0]:
                distance = results["distances"][0][0] if "distances" in results and results["distances"][0] else 1.0
                # Threshold: distance <= 0.08 (roughly >= 95% cosine similarity)
                if distance <= 0.08:
                    meta = results["metadatas"][0][0]
                    citations_raw = meta.get("citations_json", "[]")
                    try:
                        citations = json.loads(citations_raw)
                    except Exception:
                        citations = []
                        
                    logger.info(f"Semantic Cache HIT for query: '{query}' (distance: {distance:.4f})")
                    return {
                        "final_answer": meta.get("final_answer", ""),
                        "citations": citations,
                        "distance": distance
                    }
                else:
                    logger.info(f"Semantic Cache MISS (nearest distance: {distance:.4f} > 0.08) for query: '{query}'")
            else:
                logger.info(f"Semantic Cache MISS (no matches) for query: '{query}'")
        except Exception as e:
            logger.error(f"Error checking semantic cache: {e}")
            
        return None

    @classmethod
    def save_cache(cls, query: str, session_id: str, final_answer: str, citations: list) -> None:
        """Save a resolved query, final answer, and citations to the semantic cache."""
        if not query.strip() or not final_answer.strip():
            return
            
        try:
            collection = cls.get_cache_collection()
            
            # Generate a consistent ID based on query and session
            import hashlib
            query_hash = hashlib.sha256(f"{session_id}_{query.strip().lower()}".encode('utf-8')).hexdigest()
            
            metadata = {
                "session_id": session_id,
                "final_answer": final_answer,
                "citations_json": json.dumps(citations),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Saving query to semantic cache: '{query}' (ID: {query_hash})")
            collection.upsert(
                documents=[query],
                metadatas=[metadata],
                ids=[query_hash]
            )
        except Exception as e:
            logger.error(f"Error saving to semantic cache: {e}")

    @classmethod
    def clear_session_cache(cls, session_id: str) -> None:
        """Clear all cached query entries for a specific session."""
        try:
            collection = cls.get_cache_collection()
            # Delete entries matching session_id filter
            collection.delete(where={"session_id": session_id})
            logger.info(f"Cleared semantic query cache for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear semantic cache for session {session_id}: {e}")
