import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

def _force_db_zero(url: Any) -> str:
    s = str(url)
    if not s.startswith("redis"):
        return s
    try:
        u = urlparse(s)
        # Force path to /0
        new_u = u._replace(path="/0")
        return urlunparse(new_u)
    except Exception:
        return s

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="edu-ai-platform", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_chat_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_CHAT_MODEL")
    gemini_embedding_model: str = Field(default="text-embedding-004", alias="GEMINI_EMBEDDING_MODEL")
    gemini_audio_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_AUDIO_MODEL")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")

    vector_backend: str = Field(default="chroma", alias="VECTOR_BACKEND")
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="edu-ai-index", alias="PINECONE_INDEX_NAME")
    pinecone_host: str = Field(default="", alias="PINECONE_HOST")
    pinecone_namespace: str = Field(default="default", alias="PINECONE_NAMESPACE")
    chroma_collection_name: str = Field(default="edu_ai_docs", alias="CHROMA_COLLECTION_NAME")
    chroma_persist_dir: str = Field(default="./data/chroma", alias="CHROMA_PERSIST_DIR")
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8001, alias="CHROMA_PORT")

    semantic_cache_ttl_seconds: int = Field(default=3600, alias="SEMANTIC_CACHE_TTL_SECONDS")
    semantic_cache_similarity_threshold: float = Field(default=0.92, alias="SEMANTIC_CACHE_SIMILARITY_THRESHOLD")
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    temp_dir: str = Field(default="./data/tmp", alias="TEMP_DIR")

    @model_validator(mode="after")
    def sanitize_redis_urls(self) -> "Settings":
        self.redis_url = _force_db_zero(self.redis_url)
        self.celery_broker_url = _force_db_zero(self.celery_broker_url)
        self.celery_result_backend = _force_db_zero(self.celery_result_backend)
        return self

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    Path(s.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(s.temp_dir).mkdir(parents=True, exist_ok=True)
    Path(s.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    return s
