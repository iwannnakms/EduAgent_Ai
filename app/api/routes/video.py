import logging
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.core.celery_app import celery_app
from app.models.schemas import TaskAcceptedResponse, TaskStatusResponse, VideoSummarizeRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video", tags=["video"])


@router.post("/summarize", response_model=TaskAcceptedResponse)
async def summarize_video(payload: VideoSummarizeRequest) -> TaskAcceptedResponse:
    try:
        # Use send_task to avoid circular imports and ensure consistent dispatch
        task_name = "tasks.video.process_video"
        logger.info(f"Sending task {task_name} for URL: {payload.youtube_url}")
        
        task = celery_app.send_task(
            task_name,
            kwargs={
                "youtube_url": str(payload.youtube_url),
                "target_language": payload.target_language,
                "max_summary_tokens": payload.max_summary_tokens,
            }
        )
        return TaskAcceptedResponse(
            task_id=task.id,
            message="Video processing started.",
        )
    except Exception as e:
        logger.error(f"Failed to send video task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enqueue task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_video_task_status(task_id: str) -> TaskStatusResponse:
    try:
        task = AsyncResult(task_id, app=celery_app)
        if task.failed():
            return TaskStatusResponse(task_id=task_id, status=task.status, error=str(task.result))
        if task.successful():
            return TaskStatusResponse(task_id=task_id, status=task.status, result=task.result)
        return TaskStatusResponse(task_id=task_id, status=task.status)
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        return TaskStatusResponse(task_id=task_id, status="ERROR", error=str(e))
