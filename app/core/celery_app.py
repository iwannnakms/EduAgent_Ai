import ssl
import re
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

def _force_db_zero(url: str) -> str:
    if not url or not url.startswith("redis"):
        return url
    # Use regex to find the database index (e.g., /1, /2) and replace it with /0
    # This handles both redis:// and rediss:// and supports query parameters
    return re.sub(r"(\/)\d+(\?|$)", r"\1 0\2", url).replace(" ", "")

broker_url = _force_db_zero(settings.celery_broker_url)
result_backend = _force_db_zero(settings.celery_result_backend)

# Upstash/Cloud Redis requires special SSL handling
broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
} if broker_url.startswith('rediss://') else False

celery_app = Celery(
    "edu_ai_tasks",
    broker=broker_url,
    backend=result_backend,
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
