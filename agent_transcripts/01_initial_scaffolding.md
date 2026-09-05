# 01 — Initial Scaffolding: Merge Decision, Not a Rebuild

This project did not start from an empty repository. Two independent implementations of the
same assignment already existed on disk:

- `The-Lenny-Growth-Assistant/` (this project, referred to below as TARGET)
- `The_Lenny_Growth/` (a second attempt, referred to below as DONOR — kept read-only throughout,
  never modified)

The first engineering decision was **audit, don't guess**: both projects were scored against the
requirements spec by reading actual code, not filenames or READMEs.

## Findings from the initial audit

| Area | TARGET | DONOR |
|---|---|---|
| PostgreSQL + pgvector + HNSW | Flat JSON file + numpy cosine similarity — **not compliant** | Real SQLAlchemy model with a pgvector column + hybrid BM25 retrieval |
| Docker deployment | Full `docker-compose.yml`, Dockerfiles | None at all |
| Ship 30 essay length | Correctly targets ~1,250 words | Validator hard-capped essays at 300 words (inverted the spec) |
| Citation format | `[EP-142 • Brian Chesky @ 00:02:11]` | `[Chunk ID: X]` — didn't match spec format |
| Artifact sandbox | `sandbox="allow-scripts"` only (correct) | `sandbox="allow-same-origin allow-scripts"` — the exact combo the spec forbids |
| Dual LLM providers | Ollama/Anthropic/OpenAI, env + per-request switching | Ollama/Anthropic only, boolean flag |

Overall: TARGET ~71% compliant, DONOR ~48%, but each had a genuinely stronger piece the other
lacked. TARGET's retrieval layer was the one hard blocker; everything else it already did as well
or better.

## Decision: surgical merge, not a rewrite

Rather than rebuilding either project from scratch, the plan was to keep TARGET as the final
deliverable and **port only the PostgreSQL/pgvector/HNSW retrieval layer** from DONOR into it,
preserving TARGET's existing interfaces so nothing downstream (`hybrid_retriever.py`,
`orchestrator.py`, `health.py`) needed to change:

1. Ported DONOR's pgvector `Vector` column pattern into TARGET's `models/entities.py`, upgrading
   the index type from DONOR's `ivfflat` to the spec-required `hnsw`.
2. Rewrote `rag/vector_store.py`'s internals to query Postgres via cosine distance, keeping the
   exact same `PersistentVectorStore` public interface — with an automatic fallback to the
   flat-JSON store when Postgres isn't reachable (mirroring the existing Postgres→SQLite pattern
   already in `db/session.py`), so local dev and tests don't require Docker.
3. Kept TARGET's own `hybrid_retriever.py` (Reciprocal Rank Fusion over dense+BM25) as-is — it was
   already correct and arguably stronger than DONOR's equivalent, so it was pointed at the new
   store instead of being replaced.
4. Updated `docker-compose.yml` to add a `pgvector/pgvector:pg16` Postgres service, and moved
   transcript ingestion from Docker build-time to container-start (Postgres isn't reachable during
   `docker build`).
5. Never touched a single file under `The_Lenny_Growth/` — verified after every change with
   `git diff --stat` against it.

This established the working pattern for the rest of the engagement: identify the smallest set of
files that need to change, verify the specific claim (read the code, run the tests, hit the real
API) before acting on it, and never assume a prior audit's numbers are still accurate once the code
has moved.
