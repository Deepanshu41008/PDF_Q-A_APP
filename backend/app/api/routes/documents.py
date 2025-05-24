from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import Document, get_db
from app.services.document_service import save_uploaded_file, create_document_index
import os

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save the file
    filename = file.filename
    file_path = save_uploaded_file(file, filename)
    
    # Create document record in database
    db_document = Document(
        filename=filename,
        file_path=file_path,
        title=title or filename
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Create document index
    success = create_document_index(db_document.id, file_path)
    if not success:
        db.delete(db_document)
        db.commit()
        os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to process document")
    
    return {
        "id": db_document.id,
        "filename": db_document.filename,
        "title": db_document.title,
        "upload_date": db_document.upload_date
    }

@router.get("/documents")
async def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "title": doc.title,
            "upload_date": doc.upload_date
        }
        for doc in documents
    ]

@router.get("/documents/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "title": document.title,
        "upload_date": document.upload_date
    }