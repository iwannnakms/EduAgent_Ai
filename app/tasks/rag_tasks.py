from io import BytesIO
from pathlib import Path
from typing import Any, Dict

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
def ingest_file_task(document_id: str, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(file_path)
    try:
        content = path.read_bytes()
        filename = metadata.get("filename", path.name)
        if filename.lower().endswith(".pdf"):
            reader = PdfReader(BytesIO(content))
            text = "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
        else:
            text = content.decode("utf-8", errors="ignore")

        service = RAGService()
        chunks = service.ingest_text(document_id=document_id, text=text, metadata=metadata)
        return {"document_id": document_id, "chunks_ingested": chunks, "backend": service.backend}
    finally:
        path.unlink(missing_ok=True)


@celery_app.task(name="tasks.rag.ingest_youtube")
def ingest_youtube_task(document_id: str, youtube_url: str, target_language: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    video_service = VideoService()
    
    # 1. Fetch transcript using our optimized service
    transcript = video_service._get_youtube_transcript(youtube_url, target_language)
    
    if not transcript:
        # Fallback to audio extraction (needs ffmpeg/yt-dlp)
        audio_path = video_service._extract_audio(youtube_url)
        try:
            transcript = video_service.transcribe_audio(audio_path, target_language)
        finally:
            if audio_path.exists():
                audio_path.unlink(missing_ok=True)

    if not transcript:
        raise ValueError(f"Could not retrieve transcript for {youtube_url}")

    # 2. Ingest into RAG
    rag_service = RAGService()
    combined_metadata = {**metadata, "source_url": youtube_url, "type": "youtube_transcript"}
    chunks = rag_service.ingest_text(document_id=document_id, text=transcript, metadata=combined_metadata)
    
    return {"document_id": document_id, "chunks_ingested": chunks, "backend": rag_service.backend}
