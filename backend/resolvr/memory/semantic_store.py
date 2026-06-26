import os
import logging
from typing import Any, Optional
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from resolvr.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

# Lazy initialization of ChromaDB client and embedding function
_chroma_client = None
_embedding_function = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        logger.info(f"Initializing ChromaDB persistent client at: {CHROMA_PERSIST_DIR}")
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _chroma_client

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        logger.info(f"Loading SentenceTransformer embedding model: {EMBEDDING_MODEL_NAME}...")
        # Note: downloads model (~550MB) on first use
        try:
            _embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL_NAME,
                trust_remote_code=True
            )
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers embedding model: {e}")
            logger.info("Falling back to ChromaDB default embedding model...")
            # ChromaDB default embedding model fallback
            _embedding_function = None
    return _embedding_function

class SemanticStore:
    """Class to manage semantic memory in ChromaDB."""
    
    @staticmethod
    def get_or_create_collection(name: str = "documents"):
        client = get_chroma_client()
        emb_fn = get_embedding_function()
        
        # If fallback occurred and emb_fn is None, Chroma will use its internal default
        if emb_fn:
            return client.get_or_create_collection(name=name, embedding_function=emb_fn)
        else:
            return client.get_or_create_collection(name=name)

    @classmethod
    def add_document_chunks(
        cls,
        doc_id: str,
        filename: str,
        text_chunks: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None
    ) -> None:
        """Add text chunks with metadata to the vector store."""
        collection = cls.get_or_create_collection()
        
        ids = [f"{doc_id}_chunk_{idx}" for idx in range(len(text_chunks))]
        
        if metadatas is None:
            metadatas = []
            for idx in range(len(text_chunks)):
                metadatas.append({
                    "source_doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": idx
                })
        else:
            # Ensure metadata has core fields
            for idx, meta in enumerate(metadatas):
                meta["source_doc_id"] = doc_id
                meta["filename"] = filename
                meta["chunk_index"] = idx

        logger.info(f"Adding {len(text_chunks)} chunks for document {filename} to ChromaDB...")
        collection.add(
            documents=text_chunks,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Chunks added successfully.")

    @classmethod
    def semantic_search(cls, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search the vector store for similar documents."""
        collection = cls.get_or_create_collection()
        
        logger.info(f"Searching ChromaDB for query: '{query}'")
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results and "documents" in results and results["documents"]:
            # Parse results structure
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            ids = results["ids"][0]
            
            for idx in range(len(docs)):
                formatted_results.append({
                    "id": ids[idx],
                    "text": docs[idx],
                    "metadata": metas[idx],
                    "score": 1.0 - distances[idx] # Simple similarity heuristic
                })
                
        return formatted_results
