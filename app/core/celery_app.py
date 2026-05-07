import os
import ssl
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Use sanitized URLs from settings (already forced to DB 0 in config.py)
broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

# CRITICAL FIX: Celery automatically reads these environment variables and 
# overrides any programmatic configuration. We MUST update os.environ 
# to force Celery to use the sanitized database 0 URLs.
os.environ["CELERY_BROKER_URL"] = broker_url
os.environ["CELERY_RESULT_BACKEND"] = result_backend

# SSL configuration for managed Redis (e.g., Upstash, Heroku, Render)
ssl_conf = {
    'ssl_cert_reqs': ssl.CERT_NONE
} if broker_url.startswith('rediss://') else None

celery_app = Celery(
    "edu_ai_tasks",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.rag_tasks", "app.tasks.video_tasks"],
)

# Explicitly update configuration to ensure forced URLs take precedence
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
