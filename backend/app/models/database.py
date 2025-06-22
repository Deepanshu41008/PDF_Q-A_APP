"""
Database bootstrap for the PDF-QA backend.

Public API
----------
SessionLocal  – `sessionmaker` bound to the engine
Base          – declarative base class for ORM models
get_db()      – FastAPI dependency providing a scoped session
init_db()     – create tables for all registered models
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

from app.core.config import DATABASE_URL # Import DATABASE_URL

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
# DATABASE_URL is now imported from app.core.config

# Create engine with appropriate connection arguments
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# --------------------------------------------------------------------------- #
# Declarative base & session factory
# --------------------------------------------------------------------------- #
Base = declarative_base()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

# --------------------------------------------------------------------------- #
# FastAPI dependency
# --------------------------------------------------------------------------- #
def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session to FastAPI endpoints / services.

    Usage in route:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------------------------------- #
# Database initialization
# --------------------------------------------------------------------------- #
def init_db() -> None:
    """
    Initialize database tables for all models.
    Call this once on application startup.
    """
    try:
        # Import all models to ensure they're registered with Base
        from app.models.document import Document

        # Ensure the parent directory for the SQLite database exists
        if DATABASE_URL.startswith("sqlite"):
            # Correctly parse the SQLite file path
            # Example: "sqlite:///./data/pdf_qa.db" -> "./data/pdf_qa.db"
            # Example: "sqlite:///C:/path/to/db.file" -> "C:/path/to/db.file"
            db_file_path_str = DATABASE_URL.split("///", 1)[-1]
            db_file = Path(db_file_path_str)

            # Create parent directories if they don't exist
            db_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured database directory exists: {db_file.parent}")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized (url=%s)", DATABASE_URL)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

__all__ = [
    "Base",
    "SessionLocal",
    "get_db",
    "init_db",
]
