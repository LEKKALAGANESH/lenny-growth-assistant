from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.entities import SessionModel, MessageModel, ArtifactModel, AuditLogModel
from app.schemas.session import SessionCreate, SessionSummary

class ChatRepository:
    """Repository handling all database CRUD operations for conversations, artifacts, and audits."""

    @staticmethod
    def create_session(
        db: Session,
        title: Optional[str] = "New Chat",
        llm_provider: Optional[str] = "ollama",
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionModel:
        session = SessionModel(
            title=title or "New Chat",
            llm_provider=llm_provider or "ollama",
            metadata_json=metadata or {}
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        return db.scalar(stmt)

    @staticmethod
    def list_sessions(db: Session, limit: int = 50, offset: int = 0) -> List[SessionSummary]:
        stmt = (
            select(SessionModel)
            .order_by(desc(SessionModel.updated_at))
            .offset(offset)
            .limit(limit)
        )
        sessions = db.scalars(stmt).all()
        summaries = []
        for s in sessions:
            summaries.append(
                SessionSummary(
                    id=s.id,
                    title=s.title,
                    llm_provider=s.llm_provider,
                    message_count=len(s.messages),
                    artifact_count=len(s.artifacts),
                    created_at=s.created_at,
                    updated_at=s.updated_at
                )
            )
        return summaries

    @staticmethod
    def update_session(
        db: Session,
        session_id: str,
        title: Optional[str] = None,
        llm_provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[SessionModel]:
        session = ChatRepository.get_session(db, session_id)
        if not session:
            return None

        if title is not None:
            session.title = title
        if llm_provider is not None:
            session.llm_provider = llm_provider
        if metadata is not None:
            session.metadata_json = metadata

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        session = ChatRepository.get_session(db, session_id)
        if not session:
            return False

        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def add_message(
        db: Session,
        session_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[MessageModel]:
        session = ChatRepository.get_session(db, session_id)
        if not session:
            return None

        # Auto-update session title from first user message if still default
        if role == "user" and session.title == "New Chat":
            clean_title = content.strip().split("\n")[0][:40]
            if len(content.strip().split("\n")[0]) > 40:
                clean_title += "..."
            session.title = clean_title

        message = MessageModel(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations or []
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        db.refresh(session)
        return message

    @staticmethod
    def get_session_messages(db: Session, session_id: str) -> List[MessageModel]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_artifact(
        db: Session,
        session_id: str,
        title: str,
        type: str,
        content: str,
        message_id: Optional[str] = None
    ) -> Optional[ArtifactModel]:
        session = ChatRepository.get_session(db, session_id)
        if not session:
            return None

        # Determine version count for same title in session
        existing_count = sum(1 for a in session.artifacts if a.title.lower() == title.lower())

        artifact = ArtifactModel(
            session_id=session_id,
            message_id=message_id,
            title=title,
            type=type,
            content=content,
            version=existing_count + 1
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact

    @staticmethod
    def get_session_artifacts(db: Session, session_id: str) -> List[ArtifactModel]:
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.session_id == session_id)
            .order_by(ArtifactModel.created_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_artifact(db: Session, artifact_id: str) -> Optional[ArtifactModel]:
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        return db.scalar(stmt)

    @staticmethod
    def log_audit(
        db: Session,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0
    ) -> AuditLogModel:
        log = AuditLogModel(
            event_type=event_type,
            payload=payload or {},
            latency_ms=latency_ms
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
