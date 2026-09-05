import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.entities import Base

def get_database_engine():
    db_url = settings.DATABASE_URL
    
    # If standard postgres URL, try connecting; otherwise fallback cleanly to sqlite for standalone local dev/tests
    if db_url.startswith("postgresql"):
        try:
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            # Test connection
            with engine.connect():
                pass
            return engine
        except Exception:
            # Fallback to local SQLite database in storage directory
            sqlite_path = settings.STORAGE_PATH / "app_fallback.db"
            return create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    else:
        return create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})

engine = get_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(bind_engine=None) -> None:
    """Initializes all database tables."""
    target_engine = bind_engine or engine
    Base.metadata.create_all(bind=target_engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
