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

import importlib
import logging
import os
from pathlib import Path
from typing import Generator, List

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "pdf_qa.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# For SQLite we need `check_same_thread=False`
_is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _is_sqlite else None,
)

# --------------------------------------------------------------------------- #
# Declarative base & session factory
# --------------------------------------------------------------------------- #
class Base(DeclarativeBase):  # type: ignore[override]
    """Base class for all ORM models."""
    pass


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
# Model discovery & table creation
# --------------------------------------------------------------------------- #
# Add new model modules here so `init_db()` creates their tables automatically.
__all_models__: List[str] = [
    "app.models.document",
]


def init_db() -> None:
    """
    Import all models listed in `__all_models__` and create their tables.
    Call this once on application startup.
    """
    for module_path in __all_models__:
        importlib.import_module(module_path)
        logger.debug("Imported model module %s", module_path)

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialised (url=%s)", DATABASE_URL)


__all__ = [
    "Base",
    "SessionLocal",
    "get_db",
    "init_db",
]
