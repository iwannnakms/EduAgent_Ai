import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from pypdf import PdfReader

from app.core.celery_app import celery_app
from app.services.rag_service import RAGService
from app.services.video_service import VideoService


@celery_app.task(name="tasks.rag.ingest_text")
def ingest_text_task(document_id: str, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    service = RAGService()
    chunks = service.ingest_text(document_id=document_id, text=text, metadata=metadata)
    return {"document_id": document_id, "chunks_ingested": chunks, "backend": service.backend}


@celery_app.task(name="tasks.rag.ingest_file")
def ingest_file_task(
    document_id: str, 
    file_path: Optional[str] = None, 
    file_content_b64: Optional[str] = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    metadata = metadata or {}
    filename = metadata.get("filename", "unknown_file")
    
    try:
        if file_content_b64:
            content = base64.b64decode(file_content_b64)
        elif file_path:
            path = Path(file_path)
            content = path.read_bytes()
            # Cleanup if it was a local file
            path.unlink(missing_ok=True)
        else:
            raise ValueError("No file content or path provided")

        if filename.lower().endswith(".pdf"):
            reader = PdfReader(BytesIO(content))
            text = "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
        else:
            text = content.decode("utf-8", errors="ignore")

        if not text:
            raise ValueError(f"No text extracted from {filename}")

        service = RAGService()
        chunks = service.ingest_text(document_id=document_id, text=text, metadata=metadata)
        return {"document_id": document_id, "chunks_ingested": chunks, "backend": service.backend}
    except Exception as e:
        raise e


@celery_app.task(name="tasks.rag.ingest_youtube")
def ingest_youtube_task(document_id: str, youtube_url: str, target_language: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    video_service = VideoService()
    transcript = video_service._get_youtube_transcript(youtube_url, target_language)
    
    if not transcript:
        audio_path = video_service._extract_audio(youtube_url)
        try:
            transcript = video_service.transcribe_audio(audio_path, target_language)
        finally:
            if audio_path.exists():
                audio_path.unlink(missing_ok=True)

    if not transcript:
        raise ValueError(f"Could not retrieve transcript for {youtube_url}")

    rag_service = RAGService()
    combined_metadata = {**metadata, "source_url": youtube_url, "type": "youtube_transcript"}
    chunks = rag_service.ingest_text(document_id=document_id, text=transcript, metadata=combined_metadata)
    
    return {"document_id": document_id, "chunks_ingested": chunks, "backend": rag_service.backend}
