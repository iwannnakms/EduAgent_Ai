import ssl
from celery import Celery
from app.core.config import get_settings

# Settings load here will force os.environ to DB 0 via the model_validator
settings = get_settings()

broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

ssl_conf = {
    'ssl_cert_reqs': ssl.CERT_NONE
} if broker_url.startswith('rediss://') else None

celery_app = Celery(
    "edu_ai_tasks",
    broker=broker_url,
    backend=result_backend,
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

# Break circular dependency by using autodiscover instead of include in constructor
celery_app.autodiscover_tasks(['app.tasks'], force=True)
