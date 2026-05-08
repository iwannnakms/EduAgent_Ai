from celery.result import AsyncResult
from fastapi import APIRouter

from app.core.celery_app import celery_app
from app.models.schemas import TaskAcceptedResponse, TaskStatusResponse, VideoSummarizeRequest

router = APIRouter(prefix="/video", tags=["video"])


@router.post("/summarize", response_model=TaskAcceptedResponse)
async def summarize_video(payload: VideoSummarizeRequest) -> TaskAcceptedResponse:
    # Use send_task to avoid circular imports and ensure consistent dispatch
    task = celery_app.send_task(
        "tasks.video.process_video",
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


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_video_task_status(task_id: str) -> TaskStatusResponse:
    task = AsyncResult(task_id, app=celery_app)
    if task.failed():
        return TaskStatusResponse(task_id=task_id, status=task.status, error=str(task.result))
    if task.successful():
        return TaskStatusResponse(task_id=task_id, status=task.status, result=task.result)
    return TaskStatusResponse(task_id=task_id, status=task.status)
