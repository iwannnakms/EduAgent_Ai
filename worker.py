import logging
import sys
from app.core.celery_app import celery_app

# Set up logging for the worker startup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing worker startup sequence...")

try:
    # Safely import tasks
    from app.tasks.rag_tasks import ingest_file_compressed_task, ingest_text_task, ingest_youtube_task
    from app.tasks.video_tasks import process_video_task
    logger.info("All tasks successfully imported and registered with worker.")
except Exception as e:
    logger.error("CRITICAL: Failed to import tasks. Worker will likely fail: %s", str(e))

@celery_app.task(name="tasks.heartbeat")
def heartbeat_task():
    return "ok"

# This alias makes 'celery -A worker worker' valid
app = celery_app

logger.info("Worker initialization complete.")
