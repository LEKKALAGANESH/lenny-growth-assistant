from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Message Schemas ---
class MessageBase(BaseModel):
    role: str
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    created_at: datetime

# --- Artifact Schemas ---
class ArtifactBase(BaseModel):
    title: str
    type: str = "markdown"  # markdown, html, code
    content: str

class ArtifactCreate(ArtifactBase):
    message_id: Optional[str] = None

class ArtifactResponse(ArtifactBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    message_id: Optional[str] = None
    version: int = 1
    created_at: datetime

# --- Session Schemas ---
class SessionBase(BaseModel):
    title: Optional[str] = "New Chat"
    llm_provider: Optional[str] = "ollama"
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessionCreate(SessionBase):
    pass

class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    llm_provider: str
    message_count: int
    artifact_count: int
    created_at: datetime
    updated_at: datetime

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    llm_provider: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    messages: List[MessageResponse] = Field(default_factory=list)
    artifacts: List[ArtifactResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

# --- Audit Log Schemas ---
class AuditLogCreate(BaseModel):
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    payload: Dict[str, Any]
    latency_ms: float
    created_at: datetime
