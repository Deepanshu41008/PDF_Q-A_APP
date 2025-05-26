from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from starlette import status

from app.models.database import get_db
from app.models.document import Document
from app.services.document_service import (
    INDEX_DIR,
    create_document_index,
    save_uploaded_file,
)

# Constants for file validation
ALLOWED_EXTENSIONS = {".pdf"}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

logger = logging.getLogger(__name__)

router = APIRouter()  # Removed prefix


# --------------------------------------------------------------------------- #
# Pydantic response models — useful for automatic docs
# --------------------------------------------------------------------------- #
class DocumentOut(BaseModel):
    id: int
    filename: str
    title: str
    uploadDate: datetime = Field(..., alias="upload_date")
    indexPath: Optional[str] | None = Field(None, alias="index_path")
    fileSize: Optional[int] = Field(None, alias="file_size")
    pageCount: Optional[int] = Field(None, alias="page_count")
    isIndexed: bool = Field(False, alias="is_indexed")

    @validator("upload_date", pre=True, always=True)
    def _serialize_dt(cls, dt: datetime):  # noqa: D401, N805
        return dt.isoformat()
    
    @validator("is_indexed", pre=True, always=True)
    def _check_indexed(cls, _, values):  # noqa: D401, N805
        return values.get("index_path") is not None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _cleanup_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not delete file %s during rollback: %s", path, exc)


def _cleanup_index(document_id: int | str) -> None:
    index_path = INDEX_DIR / str(document_id)
    if index_path.exists():
        try:
            shutil.rmtree(index_path, ignore_errors=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not delete index dir %s during rollback: %s", index_path, exc
            )


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Accept a PDF, persist it, create a DB row, and schedule FAISS indexing in a
    background task. The response is returned immediately; indexing may finish
    a few seconds later.
    """
    # ------------------------------ Validation --------------------------- #
    if not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required"
        )
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB"
        )

    # ------------------------------ Save file --------------------------- #
    file_path: Path
    try:
        file_path = save_uploaded_file(file, file.filename)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save upload: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        ) from exc

    # ------------------------------ DB insert --------------------------- #
    try:
        db_document = Document(
            filename=file_path.name,
            file_path=str(file_path),
            title=title or file_path.name,
            file_size=file_size,
        )
        db.add(db_document)
        db.flush()  # allocate primary-key

        # Persist index path (depends on PK)
        db_document.index_path = str(INDEX_DIR / str(db_document.id))
        db.commit()
        db.refresh(db_document)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        _cleanup_file(file_path)
        logger.error("DB insert failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database insert failed",
        ) from exc

    # -------------------------- Background indexing --------------------- #
    def _index_wrapper(doc_id: int, path: Path) -> None:
        if not create_document_index(doc_id, path):
            # Best-effort: delete DB row + file + index dir
            logger.error("Index creation failed for document %s", doc_id)
            with db.begin():
                orphan = db.get(Document, doc_id)
                if orphan is not None:
                    db.delete(orphan)
            _cleanup_file(path)
            _cleanup_index(doc_id)

    background.add_task(_index_wrapper, db_document.id, file_path)

    return db_document

@router.get("/", response_model=list[DocumentOut])
async def list_documents(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get all documents with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of document objects
    """
    docs = db.execute(
        select(Document)
        .order_by(Document.upload_date.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()
    return docs


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get a specific document by ID.
    
    Args:
        document_id: The ID of the document to retrieve
        db: Database session
    
    Returns:
        Document object
    
    Raises:
        HTTPException: If document not found
    """
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Remove the PDF, its FAISS index directory, and the DB record.
    
    Args:
        document_id: The ID of the document to delete
        db: Database session
    
    Raises:
        HTTPException: If document not found
    """
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Best-effort file deletion
    _cleanup_file(Path(doc.file_path))
    _cleanup_index(document_id)

    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted successfully"}
