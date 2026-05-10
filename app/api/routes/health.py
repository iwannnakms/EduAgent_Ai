from fastapi import APIRouter
import logging

from app.core.config import get_settings
from app.models.schemas import HealthResponse
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(service=settings.app_name)

@router.get("/worker")
async def worker_health():
    """Checks if the worker is reachable and responding."""
    try:
        # Use a string name for the heartbeat task to avoid circular imports
        task = celery_app.send_task("tasks.heartbeat")
        # Wait up to 5 seconds for a response
        result = task.get(timeout=5.0)
        return {"status": "ok", "worker_response": result}
    except Exception as e:
        logger.error(f"Worker health check failed: {str(e)}")
        return {"status": "error", "message": str(e)}
