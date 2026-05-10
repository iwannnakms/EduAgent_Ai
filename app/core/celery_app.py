import os
import ssl
from celery import Celery
from app.core.config import get_settings

# Force environment variables to be set before Celery even thinks about them
settings = get_settings()
os.environ["CELERY_BROKER_URL"] = settings.celery_broker_url
os.environ["CELERY_RESULT_BACKEND"] = settings.celery_result_backend

broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

# SSL configuration for secure Redis (rediss://)
ssl_conf = {
    'ssl_cert_reqs': ssl.CERT_NONE
} if broker_url.startswith('rediss://') else None

celery_app = Celery(
    "edu_ai_tasks",
    broker=broker_url,
    backend=result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_use_ssl=ssl_conf,
    redis_backend_use_ssl=ssl_conf,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    # CRITICAL FIX: Change default queue to avoid poisoned tasks from previous runs
    task_default_queue="edu_ai_queue_v2",
    # This ensures that the worker registers tasks correctly
    imports=("app.tasks.rag_tasks", "app.tasks.video_tasks"),
)
