import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.rag.vector_store import PersistentVectorStore
from app.llm.manager import llm_manager

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])

@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive system health diagnostic verifying Database,
    Vector Knowledge Base, and LLM Provider reachability.
    """
    start_time = time.time()
    
    # 1. Database Check
    db_ok = False
    db_message = ""
    is_postgres = db.bind.dialect.name == "postgresql" if db.bind is not None else False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
        db_message = "Connected and operational."
    except Exception as e:
        db_message = f"DB Connection Error: {str(e)}"

    # 1b. pgvector extension + HNSW index checks (reuse the same DB session/engine —
    # no live Postgres available, e.g. SQLite fallback, both report False cleanly).
    pgvector_ok = False
    hnsw_index_ok = False
    if db_ok and is_postgres:
        try:
            pgvector_ok = db.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first() is not None
            hnsw_index_ok = db.execute(
                text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_transcript_chunks_embedding_hnsw'")
            ).first() is not None
        except Exception as e:
            db_message = f"{db_message} (extension/index check failed: {str(e)})"

    # 2. Vector Store Check
    vector_store = PersistentVectorStore(storage_path=settings.STORAGE_PATH)
    chunks_count = vector_store.count()
    vector_ok = chunks_count > 0

    # 3. LLM Providers Status
    provider_statuses = await llm_manager.list_providers_status()

    total_latency = round((time.time() - start_time) * 1000, 2)
    overall_healthy = db_ok and vector_ok

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "latency_ms": total_latency,
        "database": {
            "is_connected": db_ok,
            "message": db_message
        },
        "knowledge_base": {
            "is_loaded": vector_ok,
            "indexed_chunks": chunks_count,
            "storage_path": str(settings.STORAGE_PATH)
        },
        "llm_providers": [p.model_dump() for p in provider_statuses],
        "postgres": ("connected" if (db_ok and is_postgres) else ("disconnected" if db_ok else db_message)),
        "pgvector": pgvector_ok,
        "hnsw_index": hnsw_index_ok,
        "embedding_provider": "local",
        "llm_primary": settings.LLM_PROVIDER or settings.DEFAULT_LLM_PROVIDER,
        "fallbacks": [p.strip() for p in settings.LLM_FALLBACK_ORDER.split(",") if p.strip()]
    }
