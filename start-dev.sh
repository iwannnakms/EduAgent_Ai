#!/bin/bash

# Configuration
API_PORT=8000
FRONTEND_PORT=5173

echo "🚀 Starting EDU-AI Platform..."

# 1. Ensure environment is set up
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# 2. Start infrastructure (Redis and Chroma) via Docker if available
# This is the easiest way to ensure these are running correctly.
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "📦 Starting Redis and Chroma via Docker..."
    docker compose up -d redis chroma
else
    echo "⚠️ Docker not found or not running. Please ensure Redis (6379) and Chroma (8001) are running locally."
fi

# 3. Start Backend in background
echo "🐍 Starting FastAPI Backend on port $API_PORT..."
python3 -m uvicorn app.main:app --host 127.0.0.1 --port $API_PORT --reload > /dev/null 2>&1 &
BACKEND_PID=$!

# 4. Start Celery Worker in background
echo "👷 Starting Celery Worker..."
celery -A worker.celery_app worker -l info > /dev/null 2>&1 &
WORKER_PID=$!

# 5. Start Frontend
echo "⚛️ Starting Vite Frontend on port $FRONTEND_PORT..."
cd frontend && npm run dev

# Cleanup background processes on exit
trap "kill $BACKEND_PID $WORKER_PID; exit" INT TERM
