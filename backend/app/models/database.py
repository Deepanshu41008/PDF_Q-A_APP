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
import os
from pathlib import Path
from typing import Generator

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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///C:/Users/gupta/pdf/PDF_Q-A_APP/backend/data/pdf_qa.db")

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
