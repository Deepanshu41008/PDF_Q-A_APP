from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import Document, get_db
from app.services.qa_service import answer_question

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

@router.post("/documents/{document_id}/ask")
async def ask_question(
    document_id: int,
    question_request: QuestionRequest,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = answer_question(document_id, question_request.question)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "document_id": document_id,
        "question": question_request.question,
        "answer": result["answer"],
        "source_nodes": result.get("source_nodes", [])
    }