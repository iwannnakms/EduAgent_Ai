import os
import ssl
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Force database 0 in environment so Celery doesn't use provider defaults
os.environ["CELERY_BROKER_URL"] = settings.celery_broker_url
os.environ["CELERY_RESULT_BACKEND"] = settings.celery_result_backend

broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

ssl_conf = {
    'ssl_cert_reqs': ssl.CERT_NONE
} if broker_url.startswith('rediss://') else None

celery_app = Celery(
    "edu_ai_tasks",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.rag_tasks", "app.tasks.video_tasks"],
)

celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_use_ssl=ssl_conf,
    redis_backend_use_ssl=ssl_conf,
)
