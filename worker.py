import logging
import sys
from app.core.celery_app import celery_app

# Set up logging for the worker startup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing worker with PYTHONPATH: %s", sys.path)

# Ensure tasks are imported and registered
from app.tasks.rag_tasks import ingest_file_compressed_task, ingest_text_task, ingest_youtube_task
from app.tasks.video_tasks import process_video_task

@celery_app.task(name="tasks.heartbeat")
def heartbeat_task():
    return "ok"

logger.info("Worker tasks registered successfully.")
