from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @field_validator("redis_url", "celery_broker_url", "celery_result_backend", mode="after")
    @classmethod
    def force_redis_db_zero(cls, v: Any) -> str:
        s = str(v)
        if s.startswith("redis"):
            import re
            # Replaces /N with /0, preserving query parameters
            # e.g., /2?ssl=true -> /0?ssl=true, or /2 -> /0
            new_v = re.sub(r"/(\d+)(\?|$)", r"/0\2", s)
            if new_v != s:
                import logging
                logging.getLogger(__name__).warning(f"Forcing Redis DB 0: {s} -> {new_v}")
            return new_v
        return s

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


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    return settings
