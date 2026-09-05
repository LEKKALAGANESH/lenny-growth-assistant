# 02 — Debugging: From "Looks Done" to "Actually Works"

Landing the pgvector/HNSW retrieval layer (see `01_initial_scaffolding.md`) was necessary but not
sufficient — several real bugs only surfaced once the system was actually run end-to-end against
live services, not just code-reviewed. This log covers the retrieval/provider debugging chain,
in the order the symptoms appeared.

## Bug 1: HNSW index and extension creation ordering

The initial pgvector migration created the `TranscriptChunk` table before confirming the `vector`
extension existed. `init_db()` was fixed to explicitly run `CREATE EXTENSION IF NOT EXISTS vector`
before `Base.metadata.create_all()`, and the HNSW index was defined with explicit
`postgresql_using="hnsw"`, `postgresql_with={"m": 16, "ef_construction": 64}` and
`postgresql_ops={"embedding": "vector_cosine_ops"}` on the `entities.py` model — the difference
between an index that silently fails to build and one that actually accelerates cosine search.

Verified by adding `/api/health` checks that query `pg_extension` and `pg_indexes` directly rather
than trusting that migrations ran cleanly — `pgvector: true/false` and `hnsw_index: true/false`
now report the real state, not an assumption.

## Bug 2: symptom vs. root cause — "Offline Test Simulator" was answering everything

A user report showed the chat consistently returning generic, keyword-templated answers (e.g. a
fixed Sean Ellis PMF quote regardless of the actual question) and ignoring "today's date" as a
query entirely. The tempting first read was "the LLM providers are broken." Root-causing instead
of patching the symptom:

1. Traced the exact response text back to `mock_provider.py::_synthesize_response` — a hardcoded,
   keyword-matched template. This proved the request was served by the mock provider, not a real
   model, and had nothing to do with provider health.
2. Checked the actual `.env` — `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`,
   `ANTHROPIC_API_KEY` were all present. Live `httpx` calls against each provider's real API
   confirmed the keys **authenticated successfully** (404s, not 401s) — so the keys were not the
   problem either.
3. The actual bug: both `groq_provider.py` and `gemini_provider.py` had hardcoded default model
   IDs (`llama-3.3-70b-versatile`, `gemini-1.5-flash`) that had since been retired/removed from
   the respective provider catalogs for this account. `GET /v1/models` against the real Groq key
   confirmed it had zero Llama models available at all. Fixed by querying each provider's actual
   model list and switching defaults to `openai/gpt-oss-20b` (Groq) and `gemini-flash-latest`
   (Gemini) — both verified with real `generate()` calls before committing.

## Bug 3: the real trigger — `.env` never loading from the documented run path

Even after fixing the model IDs, live runs still fell through to mock. `config.py` declared
`model_config = SettingsConfigDict(env_file=".env", ...)` — a **relative** path, resolved against
the process's current working directory. The documented (and correct) way to run the backend is
`cd backend && uvicorn app.main:app`, so pydantic-settings was looking for `backend/.env`, which
doesn't exist — the real `.env` lives at the project root next to `docker-compose.yml`. Every API
key silently resolved to `None` in the running server, every provider's `check_health()` correctly
reported itself unavailable, and the fallback chain correctly cascaded straight to mock — the code
was behaving exactly as written, the configuration was just pointed at nothing.

Fixed by anchoring `env_file` to the absolute `WORKSPACE_DIR / ".env"` path (already computed in
that file from its own location), independent of process cwd. Verified by temporarily copying the
real `.env` into an isolated git worktree and confirming all four keys resolved non-empty when run
from `backend/` — previously all `False`.

## Bug 4: `check_health()` checks presence, not validity

With `.env` finally loading, one more layer surfaced: `check_health()` on every cloud provider only
checks `if not self.api_key`, never whether the key actually works. The real `.env`'s
`ANTHROPIC_API_KEY` turned out to be expired — `check_health()` reported it "available," so
`stream_with_fallback()` picked it as the serving hop, and the raw string `"[Anthropic Error HTTP
401]"` streamed straight into the chat as if it were the model's answer, with no fallback to the
next provider in the chain.

Every provider's `stream_generate()` is deliberately designed to *yield* an error string rather
than raise an exception (so a partial response before a mid-stream failure isn't discarded) — but
that meant the manager's exception-based fallback logic never saw the failure. Fixed by peeking the
first chunk of each hop's stream against a small fixed set of known error markers
(`"Error HTTP"`, `"connection error:"`, etc.); if it matches, that hop is treated as failed and the
chain moves on, exactly as an exception would. Verified against the real invalid key: previously
a failing test (`test_llm_manager_stream_fallback`), now passing.

## Working principle established

Every fix in this chain was verified against the *actual* running system before being called
done — live API calls with real keys, a real `pytest` run with before/after pass counts, a real
`npm run build`, a real check that `git diff` against the donor folder stayed empty. "The code
looks correct" was never treated as equivalent to "the code works."
