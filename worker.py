from app.core.celery_app import celery_app
from app.tasks.rag_tasks import ingest_file_compressed_task, ingest_text_task
from app.tasks.video_tasks import process_video_task

# This ensures the worker has all tasks registered with their correct names
__all__ = (
    "celery_app", 
    "process_video_task", 
    "ingest_text_task", 
    "ingest_file_compressed_task"
)

@celery_app.task(name="tasks.heartbeat")
def heartbeat_task():
    return "ok"
