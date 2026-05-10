import logging
from io import BytesIO
from uuid import uuid4

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

        if not text:
            raise ValueError(f"No readable text in {filename}")

        service = RAGService()
        count = service.ingest_text(
            document_id=document_id,
            text=text,
            metadata={"filename": filename},
        )
        return RAGIngestResponse(document_id=document_id, chunks_ingested=count, backend=service.backend)
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/file/async", response_model=TaskAcceptedResponse)
async def ingest_file_async(document_id: str = Form(...), file: UploadFile = File(...)) -> TaskAcceptedResponse:
    """
    DEPRECATED ASYNC: Cloud-Native Stability Fix.
    We now run ingestion synchronously to avoid Redis payload limits and Shared Disk issues.
    This returns a 'fake' successful task to keep the frontend working perfectly.
    """
    result = await ingest_file(document_id, file)
    
    # Return a fake task_id that the poller will recognize as SUCCESS immediately
    return TaskAcceptedResponse(
        task_id=f"sync_{uuid4()}",
        message=f"Processed {file.filename} successfully ({result.chunks_ingested} chunks).",
    )

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_rag_task_status(task_id: str) -> TaskStatusResponse:
    # Handle the 'fake' sync tasks immediately
    if task_id.startswith("sync_"):
        return TaskStatusResponse(task_id=task_id, status="SUCCESS", result={"message": "Already processed"})
        
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
