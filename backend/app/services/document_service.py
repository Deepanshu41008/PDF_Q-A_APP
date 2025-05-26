"""
Document filesystem & vector-index utilities
===========================================

Responsibilities
----------------
* Persist uploaded PDF files (de-duplicated, atomic writes)
* Build / load FAISS vector indexes
* Remain framework-agnostic (no FastAPI / SQLAlchemy imports)

Safeguards
----------
* Handles empty / invalid filenames
* Works with both FastAPI ``UploadFile`` and generic ``BinaryIO``
* Recovers gracefully from interrupted writes / index failures
* Robust repository root detection
"""
from __future__ import annotations

import logging
import os
import pickle
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, IO, Optional, Union, overload

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader

if TYPE_CHECKING:  # pragma: no cover
    # Only imported for type-checking; avoids runtime dependency in non-API code
    from fastapi import UploadFile
else:  # pragma: no cover
    UploadFile = object  # type: ignore

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
# Ensure at least one handler exists when the app is run as a script
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# --------------------------------------------------------------------------- #
# Paths – resolved robustly regardless of project depth
# --------------------------------------------------------------------------- #
def _discover_repo_root(start: Path) -> Path:
    """Walk upwards until we find a marker (git / pyproject) or hit fs-root."""
    cur = start
    for _ in range(4):  # Up to 4 levels is plenty for most repos
        if (cur / ".git").exists() or (cur / "pyproject.toml").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.parent  # fallback: one level above current file


REPO_ROOT: Path = _discover_repo_root(Path(__file__).resolve())
DATA_DIR: Path = REPO_ROOT / "data"
UPLOAD_DIR: Path = DATA_DIR / "documents"
INDEX_DIR: Path = DATA_DIR / "indices"

for _d in (UPLOAD_DIR, INDEX_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _safe_unlink(path: Path) -> None:
    """Delete *path* while silencing most OS errors."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not delete %s: %s", path, exc)


def _is_pdf(name: str | Path) -> bool:
    return str(name).lower().endswith(".pdf")


def generate_unique_name(original: str) -> str:
    """
    Return a filename that will not collide inside ``UPLOAD_DIR``.
    Keeps the original extension (defaults to ``.pdf``).
    """
    stem = Path(original).stem
    ext = Path(original).suffix or ".pdf"
    candidate = UPLOAD_DIR / f"{stem}{ext}"
    if not candidate.exists():
        return candidate.name
    return f"{stem}-{uuid.uuid4().hex[:6]}{ext}"


# --------------------------------------------------------------------------- #
# File persistence
# --------------------------------------------------------------------------- #
@overload
def save_uploaded_file(
    upload_file: "UploadFile",
    original_filename: None | str = None,
    *,
    mime_check: bool = True,
) -> Path: ...  # noqa: D401


@overload
def save_uploaded_file(
    upload_file: BinaryIO,
    original_filename: str,
    *,
    mime_check: bool = True,
) -> Path: ...  # noqa: D401


def save_uploaded_file(
    upload_file: Union["UploadFile", BinaryIO],
    original_filename: Optional[str] = None,
    *,
    mime_check: bool = True,
) -> Path:
    """
    Atomically write *upload_file* to ``UPLOAD_DIR`` and return the final path.
    """
    # Derive original filename ------------------------------------------------
    if isinstance(upload_file, UploadFile):  # type: ignore[arg-type]
        original_filename = original_filename or upload_file.filename  # type: ignore[assignment]
    if not original_filename:
        raise ValueError("original_filename must be provided and non-empty")

    if mime_check and not _is_pdf(original_filename):
        raise OSError("Only PDF files are allowed")

    # Source handle -----------------------------------------------------------
    src: BinaryIO
    if isinstance(upload_file, UploadFile):  # type: ignore[arg-type]
        src = upload_file.file  # type: ignore[assignment]
    else:
        src = upload_file

    try:
        src.seek(0)
    except Exception:  # noqa: BLE001
        pass

    # Write atomically --------------------------------------------------------
    final_name = generate_unique_name(original_filename)
    tmp_path = UPLOAD_DIR / f".tmp-{uuid.uuid4().hex}"
    final_path = UPLOAD_DIR / final_name

    try:
        with open(tmp_path, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)  # 1 MiB buffer
        os.replace(tmp_path, final_path)
        logger.info("Saved PDF to %s", final_path)
        return final_path
    except Exception:  # noqa: BLE001
        _safe_unlink(tmp_path)
        raise

# --------------------------------------------------------------------------- #
# PDF helpers
# --------------------------------------------------------------------------- #
def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    """
    Extract plain text from a PDF; returns ``None`` on any failure or
    when the PDF contains zero extractable pages.
    """
    if not file_path.exists():
        logger.error("File not found: %s", file_path)
        return None

    try:
        pages = PyMuPDFLoader(str(file_path)).load()
        if not pages:
            logger.warning("No extractable pages in %s", file_path)
            return None
        return "\n".join(p.page_content for p in pages)
    except Exception as exc:  # noqa: BLE001
        logger.error("Text extraction failed: %s", exc, exc_info=True)
        return None

# --------------------------------------------------------------------------- #
# Vector-index helpers
# --------------------------------------------------------------------------- #
_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 200


def _dump_pickle(obj: object, path: Path) -> None:
    with open(path, "wb") as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)


def _load_pickle(path: Path) -> Any:
    with open(path, "rb") as fh:
        return pickle.load(fh)


def create_document_index(document_id: int | str, file_path: Path) -> bool:
    """
    Create a FAISS vector index for *file_path* and persist it under
    ``INDEX_DIR/<document_id>/vectorstore.pkl``.
    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        docs = PyMuPDFLoader(str(file_path)).load()
        if not docs:
            logger.warning("PDF had no pages: %s", file_path)
            return False

        chunks = RecursiveCharacterTextSplitter(
            chunk_size=_CHUNK_SIZE, chunk_overlap=_CHUNK_OVERLAP
        ).split_documents(docs)

        vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
        out_dir = INDEX_DIR / str(document_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        _dump_pickle(vs, out_dir / "vectorstore.pkl")
        logger.info("Vector index created for document %s", document_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Index creation failed for %s: %s", document_id, exc, exc_info=True)
        shutil.rmtree(INDEX_DIR / str(document_id), ignore_errors=True)
        return False


def get_document_index(document_id: int | str) -> Optional[FAISS]:
    """
    Load the FAISS index for *document_id* or ``None`` if not present / corrupt.
    """
    pkl = INDEX_DIR / str(document_id) / "vectorstore.pkl"
    if not pkl.exists():
        logger.warning("Index not found for document %s", document_id)
        return None
    try:
        index = _load_pickle(pkl)
        if not isinstance(index, FAISS):
            raise TypeError("Pickle did not contain a FAISS object")
        return index
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load index for %s: %s", document_id, exc, exc_info=True)
        return None
# --------------------------------------------------------------------------- #
# Public exports
# --------------------------------------------------------------------------- #
__all__ = [
    "UPLOAD_DIR",
    "INDEX_DIR",
    "generate_unique_name",
    "save_uploaded_file",
    "extract_text_from_pdf",
    "create_document_index",
    "get_document_index",
]
