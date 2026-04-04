from app.core.celery_app import celery_app
from app.services.video_service import VideoService


@celery_app.task(name="tasks.video.process_video")
def process_video_task(youtube_url: str, target_language: str | None = "en", max_summary_tokens: int = 350) -> dict:
    service = VideoService()
    return service.process_video(
        youtube_url=youtube_url,
        target_language=target_language,
        max_summary_tokens=max_summary_tokens,
    )
