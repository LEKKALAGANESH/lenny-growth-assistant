# The Lenny Growth Assistant

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)
![Next.js](https://img.shields.io/badge/Next.js-14.2-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector%20%2B%20HNSW-336791)
![Docker](https://img.shields.io/badge/deploy-docker%20compose-2496ED)

> A grounded RAG assistant over Lenny Rachitsky's podcast transcripts — hybrid retrieval, multi-provider LLM routing with automatic fallback, and a Claude-style sandboxed artifact viewer.

## Overview

The Lenny Growth Assistant answers product and growth questions using only what's actually said in Lenny's Podcast, citing every claim back to a specific episode, guest, and timestamp. It combines:

- **Hybrid retrieval** — dense vector search (PostgreSQL + `pgvector`, HNSW-indexed) fused with BM25 lexical search via Reciprocal Rank Fusion, so exact terminology and semantic meaning are both captured.
- **Resilient multi-LLM routing** — a configurable primary provider with automatic fallback across a priority chain (OpenAI → Groq → Gemini by default), plus local Ollama and Anthropic Claude support, so a single provider outage never takes down the assistant.
- **Grounded citations** — every factual claim carries an inline badge like `[EP-142 • Brian Chesky @ 00:02:11]`; out-of-scope questions are refused rather than hallucinated.
- **Claude-style artifact viewer** — long-form output (PRDs, Ship 30 for 30 essays, interactive widgets) renders in a split-pane panel inside a sandboxed `<iframe sandbox="allow-scripts">` — no `allow-same-origin`, by design.

## Architecture

```
┌────────────┐      SSE / REST       ┌──────────────────┐
│  Next.js   │ ─────────────────────▶│  FastAPI backend  │
│  frontend  │◀───────────────────── │  (agent + skills) │
└────────────┘                       └─────────┬─────────┘
                                                │
                        ┌───────────────────────┼───────────────────────┐
                        ▼                       ▼                       ▼
              ┌──────────────────┐   ┌────────────────────┐   ┌──────────────────┐
              │ Hybrid retriever │   │   LLM manager       │   │  Session store    │
              │ (dense + BM25,   │   │ OpenAI → Groq →     │   │  (Postgres, with  │
              │  RRF fusion)     │   │ Gemini fallback,    │   │  SQLite fallback) │
              └────────┬─────────┘   │ + Ollama / Claude   │   └──────────────────┘
                       ▼             └────────────────────┘
              ┌──────────────────┐
              │ PostgreSQL +     │
              │ pgvector (HNSW)  │
              └──────────────────┘
```

## Key Capabilities

| Capability | Detail |
| :--- | :--- |
| **Grounded Q&A** | Inline citation badges `[Episode • Guest @ Timestamp]`; refuses out-of-domain questions instead of guessing. |
| **Hybrid RAG** | Dense cosine similarity (pgvector, HNSW index) + BM25 keyword search, merged with Reciprocal Rank Fusion. |
| **Multi-LLM fallback** | Primary provider (default `openai`) with automatic failover through `LLM_FALLBACK_ORDER` (default `groq,gemini`) on timeout, rate limit, or provider error — plus offline `ollama` and `anthropic` support. |
| **Ship 30 for 30 skill** | Generates ~1,250-word growth essays with hook, 1-3-1 sentence cadence, and a five-section structure. |
| **Sandboxed artifacts** | Interactive HTML/PRD/essay output renders in an `iframe` with `sandbox="allow-scripts"` only — never `allow-same-origin`. |
| **Health diagnostics** | `/api/health` reports live Postgres connectivity, `pgvector` extension status, HNSW index presence, embedding provider, and the active LLM fallback chain. |
| **Session persistence** | Conversations, messages, and artifacts persisted to PostgreSQL, with automatic SQLite fallback for zero-friction local dev. |

## Quickstart

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

On container start, the backend automatically waits for Postgres, verifies the `vector` extension and HNSW index, runs migrations, ingests the sample transcripts, then serves the API.

- Frontend: [http://localhost:3000](http://localhost:3000)
- API + OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5432`

### Option B — Local development

**Backend**

```bash
python -m pip install -r requirements.txt

cd backend
python -m app.rag.ingestion                 # ingest & index the sample transcripts
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

> Windows users can also double-click `scripts/run_local.bat`; macOS/Linux, run `scripts/run_local.sh`.

## Configuration

Copy `.env.example` to `.env` and fill in what you need. Nothing is required to run offline via Ollama/mock providers.

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lenny_assistant

# LLM providers (set only the ones you use)
OPENAI_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# Routing
LLM_PROVIDER=openai
LLM_FALLBACK_ORDER=groq,gemini

# Frontend -> backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

No API keys? Install [Ollama](https://ollama.com), run `ollama pull llama3.2 && ollama serve`, and select **Ollama** in the UI's provider switcher — the assistant runs fully offline. If Ollama isn't reachable either, requests route to a mock provider so the UI stays usable during evaluation.

## Testing

```bash
cd backend
pytest -v
```

Covers RAG chunking/retrieval, PostgreSQL + pgvector/HNSW persistence (skips cleanly without a live database), LLM provider abstraction and fallback chain, agent skills, and the FastAPI REST/SSE surface.

Run the standalone diagnostic script for a human-readable health check:

```bash
python scripts/verify_system.py
```

## Troubleshooting

**`ModuleNotFoundError: No module named 'backend'`**
You're running uvicorn from the repo root (`uvicorn backend.app.main:app ...`). `backend/` intentionally has no `__init__.py`, and its internal code imports as `from app.xxx import ...`, so it must run with `backend/` as the working directory. Fix:
```bash
cd backend
python -m app.rag.ingestion
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Or just run `scripts/run_local.bat` (Windows) / `scripts/run_local.sh` (macOS/Linux), which `cd` into `backend/` automatically.

**`Module not found: Can't resolve '@/lib/api'` or `'@/lib/constants'`**
Fixed — both `frontend/lib/api.js` (the backend API client) and `frontend/lib/constants.js` (`STARTER_PROMPTS` used by `QuickPrompts.js`) are present and tracked in this repo. If you still hit this on a fresh clone, check that `.gitignore`'s `lib/` rule is scoped to `/lib/` and `/backend/lib/` (not a bare `lib/`) — a bare rule silently swallows `frontend/lib/` too, which was the original root cause.

## Project Structure

```
The-Lenny-Growth-Assistant/
├── backend/
│   ├── app/
│   │   ├── agent/            # Orchestrator, skills (grounded QA, Ship30, artifacts), prompts
│   │   ├── api/endpoints/    # chat, chat/stream (SSE), sessions, models, health
│   │   ├── core/             # Settings & environment config
│   │   ├── db/               # Session/engine setup, repository layer
│   │   ├── llm/              # Provider abstraction: OpenAI, Groq, Gemini, Anthropic, Ollama, mock
│   │   ├── models/           # SQLAlchemy entities, incl. pgvector + HNSW chunk model
│   │   ├── rag/              # Parser, chunker, embeddings, hybrid (dense+BM25) retriever
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── startup_check.py  # Container-start DB/pgvector/HNSW readiness checks
│   │   └── main.py           # FastAPI app factory & CORS
│   ├── tests/                # pytest suite
│   └── Dockerfile
├── data/
│   ├── transcripts/          # Sample podcast transcripts (Chesky, Verna, Doshi, Ellis)
│   └── storage/              # SQLite/vector fallback storage for local dev
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # ArtifactViewer, ChatPane, Navbar, Sidebar, CitationModal
│   ├── lib/api.js            # Backend API client (REST + SSE streaming)
│   └── Dockerfile
├── scripts/
│   ├── verify_system.py
│   ├── run_local.sh
│   └── run_local.bat
├── docker-compose.yml         # postgres (pgvector) + backend + frontend
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── design.md
└── agent_transcripts/
    ├── 01_initial_scaffolding.md
    └── 02_debugging_pgvector_indexing.md
```

## Documentation

| Document | Purpose |
| :--- | :--- |
| [`docs/PRD.md`](./docs/PRD.md) | Product requirements, personas, jobs-to-be-done, success metrics |
| [`docs/architecture.md`](./docs/architecture.md) | System architecture, hybrid RAG design, LLM routing, and security model |
| [`docs/design.md`](./docs/design.md) | Dual-pane UI split, state transitions, and responsive behavior |
| [`agent_transcripts/`](./agent_transcripts/) | Process log: the scaffolding/merge decision and the real debugging chain behind the current retrieval + provider-fallback implementation |
