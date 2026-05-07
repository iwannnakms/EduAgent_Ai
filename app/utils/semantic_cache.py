import hashlib
import json
from typing import Any, Dict, Optional
import numpy as np
import redis
import logging

from app.core.config import get_settings
from app.utils.gemini_client import get_gemini_client
from app.utils.gemini_models import resolve_model

logger = logging.getLogger(__name__)

class SemanticCache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_gemini_client()
        
        self.redis_client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
        self.embedding_model = resolve_model(self.settings.gemini_embedding_model, "embedContent")

    def _cache_index_key(self, scope: str) -> str:
        return f"semantic-cache:index:{scope}"

    def _cache_item_key(self, scope: str, digest: str) -> str:
        return f"semantic-cache:item:{scope}:{digest}"

    def _embed(self, text: str) -> np.ndarray:
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text
        )
        values = response.embeddings[0].values
        return np.array(values, dtype=np.float32)

    @staticmethod
    def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
        if denom == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / denom)

    def get(self, scope: str, query: str) -> Optional[Dict[str, Any]]:
        try:
            index_key = self._cache_index_key(scope)
            cached_keys = self.redis_client.smembers(index_key)
            if not cached_keys:
                return None

            query_vec = self._embed(query)
            threshold = self.settings.semantic_cache_similarity_threshold

            best_payload: Optional[Dict[str, Any]] = None
            best_score = -1.0

            for digest in cached_keys:
                payload_raw = self.redis_client.get(self._cache_item_key(scope, digest))
                if not payload_raw:
                    continue
                payload = json.loads(payload_raw)
                cached_vec = np.array(payload["embedding"], dtype=np.float32)
                similarity = self._cosine_similarity(query_vec, cached_vec)
                if similarity > best_score:
                    best_score = similarity
                    best_payload = payload

            if best_payload and best_score >= threshold:
                return {"response": best_payload["response"], "similarity": best_score}
        except Exception as e:
            logger.warning(f"Cache lookup failed: {str(e)}")
            return None
        return None

    def set(self, scope: str, query: str, response: Dict[str, Any]) -> None:
        try:
            query_vec = self._embed(query)
            digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
            item_key = self._cache_item_key(scope, digest)
            index_key = self._cache_index_key(scope)

            payload = {
                "query": query,
                "embedding": query_vec.tolist(),
                "response": response,
            }
            self.redis_client.setex(item_key, self.settings.semantic_cache_ttl_seconds, json.dumps(payload))
            self.redis_client.sadd(index_key, digest)
        except Exception as e:
            logger.warning(f"Cache set failed: {str(e)}")
