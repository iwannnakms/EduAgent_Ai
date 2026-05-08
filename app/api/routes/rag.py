import base64
import logging
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pypdf import PdfReader

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.models.schemas import (
    RAGIngestResponse,
    RAGIngestTextRequest,
    RAGIngestYoutubeRequest,
    RAGQueryRequest,
    RAGQueryResponse,
    TaskAcceptedResponse,
    TaskStatusResponse,
)
from app.services.rag_service import RAGService
from app.tasks.rag_tasks import ingest_file_task, ingest_text_task, ingest_youtube_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest/text", response_model=RAGIngestResponse)
async def ingest_text(payload: RAGIngestTextRequest) -> RAGIngestResponse:
    service = RAGService()
    count = service.ingest_text(
        document_id=payload.document_id,
        text=payload.text,
        metadata=payload.metadata,
    )
    return RAGIngestResponse(document_id=payload.document_id, chunks_ingested=count, backend=service.backend)


@router.post("/ingest/text/async", response_model=TaskAcceptedResponse)
async def ingest_text_async(payload: RAGIngestTextRequest) -> TaskAcceptedResponse:
    task = ingest_text_task.delay(
        document_id=payload.document_id,
        text=payload.text,
        metadata=payload.metadata,
    )
    return TaskAcceptedResponse(
        task_id=task.id,
        message="RAG text ingestion started. Poll /api/v1/rag/tasks/{task_id} for status.",
    )


@router.post("/ingest/file", response_model=RAGIngestResponse)
async def ingest_file(document_id: str = Form(...), file: UploadFile = File(...)) -> RAGIngestResponse:
    content = await file.read()
    filename = file.filename or "uploaded_file"
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        text = "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
    else:
        text = content.decode("utf-8", errors="ignore")

    service = RAGService()
    count = service.ingest_text(
        document_id=document_id,
        text=text,
        metadata={"filename": filename},
    )
    return RAGIngestResponse(document_id=document_id, chunks_ingested=count, backend=service.backend)


@router.post("/ingest/file/async", response_model=TaskAcceptedResponse)
async def ingest_file_async(document_id: str = Form(...), file: UploadFile = File(...)) -> TaskAcceptedResponse:
    filename = file.filename or "uploaded_file"
    
    try:
        content = await file.read()
        content_b64 = base64.b64encode(content).decode("utf-8")
        
        task = ingest_file_task.delay(
            document_id=document_id,
            file_content_b64=content_b64,
            metadata={"filename": filename},
        )
        return TaskAcceptedResponse(
            task_id=task.id,
            message="RAG file ingestion started. Poll /api/v1/rag/tasks/{task_id} for status.",
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/youtube", response_model=TaskAcceptedResponse)
async def ingest_youtube(payload: RAGIngestYoutubeRequest) -> TaskAcceptedResponse:
    task = ingest_youtube_task.delay(
        document_id=payload.document_id,
        youtube_url=str(payload.youtube_url),
        target_language=payload.target_language,
        metadata=payload.metadata,
    )
    return TaskAcceptedResponse(
        task_id=task.id,
        message="RAG YouTube ingestion started. Poll /api/v1/rag/tasks/{task_id} for status.",
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_rag_task_status(task_id: str) -> TaskStatusResponse:
    task = AsyncResult(task_id, app=celery_app)
    if task.failed():
        return TaskStatusResponse(task_id=task_id, status=task.status, error=str(task.result))
    if task.successful():
        return TaskStatusResponse(task_id=task_id, status=task.status, result=task.result)
    return TaskStatusResponse(task_id=task_id, status=task.status)


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(payload: RAGQueryRequest) -> RAGQueryResponse:
    service = RAGService()
    result = service.answer_query(query=payload.query, document_id=payload.document_id, top_k=payload.top_k)
    return RAGQueryResponse(**result)
