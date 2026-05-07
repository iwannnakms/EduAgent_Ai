from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Upstash/Cloud Redis requires special SSL handling
broker_use_ssl = {
    'ssl_cert_reqs': None
} if settings.celery_broker_url.startswith('rediss://') else False

celery_app = Celery(
    "edu_ai_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.rag_tasks", "app.tasks.video_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Fix for Upstash SSL
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=broker_use_ssl,
)
