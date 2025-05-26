from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import anyio
import anyio.to_thread
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.document import Document
from app.services.qa_service import answer_question

logger = logging.getLogger(__name__)

router = APIRouter()

# --------------------------------------------------------------------------- #
# Pydantic models
# --------------------------------------------------------------------------- #
class QuestionRequest(BaseModel):
    """
    Incoming payload for a question on a particular document.
    """
    question: str = Field(..., min_length=5, description="User question in plain text")


class SourceNode(BaseModel):
    """
    Minimal representation of a source chunk returned by the retriever/QA chain.
    """
    text: str
    score: Optional[float] = Field(
        None,
        description="Similarity/relevance score if available (None otherwise)",
    )


class QuestionResponse(BaseModel):
    """
    Outgoing payload containing the answer and optional source nodes.
    """
    document_id: int
    question: str
    answer: str
    source_nodes: List[SourceNode] = Field(default_factory=list)

# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@router.post(
    "/documents/{document_id}/ask",
    response_model=QuestionResponse,
    summary="Ask a question about a specific PDF",
)
async def ask_question(
    document_id: int,
    question_request: QuestionRequest,
    db: Session = Depends(get_db),
) -> QuestionResponse:
    """
    Answer `question_request.question` using the vector index linked to
    `document_id`. Raises ``404`` if the document does not exist and ``500`` if
    the LLM / retrieval step fails for any reason.
    """
    # --------------------------------------------------------------------- #
    # 1. Ensure document exists
    # --------------------------------------------------------------------- #
    document: Document | None = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # --------------------------------------------------------------------- #
    # 2. Run the heavy LangChain chain in a worker-thread
    # --------------------------------------------------------------------- #
    try:
        # AnyIO ≥ 4 uses to_thread.run_sync for off-loading blocking work
        result: Dict[str, Any] = await anyio.to_thread.run_sync(
            answer_question,
            document_id,
            question_request.question,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("QA chain crashed for doc_id=%s: %s", document_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Question-answering failed") from exc

    # --------------------------------------------------------------------- #
    # 3. Validate result and produce response
    # --------------------------------------------------------------------- #
    if "error" in result:
        logger.error("qa_service returned error for doc_id=%s: %s", document_id, result["error"])
        raise HTTPException(status_code=500, detail=result["error"])

    answer_text: str = result.get("answer", "").strip()
    if not answer_text:
        raise HTTPException(status_code=500, detail="No answer generated")

    raw_nodes: List[Dict[str, Any]] = result.get("source_nodes", [])

    return QuestionResponse(
        document_id=document_id,
        question=question_request.question,
        answer=answer_text,
        source_nodes=[SourceNode(**node) for node in raw_nodes],
    )
