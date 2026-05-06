#!/bin/bash
# start-prod.sh
# This script starts both the API and the Celery Worker in a single container for Render/Railway

# 1. Start the Celery Worker in the background
echo "Starting Celery Worker..."
celery -A worker.celery_app worker --loglevel=info &

# 2. Start the FastAPI server (this remains in the foreground)
echo "Starting FastAPI API on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
