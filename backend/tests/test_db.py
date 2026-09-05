import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.entities import Base
from app.db.repository import ChatRepository

@pytest.fixture
def db_session():
    # In-memory SQLite database for isolated unit testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_session_lifecycle(db_session):
    # 1. Create session
    session = ChatRepository.create_session(
        db_session,
        title="Test Growth Chat",
        llm_provider="ollama",
        metadata={"user_role": "PM"}
    )
    assert session.id is not None
    assert session.title == "Test Growth Chat"
    assert session.llm_provider == "ollama"

    # 2. Get session
    fetched = ChatRepository.get_session(db_session, session.id)
    assert fetched is not None
    assert fetched.id == session.id

    # 3. List sessions
    summaries = ChatRepository.list_sessions(db_session)
    assert len(summaries) == 1
    assert summaries[0].id == session.id

    # 4. Update session
    updated = ChatRepository.update_session(
        db_session,
        session.id,
        title="Updated Title",
        llm_provider="anthropic"
    )
    assert updated.title == "Updated Title"
    assert updated.llm_provider == "anthropic"

    # 5. Delete session
    deleted = ChatRepository.delete_session(db_session, session.id)
    assert deleted is True
    assert ChatRepository.get_session(db_session, session.id) is None

def test_message_history_and_citations(db_session):
    session = ChatRepository.create_session(db_session)
    
    citations = [
        {
            "badge": "[EP-142 • Brian Chesky @ 00:02:11]",
            "episode_id": "ep-142",
            "quote": "Founder mode means you do not run the company through disconnected business units."
        }
    ]

    msg1 = ChatRepository.add_message(db_session, session.id, "user", "What is Founder Mode?")
    assert msg1.role == "user"
    assert session.title == "What is Founder Mode?"  # Auto-title update

    msg2 = ChatRepository.add_message(db_session, session.id, "assistant", "Founder Mode is being in the details.", citations=citations)
    assert msg2.role == "assistant"
    assert len(msg2.citations) == 1
    assert msg2.citations[0]["episode_id"] == "ep-142"

    messages = ChatRepository.get_session_messages(db_session, session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"

def test_artifact_versioning(db_session):
    session = ChatRepository.create_session(db_session)

    art1 = ChatRepository.create_artifact(
        db_session,
        session_id=session.id,
        title="Growth Framework",
        type="markdown",
        content="# Growth Loop Strategy v1"
    )
    assert art1.version == 1

    art2 = ChatRepository.create_artifact(
        db_session,
        session_id=session.id,
        title="Growth Framework",
        type="markdown",
        content="# Growth Loop Strategy v2"
    )
    assert art2.version == 2

    artifacts = ChatRepository.get_session_artifacts(db_session, session.id)
    assert len(artifacts) == 2

def test_session_isolation(db_session):
    session_a = ChatRepository.create_session(db_session, title="Session A")
    session_b = ChatRepository.create_session(db_session, title="Session B")

    ChatRepository.add_message(db_session, session_a.id, "user", "Hello from A")
    ChatRepository.add_message(db_session, session_b.id, "user", "Hello from B")

    messages_a = ChatRepository.get_session_messages(db_session, session_a.id)
    messages_b = ChatRepository.get_session_messages(db_session, session_b.id)

    assert len(messages_a) == 1
    assert messages_a[0].content == "Hello from A"

    assert len(messages_b) == 1
    assert messages_b[0].content == "Hello from B"

def test_session_cascade_delete(db_session):
    session = ChatRepository.create_session(db_session)
    ChatRepository.add_message(db_session, session.id, "user", "Message to be deleted")
    ChatRepository.create_artifact(db_session, session.id, "Artifact", "markdown", "# Temp")

    # Verify existing
    assert len(ChatRepository.get_session_messages(db_session, session.id)) == 1
    assert len(ChatRepository.get_session_artifacts(db_session, session.id)) == 1

    # Delete session
    ChatRepository.delete_session(db_session, session.id)

    # Verify cascaded deletion
    assert len(ChatRepository.get_session_messages(db_session, session.id)) == 0
    assert len(ChatRepository.get_session_artifacts(db_session, session.id)) == 0

def test_audit_logging(db_session):
    log = ChatRepository.log_audit(
        db_session,
        event_type="query_executed",
        payload={"query": "Founder mode", "provider": "ollama"},
        latency_ms=145.2
    )
    assert log.id is not None
    assert log.event_type == "query_executed"
    assert log.latency_ms == 145.2
