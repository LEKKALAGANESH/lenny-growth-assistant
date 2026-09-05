import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import json
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield

@pytest.mark.anyio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert "The Lenny Growth Assistant" in data["project"]

@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["database"]["is_connected"] is True
    assert data["knowledge_base"]["indexed_chunks"] > 0
    assert len(data["llm_providers"]) >= 3

@pytest.mark.anyio
async def test_models_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "default_provider" in data
    assert len(data["supported_providers"]) == 3

@pytest.mark.anyio
async def test_session_crud_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Session
        create_resp = await ac.post("/api/sessions", json={"title": "Test Session", "llm_provider": "mock"})
        assert create_resp.status_code == 201
        session_data = create_resp.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Test Session"

        # 2. Get Session
        get_resp = await ac.get(f"/api/sessions/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == session_id

        # 3. List Sessions
        list_resp = await ac.get("/api/sessions")
        assert list_resp.status_code == 200
        assert any(s["id"] == session_id for s in list_resp.json())

        # 4. Patch Session
        patch_resp = await ac.patch(f"/api/sessions/{session_id}?title=Renamed+Session")
        assert patch_resp.status_code == 200
        assert patch_resp.json()["title"] == "Renamed Session"

        # 5. Delete Session
        del_resp = await ac.delete(f"/api/sessions/{session_id}")
        assert del_resp.status_code == 204

        # 6. Verify Gone
        not_found_resp = await ac.get(f"/api/sessions/{session_id}")
        assert not_found_resp.status_code == 404

@pytest.mark.anyio
async def test_chat_endpoint_turn():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create session
        s_resp = await ac.post("/api/sessions", json={"title": "Chat API Test", "llm_provider": "mock"})
        session_id = s_resp.json()["id"]

        # Post chat
        chat_resp = await ac.post("/api/chat", json={
            "session_id": session_id,
            "message": "What did Brian Chesky say about Founder Mode?",
            "llm_provider": "mock"
        })
        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert data["session_id"] == session_id
        assert "Brian Chesky" in data["message"]
        assert len(data["citations"]) > 0

@pytest.mark.anyio
async def test_chat_stream_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_resp = await ac.post("/api/sessions", json={"title": "Stream API Test", "llm_provider": "mock"})
        session_id = s_resp.json()["id"]

        resp = await ac.post("/api/chat/stream", json={
            "session_id": session_id,
            "message": "Explain Elena Verna's definition of Product-Led Growth",
            "llm_provider": "mock"
        })
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "data:" in resp.text
        assert "event: complete" in resp.text
