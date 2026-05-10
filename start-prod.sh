#!/bin/bash
# start-prod.sh

# 1. Ensure directories exist with correct permissions
echo "Preparing directories..."
mkdir -p data/uploads data/tmp data/chroma

# 2. Set PYTHONPATH so the worker can find the 'app' module
export PYTHONPATH=$PYTHONPATH:.

# 3. Start the Celery Worker in the background
echo "Starting Celery Worker..."
celery -A worker.celery_app worker --pool=threads --concurrency=4 --loglevel=info &

# 4. Start the FastAPI server (this remains in the foreground)
echo "Starting FastAPI API on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
