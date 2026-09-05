from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend and workspace
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
INDEX_STORAGE_DIR = DATA_DIR / "storage"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "The Lenny Growth Assistant"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    
    # Storage Paths
    TRANSCRIPTS_PATH: Path = TRANSCRIPTS_DIR
    STORAGE_PATH: Path = INDEX_STORAGE_DIR
    
    # RAG Settings
    CHUNK_SIZE_TOKENS: int = 450
    CHUNK_OVERLAP_TOKENS: int = 100
    TOP_K_RETRIEVAL: int = 5
    DENSE_WEIGHT: float = 0.6
    SPARSE_WEIGHT: float = 0.4
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "ollama"  # "ollama", "anthropic", "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # Cloud API Keys (optional for local demo)
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/lenny_assistant"

settings = Settings()

# Ensure storage directories exist
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
