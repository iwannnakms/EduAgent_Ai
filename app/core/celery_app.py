import os
import ssl
from celery import Celery
from app.core.config import get_settings

# This load will force os.environ to use database 0
settings = get_settings()

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
)

# Force the worker to discover tasks across the 'app.tasks' package
celery_app.autodiscover_tasks(['app.tasks'], force=True)
