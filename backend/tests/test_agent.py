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
from app.agent.parser import AgentStreamParser
from app.agent.orchestrator import GrowthAgentOrchestrator

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_stream_parser_artifact_extraction():
    raw_output = (
        "Here is the growth framework you requested:\n\n"
        '<<<ARTIFACT title="B2B PLG Funnel Calculator" type="html">>>\n'
        '<div class="calculator"><h1>CAC to LTV</h1></div>\n'
        '<<<END_ARTIFACT>>>\n\n'
        "Let me know if you want to tweak the conversion parameters."
    )

    citations = [{"badge": "[EP-118 • Elena Verna @ 00:00:36]"}]
    parsed = AgentStreamParser.parse_response(raw_output, citations=citations)

    assert len(parsed.artifacts) == 1
    art = parsed.artifacts[0]
    assert art.title == "B2B PLG Funnel Calculator"
    assert art.type == "html"
    assert "<h1>CAC to LTV</h1>" in art.content
    assert "[Generated Artifact: **B2B PLG Funnel Calculator**" in parsed.display_text
    assert len(parsed.citations) == 1

def test_stream_parser_markdown_artifact():
    raw_output = (
        "Here is the PRD Template based on Shreyas Doshi's advice:\n\n"
        '<<<ARTIFACT title="Product Pre-Mortem Template" type="markdown">>>\n'
        '# Pre-Mortem Protocol\n- Risk 1: Distribution\n- Risk 2: Latency\n'
        '<<<END_ARTIFACT>>>\n'
    )
    parsed = AgentStreamParser.parse_response(raw_output)
    assert len(parsed.artifacts) == 1
    assert parsed.artifacts[0].title == "Product Pre-Mortem Template"
    assert parsed.artifacts[0].type == "markdown"
    assert "# Pre-Mortem Protocol" in parsed.artifacts[0].content

def test_classify_intent():
    orchestrator = GrowthAgentOrchestrator()

    assert orchestrator.classify_intent("Write a Ship 30 for 30 essay on founder mode") == "ship30_essay"
    assert orchestrator.classify_intent("Create an interactive HTML calculator for CAC") == "artifact"
    assert orchestrator.classify_intent("How does Brian Chesky run Airbnb?") == "grounded_qa"

@pytest.mark.anyio
async def test_agent_orchestrator_turn_execution(db_session):
    orchestrator = GrowthAgentOrchestrator()
    session = ChatRepository.create_session(db_session, title="Agent Test", llm_provider="mock")

    parsed, llm_resp = await orchestrator.execute_turn(
        db=db_session,
        session_id=session.id,
        user_message="What did Brian Chesky say about Founder Mode?",
        llm_provider="mock"
    )

    assert parsed.display_text is not None
    assert "Brian Chesky" in parsed.display_text
    assert len(parsed.citations) > 0
    assert parsed.citations[0]["episode_id"] == "ep-142"

    # Verify automatic DB persistence
    messages = ChatRepository.get_session_messages(db_session, session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert len(messages[1].citations) > 0

@pytest.mark.anyio
async def test_agent_orchestrator_streaming_turn(db_session):
    orchestrator = GrowthAgentOrchestrator()
    session = ChatRepository.create_session(db_session, title="Stream Test", llm_provider="mock")

    chunks = []
    async for chunk in orchestrator.stream_turn(
        db=db_session,
        session_id=session.id,
        user_message="Explain the LNO Framework by Shreyas Doshi",
        llm_provider="mock"
    ):
        chunks.append(chunk)

    full_output = "".join(chunks)
    assert len(chunks) > 0
    assert "Shreyas Doshi" in full_output or "LNO" in full_output

    # Verify messages saved after streaming completes
    messages = ChatRepository.get_session_messages(db_session, session.id)
    assert len(messages) == 2
    assert messages[1].role == "assistant"
