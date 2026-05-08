from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Minimal Celery setup - avoids circular imports and complex SSL logic
celery_app = Celery(
    "edu_ai_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Standard connection retries
    broker_connection_retry_on_startup=True,
)
