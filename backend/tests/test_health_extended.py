import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield


@pytest.mark.anyio
async def test_health_endpoint_new_fields_present_and_typed():
    """Extends the existing /api/health contract (does not remove any prior field)
    with Postgres/pgvector/HNSW/LLM-chain diagnostics. Runs fine even when Postgres
    is unavailable — the fields just report the degraded state instead of erroring."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()

    assert "postgres" in data and isinstance(data["postgres"], str)
    assert isinstance(data["pgvector"], bool)
    assert isinstance(data["hnsw_index"], bool)
    assert isinstance(data["embedding_provider"], str)
    assert isinstance(data["llm_primary"], str)
    assert isinstance(data["fallbacks"], list)
    assert data["fallbacks"] == ["groq", "gemini"]

    # Prior fields untouched
    assert "status" in data
    assert "database" in data
    assert "knowledge_base" in data
    assert "llm_providers" in data
