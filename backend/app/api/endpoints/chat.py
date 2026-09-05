import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.agent.orchestrator import agent_orchestrator

router = APIRouter(prefix="/chat", tags=["Conversational Chat & Streaming"])

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    llm_provider: Optional[str] = None  # "ollama", "anthropic", "openai", "mock"
    skill: Optional[str] = None         # "grounded_qa", "ship30_essay", "artifact"

class ChatResponse(BaseModel):
    session_id: str
    message: str
    provider: str
    model: str
    citations: list
    artifacts: list
    latency_ms: float
    is_fallback: bool = False
    fallback_reason: Optional[str] = None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Synchronous chat turn execution with hybrid RAG retrieval,
    automatic skill routing, citation generation, and artifact extraction.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = payload.session_id or "new"
    parsed, llm_resp = await agent_orchestrator.execute_turn(
        db=db,
        session_id=session_id,
        user_message=payload.message,
        llm_provider=payload.llm_provider,
        skill_override=payload.skill
    )

    return ChatResponse(
        session_id=session_id,
        message=parsed.display_text,
        provider=llm_resp.provider,
        model=llm_resp.model,
        citations=parsed.citations,
        artifacts=[a.model_dump() for a in parsed.artifacts],
        latency_ms=llm_resp.latency_ms,
        is_fallback=llm_resp.is_fallback,
        fallback_reason=llm_resp.fallback_reason
    )

@router.post("/stream")
async def chat_stream_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Server-Sent Events (SSE) streaming endpoint delivering token-by-token
    stream to the UI, completing with a structured JSON completion event.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = payload.session_id or "new"

    async def event_generator():
        # SSE Event Stream
        async for chunk in agent_orchestrator.stream_turn(
            db=db,
            session_id=session_id,
            user_message=payload.message,
            llm_provider=payload.llm_provider,
            skill_override=payload.skill
        ):
            event_payload = json.dumps({"token": chunk})
            yield f"data: {event_payload}\n\n"

        # Emit completion event
        yield f"event: complete\ndata: {json.dumps({'status': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
