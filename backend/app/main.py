from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Iterable, List

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, questions
from app.core.config import (
    INDEX_DIR,
    UPLOAD_DIR,
    _env,
)
from app.models.database import init_db

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _parse_origins(raw: str | Iterable[str] | None) -> List[str]:
    """
    Parse the CORS_ORIGINS env-var (comma-separated) or pass-through iterables.
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        return [o.strip() for o in raw.split(",") if o.strip()]
    return list(raw)


# --------------------------------------------------------------------------- #
# Lifespan – run once on startup / shutdown
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup -------------------------------------------------------------- #
    logger.info("Starting PDF-QA API …")

    # 1. ensure DB schema / migrations are in place
    init_db()
    logger.info("Database initialised")

    # 2. double-check data directories exist (config already attempts this)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug("Verified data directories at %s and %s", UPLOAD_DIR, INDEX_DIR)

    yield

    # Shutdown ------------------------------------------------------------- #
    logger.info("API shutdown complete")


# --------------------------------------------------------------------------- #
# Application factory
# --------------------------------------------------------------------------- #
def create_app() -> FastAPI:
    app = FastAPI(
        title="PDF QA API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    allowed_origins = _parse_origins(
        _env("CORS_ORIGINS", "http://localhost:12001,http://localhost:3000")
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],  # fallback to permissive
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("CORS configured for %s", allowed_origins or "*")

    # ------------------------------------------------------------------ #
    # Routers
    # ------------------------------------------------------------------ #
    app.include_router(documents.router, prefix="/api", tags=["documents"])
    app.include_router(questions.router, prefix="/api", tags=["questions"])

    # ------------------------------------------------------------------ #
    # Root & health-check endpoints
    # ------------------------------------------------------------------ #
    @app.get("/", summary="Health check / welcome")
    async def root():
        return {"message": "Welcome to PDF QA API", "status": "ok"}

    # ------------------------------------------------------------------ #
    # Generic exception handler
    # ------------------------------------------------------------------ #
    @app.exception_handler(Exception)  # noqa: BLE001
    async def _unhandled_exception_handler(_: Request, exc: Exception):
        # Log full traceback, but return generic error to client
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    # Validation errors should still return 422 with details
    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    return app


# Instantiate application for ASGI servers (uvicorn / gunicorn)
app = create_app()
