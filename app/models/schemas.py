from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str


class VideoSummarizeRequest(BaseModel):
    youtube_url: HttpUrl
    target_language: Optional[str] = "en"
    max_summary_tokens: int = Field(default=350, ge=100, le=1200)


class TaskAcceptedResponse(BaseModel):
    task_id: str
    status: Literal["queued"] = "queued"
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RAGIngestTextRequest(BaseModel):
    document_id: str
    text: str = Field(min_length=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGIngestYoutubeRequest(BaseModel):
    document_id: str
    youtube_url: HttpUrl
    target_language: Optional[str] = "en"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGIngestResponse(BaseModel):
    document_id: str
    chunks_ingested: int
    backend: str


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=2)
    document_id: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=20)


class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[RetrievedChunk]
    cache_hit: bool = False


class RoadmapRequest(BaseModel):
    topic: str = Field(min_length=2)
    learner_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    target_duration_weeks: int = Field(default=12, ge=1, le=52)


class RoadmapStep(BaseModel):
    step: int
    title: str
    outcomes: List[str]
    resources: List[str]
    estimated_hours: int


class RoadmapResponse(BaseModel):
    topic: str
    learner_level: str
    total_weeks: int
    steps: List[RoadmapStep]
