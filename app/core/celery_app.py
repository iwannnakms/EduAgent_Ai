import ssl
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Upstash/Cloud Redis requires special SSL handling
# The error "A rediss:// URL must have parameter ssl_cert_reqs" 
# is fixed by explicitly providing the ssl_cert_reqs in the broker_use_ssl dict.
broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
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
    # Use the same SSL settings for both broker and result backend
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=broker_use_ssl,
)
