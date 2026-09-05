#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "  Starting The Lenny Growth Assistant (Local Development Mode)"
echo "======================================================================"

echo "[1/3] Ingesting & Verifying Knowledge Base Transcripts..."
python -m backend.app.rag.ingestion

echo "[2/3] Starting FastAPI Backend on http://localhost:8000..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[3/3] Starting Next.js Frontend on http://localhost:3000..."
cd frontend
npm run dev

trap "kill $BACKEND_PID" EXIT
