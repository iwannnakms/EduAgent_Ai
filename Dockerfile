FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies: ffmpeg (for audio), curl/nodejs (for yt-dlp JS runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
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

COPY start-prod.sh .
RUN chmod +x start-prod.sh

CMD ["./start-prod.sh"]
