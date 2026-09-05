# The Lenny Growth Assistant
> **Full-Stack AI Conversational Intelligence Platform Grounded in Lenny's Podcast Transcripts**  

---

## Executive Overview

**The Lenny Growth Assistant** is an enterprise-grade AI copilot built to deliver actionable, grounded product management and growth strategy advice. Grounded directly in transcripts from Lenny Rachitsky's podcast interviews (including **Brian Chesky**, **Elena Verna**, **Shreyas Doshi**, and **Sean Ellis**), the platform pairs hybrid RAG retrieval with dynamic multi-LLM routing (**Local Ollama**, **Claude 3.5 Sonnet**, **GPT-4o**) and a **Claude-style split-pane Artifact Viewer** for interactive widgets, PRD templates, and Ship 30 for 30 essays.

---

## Key Architectural Capabilities

- **Strict Grounding & Anti-Hallucination**: 100% of factual assertions include inline bracketed citation badges `[EP-142 • Brian Chesky @ 00:02:11]`. Clicking any badge reveals the exact timestamp and transcript excerpt. Out-of-scope questions are gracefully refused.
- **Claude-Style Dual-Pane Artifact Viewer**: Automatically opens an interactive right-hand panel when generating live HTML/CSS widgets, ROI calculators, or long-form PRD templates, executing inside a secure `<iframe>` (`sandbox="allow-scripts"`).
- **Ship 30 for 30 Content Skill**: Generates high-density ~1,250-word synthesis essays structured with Hooks, 1/3/1 sentence cadences, and scannable subheadings.
- **Hybrid Retrieval with Reciprocal Rank Fusion (RRF)**: Combines dense vector cosine similarity with BM25 lexical keyword matching to accurately capture both concepts and exact practitioner terminology.
- **Dynamic Multi-LLM Routing**: Switch seamlessly between local zero-cost offline models (**Ollama `llama3.2` / `mistral`**) and frontier cloud models (**Claude 3.5 Sonnet / GPT-4o**) with resilient fallbacks.
- **PostgreSQL Persistence & Session Isolation**: Multi-turn conversation history, artifact versions, and audit logs stored with automatic SQLite fallback for zero-friction local testing.

---

## Quickstart Guide

### Option A: Single-Command Docker Compose (Recommended)

Ensure Docker Desktop is running, then run:

```bash
docker compose up --build
```

- **Frontend Application**: `http://localhost:3000`
- **FastAPI API & OpenAPI Docs**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5432`

---

### Option B: Local Development Setup

#### 1. Backend Setup (FastAPI & Vector Ingestion)
```bash
# In project root:
python -m pip install -r requirements.txt

# Ingest & index podcast transcripts
python -m backend.app.rag.ingestion

# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup (Next.js / JavaScript)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Local Ollama Setup (Zero-Cost Offline Demo)

To run the assistant completely offline without API keys:

1. Install [Ollama](https://ollama.com).
2. Pull the recommended local model:
   ```bash
   ollama pull llama3.2
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```
4. In the top navbar of the web UI, select **Ollama (Local LLM - llama3.2)**. The status dot will turn **green (Ready)**.

*(Optional)* If Ollama is not installed or offline, the platform automatically routes requests to the **Mock Local Provider** to ensure uninterrupted evaluation.

---

## Cloud LLM Configuration (Optional)

Create a `.env` file in the project root based on `.env.example`:

```bash
# Cloud Providers
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...

# Default provider on startup
DEFAULT_LLM_PROVIDER=ollama
```

---

## Automated Test Suite (29/29 Passing)

Run the full automated pytest suite covering RAG, DB, LLM abstractions, Agent skills, and FastAPI REST/SSE endpoints:

```bash
python -m pytest backend/tests/ -v
```

### System Health Diagnostic CLI
Run the diagnostic script to verify database connectivity, vector index search, and LLM reachability:

```bash
python scripts/verify_system.py
```

---

## Project Structure

```
The Lenny Growth Assistant/
├── backend/
│   ├── app/
│   │   ├── agent/               # Agent orchestrator, skills, prompts, stream parser
│   │   ├── api/                 # FastAPI endpoints (chat, stream, sessions, models, health)
│   │   ├── core/                # App config & environment settings
│   │   ├── db/                  # Database session & repository layer
│   │   ├── llm/                 # Multi-LLM provider abstraction (Ollama, Claude, OpenAI, Mock)
│   │   ├── models/              # SQLAlchemy persistence entities
│   │   ├── rag/                 # Transcript parser, chunker, embeddings, hybrid retriever
│   │   ├── schemas/             # Pydantic validation schemas
│   │   └── main.py              # FastAPI app factory & CORS
│   ├── tests/                   # 29 automated test cases (pytest)
│   └── Dockerfile               # Backend Docker container
├── data/
│   ├── transcripts/             # Podcast transcripts (Chesky, Verna, Doshi, Ellis)
│   └── storage/                 # Persistent vector store & fallback SQLite DB
├── frontend/
│   ├── app/                     # Next.js App Router (layout.js, page.js, globals.css)
│   ├── components/              # Claude-style ArtifactViewer, ChatPane, Navbar, Sidebar
│   ├── lib/                     # SSE streaming client & constants
│   └── Dockerfile               # Multi-stage Next.js Docker container
├── scripts/
│   ├── verify_system.py         # End-to-end diagnostic runner
│   ├── run_local.bat            # Windows one-click launcher
│   └── run_local.sh             # Unix one-click launcher
├── docker-compose.yml           # Multi-container orchestration
├── PRD.md                       # Product Requirements Document
├── architecture.md              # Technical Architecture & Security Specification
```

---

## Documentation Deliverables Index

| Document | Purpose |
| :--- | :--- |
| **[`PRD.md`](./PRD.md)** | Product Requirements Document, Personas, JTBDs, and Success KPIs |
| **[`architecture.md`](./architecture.md)** | End-to-End System Architecture, Hybrid RAG, Multi-LLM Routing & Security |