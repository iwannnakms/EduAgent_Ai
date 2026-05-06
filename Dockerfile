FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies: ffmpeg, nodejs, and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 1. Build Frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# 2. Setup Backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the built frontend is in the right place (if not already copied)
# app/main.py expects it at frontend/dist

COPY start-prod.sh .
RUN chmod +x start-prod.sh

CMD ["./start-prod.sh"]
