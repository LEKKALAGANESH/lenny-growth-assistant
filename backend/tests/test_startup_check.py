import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.db.session import engine
from app.startup_check import wait_for_postgres, verify_pgvector_and_hnsw

requires_postgres = pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="No live Postgres/pgvector instance configured (DATABASE_URL fell back to SQLite) — "
           "run `docker compose up postgres` and point DATABASE_URL at it to exercise this test."
)


def test_wait_for_postgres_skips_immediately_on_non_postgres_url(monkeypatch):
    """Unit-tests the retry/polling function in isolation (no real Docker/DB): when
    DATABASE_URL isn't a Postgres URL, it returns True on the first check with no
    sleeping/retrying."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:///:memory:")
    assert wait_for_postgres(max_attempts=3, delay_seconds=0) is True


def test_wait_for_postgres_retries_then_gives_up(monkeypatch):
    """Simulates an always-unreachable Postgres and asserts the loop gives up after
    max_attempts rather than hanging forever."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://bad:bad@localhost:1/doesnotexist")

    import app.startup_check as sc

    def broken_engine():
        raise ConnectionError("simulated: postgres unreachable")

    monkeypatch.setattr(sc, "get_database_engine", broken_engine)
    assert wait_for_postgres(max_attempts=2, delay_seconds=0) is False


@requires_postgres
def test_verify_pgvector_and_hnsw_finds_extension_and_index():
    """Extends the Postgres-only test pattern from the prior patch: only runs when
    DATABASE_URL actually resolved to a live Postgres engine (see requires_postgres)."""
    from app.db.session import init_db
    init_db()
    # Should not raise; prints diagnostics either way. We can't assert True/False
    # generically here since it depends on whether ingestion already ran, but the
    # extension itself must exist once init_db() has run against Postgres.
    verify_pgvector_and_hnsw(engine)
    with engine.connect() as conn:
        from sqlalchemy import text
        has_vector = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).first() is not None
    assert has_vector is True
