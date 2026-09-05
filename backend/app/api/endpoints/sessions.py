from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repository import ChatRepository
from app.schemas.session import (
    SessionCreate, SessionSummary, SessionResponse,
    ArtifactResponse
)

router = APIRouter(prefix="/sessions", tags=["Session Management"])

@router.get("", response_model=List[SessionSummary])
def list_sessions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Lists all user sessions with summary stats and timestamps."""
    return ChatRepository.list_sessions(db, limit=limit, offset=offset)

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    """Creates a new conversation session with independent context."""
    session = ChatRepository.create_session(
        db=db,
        title=payload.title,
        llm_provider=payload.llm_provider,
        metadata=payload.metadata_json
    )
    return session

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieves full conversation history and artifacts for a session."""
    session = ChatRepository.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    title: Optional[str] = None,
    llm_provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Updates session title or active LLM provider selection."""
    session = ChatRepository.update_session(db, session_id, title=title, llm_provider=llm_provider)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Deletes a session and cascades deletion to messages and artifacts."""
    deleted = ChatRepository.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return None

@router.get("/{session_id}/artifacts", response_model=List[ArtifactResponse])
def get_session_artifacts(session_id: str, db: Session = Depends(get_db)):
    """Lists all artifacts generated in the session."""
    return ChatRepository.get_session_artifacts(db, session_id)

@router.get("/{session_id}/artifacts/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(session_id: str, artifact_id: str, db: Session = Depends(get_db)):
    """Retrieves a specific artifact by ID."""
    artifact = ChatRepository.get_artifact(db, artifact_id)
    if not artifact or artifact.session_id != session_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact
