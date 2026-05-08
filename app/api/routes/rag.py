import base64
import zlib
import logging
from io import BytesIO

from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pypdf import PdfReader

from app.core.celery_app import celery_app
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
    # Use send_task to avoid circular imports
    task = celery_app.send_task(
        "tasks.rag.ingest_text",
        kwargs={
            "document_id": payload.document_id,
            "text": payload.text,
            "metadata": payload.metadata,
        }
    )
    return TaskAcceptedResponse(
        task_id=task.id,
        message="RAG text ingestion started.",
    )


@router.post("/ingest/file", response_model=RAGIngestResponse)
async def ingest_file(document_id: str = Form(...), file: UploadFile = File(...)) -> RAGIngestResponse:
    try:
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
    except Exception as e:
        logger.error(f"Sync ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/file/async", response_model=TaskAcceptedResponse)
async def ingest_file_async(document_id: str = Form(...), file: UploadFile = File(...)) -> TaskAcceptedResponse:
    filename = file.filename or "uploaded_file"
    
    try:
        # 1. Read file
        content = await file.read()
        
        # 2. Compress and encode (extremely efficient for text-based PDFs)
        compressed_data = zlib.compress(content)
        compressed_b64 = base64.b64encode(compressed_data).decode("utf-8")
        
        # 3. Dispatch using send_task (No Imports = No Crashes)
        task = celery_app.send_task(
            "tasks.rag.ingest_file_compressed",
            kwargs={
                "document_id": document_id,
                "compressed_b64": compressed_b64,
                "metadata": {"filename": filename},
            }
        )
        
        return TaskAcceptedResponse(
            task_id=task.id,
            message=f"Received {filename}. Ingestion started.",
        )
    except Exception as e:
        logger.error(f"Ingestion dispatch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/youtube", response_model=TaskAcceptedResponse)
async def ingest_youtube(payload: RAGIngestYoutubeRequest) -> TaskAcceptedResponse:
    task = celery_app.send_task(
        "tasks.rag.ingest_youtube",
        kwargs={
            "document_id": payload.document_id,
            "youtube_url": str(payload.youtube_url),
            "target_language": payload.target_language,
            "metadata": payload.metadata,
        }
    )
    return TaskAcceptedResponse(
        task_id=task.id,
        message="RAG YouTube ingestion started.",
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
