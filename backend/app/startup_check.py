"""
Container-start verification: wait for Postgres, confirm pgvector + the HNSW
index exist, then run init_db()/ingestion. Runs before uvicorn starts serving
(see backend/Dockerfile CMD) — no separate wait-for-it dependency needed, a
small retry loop against the DB is enough.
"""
import sys
import time
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_database_engine, init_db


def wait_for_postgres(max_attempts: int = 30, delay_seconds: float = 2.0) -> bool:
    """Poll until the DB accepts connections, or give up after max_attempts."""
    if not settings.DATABASE_URL.startswith("postgresql"):
        print("[startup] DATABASE_URL is not Postgres — skipping wait-for-db.")
        return True

    for attempt in range(1, max_attempts + 1):
        try:
            engine = get_database_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[startup] Postgres is accepting connections (attempt {attempt}).")
            return True
        except Exception as e:
            print(f"[startup] Postgres not ready yet (attempt {attempt}/{max_attempts}): {e}")
            time.sleep(delay_seconds)
    print("[startup] Postgres did not become ready in time — continuing with fallback engine.")
    return False


def verify_pgvector_and_hnsw(engine) -> None:
    """Best-effort diagnostic checks — never blocks startup, just logs."""
    if engine.dialect.name != "postgresql":
        print("[startup] Non-Postgres engine — skipping pgvector/HNSW checks.")
        return
    try:
        with engine.connect() as conn:
            has_vector = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first() is not None
            has_hnsw = conn.execute(
                text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_transcript_chunks_embedding_hnsw'")
            ).first() is not None
            print(f"[startup] pgvector extension present: {has_vector}")
            print(f"[startup] HNSW index present: {has_hnsw}")
    except Exception as e:
        print(f"[startup] pgvector/HNSW check failed (non-fatal): {e}")


def run_startup_checks() -> None:
    wait_for_postgres()
    from app.db.session import engine
    init_db(bind_engine=engine)
    verify_pgvector_and_hnsw(engine)


if __name__ == "__main__":
    run_startup_checks()
    sys.exit(0)
