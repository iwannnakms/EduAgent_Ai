from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

from app.core.config import get_settings
from app.utils.gemini_client import get_gemini_client
from app.utils.gemini_models import resolve_model
from app.utils.semantic_cache import SemanticCache

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    text: str
    score: float
    metadata: Dict[str, Any]


class RAGService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_gemini_client()
        self.chat_model_name = resolve_model(self.settings.gemini_chat_model, "generateContent")
        self.embedding_model_name = resolve_model(self.settings.gemini_embedding_model, "embedContent")
        self.cache = SemanticCache()
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)

        self.backend = self.settings.vector_backend.lower()
        if self.backend == "pinecone":
            pc = Pinecone(api_key=self.settings.pinecone_api_key)
            if self.settings.pinecone_host:
                self.pinecone_index = pc.Index(host=self.settings.pinecone_host)
            else:
                self.pinecone_index = pc.Index(self.settings.pinecone_index_name)
            self.pinecone_namespace = self.settings.pinecone_namespace
        elif self.backend == "chroma_http":
            self.chroma = chromadb.HttpClient(host=self.settings.chroma_host, port=self.settings.chroma_port)
            self.chroma_collection = self.chroma.get_or_create_collection(self.settings.chroma_collection_name)
        else:
            self.chroma = chromadb.PersistentClient(path=self.settings.chroma_persist_dir)
            self.chroma_collection = self.chroma.get_or_create_collection(self.settings.chroma_collection_name)

    def _embed(self, text: str) -> List[float]:
        response = self.client.models.embed_content(
            model=self.embedding_model_name,
            contents=text
        )
        return response.embeddings[0].values

    def ingest_text(self, document_id: str, text: str, metadata: Dict[str, Any]) -> int:
        chunks = self.splitter.split_text(text)
        if not chunks:
            return 0

        vectors = []
        ids = []
        metadatas = []
        for chunk in chunks:
            vector = self._embed(chunk)
            chunk_id = str(uuid4())
            chunk_meta = {"document_id": document_id, **metadata, "chunk_preview": chunk[:100]}
            vectors.append(vector)
            ids.append(chunk_id)
            metadatas.append(chunk_meta)

        if self.backend == "pinecone":
            self.pinecone_index.upsert(
                vectors=[
                    {"id": ids[i], "values": vectors[i], "metadata": {**metadatas[i], "text": chunks[i]}}
                    for i in range(len(chunks))
                ],
                namespace=self.pinecone_namespace,
            )
        else:
            self.chroma_collection.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)
        return len(chunks)

    def _vector_search(self, query: str, top_k: int, document_id: Optional[str] = None) -> List[SearchResult]:
        query_embedding = self._embed(query)
        
        # Normalize document_id: empty string should be None for global search
        target_id = document_id if document_id and document_id.strip() else None

        if self.backend == "pinecone":
            filter_dict = {"document_id": target_id} if target_id else None
            matches = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True,
                namespace=self.pinecone_namespace,
            ).get("matches", [])
            return [
                SearchResult(
                    text=(m.get("metadata") or {}).get("text", ""),
                    score=float(m.get("score", 0.0)),
                    metadata={k: v for k, v in (m.get("metadata") or {}).items() if k != "text"},
                )
                for m in matches
            ]

        # Chroma filtering
        where = {"document_id": target_id} if target_id else None
        result = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        docs = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        return [
            SearchResult(
                text=docs[i],
                score=1.0 - float(distances[i]) if i < len(distances) else 0.0,
                metadata=metadatas[i] if i < len(metadatas) else {},
            )
            for i in range(len(docs))
        ]

    def answer_query(self, query: str, top_k: int, document_id: Optional[str] = None) -> Dict[str, Any]:
        cache_scope = f"rag-chat:{document_id}" if document_id else "rag-chat:global"
        cached = self.cache.get(scope=cache_scope, query=query)
        if cached:
            response = cached["response"]
            response["cache_hit"] = True
            return response

        sources = self._vector_search(query=query, top_k=top_k, document_id=document_id)
        
        if not sources:
            logger.warning(f"No context found for query '{query}' in document '{document_id}'")
        else:
            logger.info(f"Found {len(sources)} context chunks for query in '{document_id}'")

        context = "\n\n".join([f"- {s.text}" for s in sources])

        prompt = (
            "You are an education assistant. Use only the provided context. "
            "If context is insufficient, state uncertainty.\n\n"
            f"Context:\n{context}\n\nQuestion:\n{query}"
        )
        
        # Robust retry logic for 503/429 errors
        max_retries = 5
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.chat_model_name,
                    contents=prompt
                )
                answer = response.text or "No answer generated."
                payload = {
                    "answer": answer,
                    "sources": [{"text": s.text, "score": s.score, "metadata": s.metadata} for s in sources],
                    "cache_hit": False,
                }
                self.cache.set(scope=cache_scope, query=query, response=payload)
                return payload
            except Exception as e:
                last_error = e
                if "503" in str(e) or "429" in str(e):
                    import time
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"Gemini busy (attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                break

        logger.error(f"RAG query failed after retries: {str(last_error)}")
        raise RuntimeError(f"RAG query failed: {str(last_error)}")
