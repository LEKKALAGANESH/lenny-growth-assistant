# Production Dockerfile for The Lenny Growth Assistant Backend (FastAPI)
FROM python:3.11-slim

WORKDIR /app

# Install system utilities and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code and data corpus
COPY backend/app /app/app
COPY data /app/data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PYTHONPATH=/app
ENV STORAGE_PATH=/app/data/storage
ENV TRANSCRIPTS_DIR=/app/data/transcripts

# Run ingestion indexing on container build / boot
RUN python -m app.rag.ingestion

EXPOSE 8000

# Start FastAPI production ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
