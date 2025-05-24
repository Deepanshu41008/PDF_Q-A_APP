# PDF Question Answering Application - Code Documentation

## Project Structure

```
/workspace/
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   └── document.py
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   └── questions.py
│   │   └── services/
│   │       ├── document_service.py
│   │       └── qa_service.py
│   ├── data/
│   │   ├── documents/
│   │   └── vector_stores/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── AnswerDisplay.jsx
│   │   │   ├── DocumentCard.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   ├── Navbar.jsx
│   │   │   └── QuestionForm.jsx
│   │   ├── main.jsx
│   │   ├── pages/
│   │   │   ├── DocumentView.jsx
│   │   │   ├── Home.jsx
│   │   │   └── Upload.jsx
│   │   └── services/
│   │       └── api.js
│   ├── tailwind.config.js
│   └── vite.config.js
├── .env
├── .gitignore
├── README.md
└── run.sh
```

## Backend Code Documentation

### Main Application (`backend/app/main.py`)

The main FastAPI application file sets up the API server, configures CORS, and includes the API routers.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import documents, questions

app = FastAPI(title="PDF QA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev",
        "https://work-2-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev",
        "https://work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev:12000",
        "https://work-2-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev:12001",
        "http://localhost:12001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(questions.router, prefix="/api", tags=["questions"])
```

### Database Configuration (`backend/app/database.py`)

Sets up the SQLAlchemy database connection and creates the database tables.

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/pdf_qa.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Document Model (`backend/app/models/document.py`)

Defines the Document model for storing document metadata in the database.

```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String)
    vector_store_path = Column(String)
```

### Document Service (`backend/app/services/document_service.py`)

Handles PDF processing, text extraction, and vector embedding creation.

```python
import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
import shutil

DOCUMENT_DIR = "./data/documents"
VECTOR_STORE_DIR = "./data/vector_stores"

os.makedirs(DOCUMENT_DIR, exist_ok=True)
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def process_document(file_path, document_id):
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    
    # Create vector store
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(chunks, embeddings)
    
    # Save vector store
    vector_store_path = os.path.join(VECTOR_STORE_DIR, f"doc_{document_id}")
    vector_store.save_local(vector_store_path)
    
    return vector_store_path

def save_uploaded_file(file, filename, document_id):
    # Create directory if it doesn't exist
    os.makedirs(DOCUMENT_DIR, exist_ok=True)
    
    # Save file
    file_path = os.path.join(DOCUMENT_DIR, f"doc_{document_id}_{filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path
```

### QA Service (`backend/app/services/qa_service.py`)

Handles question answering using LangChain and OpenAI.

```python
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI

def get_answer_for_question(vector_store_path, question):
    # Load vector store
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.load_local(vector_store_path, embeddings)
    
    # Create retriever
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    # Create QA chain
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # Get answer
    result = qa({"query": question})
    
    return {
        "answer": result["result"],
        "sources": [doc.page_content for doc in result["source_documents"]]
    }
```

### Documents Router (`backend/app/routes/documents.py`)

Defines API endpoints for document management.

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os

from app.database import get_db
from app.models.document import Document
from app.services.document_service import save_uploaded_file, process_document

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create document in database
    db_document = Document(
        title=title,
        filename=file.filename
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Save file
    file_path = save_uploaded_file(file, file.filename, db_document.id)
    
    # Process document
    vector_store_path = process_document(file_path, db_document.id)
    
    # Update document with file paths
    db_document.file_path = file_path
    db_document.vector_store_path = vector_store_path
    db.commit()
    
    return {"id": db_document.id, "title": db_document.title}

@router.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return [{"id": doc.id, "title": doc.title, "filename": doc.filename, "upload_date": doc.upload_date} for doc in documents]

@router.get("/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "upload_date": document.upload_date
    }
```

### Questions Router (`backend/app/routes/questions.py`)

Defines API endpoints for question answering.

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.document import Document
from app.services.qa_service import get_answer_for_question

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

@router.post("/documents/{document_id}/ask")
def ask_question(
    document_id: int,
    question_request: QuestionRequest,
    db: Session = Depends(get_db)
):
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get answer
    result = get_answer_for_question(
        document.vector_store_path,
        question_request.question
    )
    
    return {
        "question": question_request.question,
        "answer": result["answer"],
        "sources": result["sources"]
    }
```

## Frontend Code Documentation

### Main Application (`frontend/src/App.jsx`)

Sets up the React application with routing.

```jsx
import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Upload from './pages/Upload'
import DocumentView from './pages/DocumentView'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/documents/:id" element={<DocumentView />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
```

### API Service (`frontend/src/services/api.js`)

Handles communication with the backend API.

```javascript
import axios from 'axios'

const API_URL = 'http://work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev:12000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const uploadDocument = async (formData) => {
  const response = await axios.post(`${API_URL}/documents/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getDocuments = async () => {
  const response = await api.get('/documents')
  return response.data
}

export const getDocument = async (id) => {
  const response = await api.get(`/documents/${id}`)
  return response.data
}

export const askQuestion = async (documentId, questionData) => {
  const response = await api.post(`/documents/${documentId}/ask`, questionData)
  return response.data
}
```

### Home Page (`frontend/src/pages/Home.jsx`)

Displays a list of uploaded documents.

```jsx
import React, { useState, useEffect } from 'react'
import { getDocuments } from '../services/api'
import DocumentCard from '../components/DocumentCard'

const Home = () => {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await getDocuments()
        setDocuments(data)
        setLoading(false)
      } catch (err) {
        setError('Failed to load documents')
        setLoading(false)
      }
    }

    fetchDocuments()
  }, [])

  if (loading) return <div className="text-center py-8">Loading documents...</div>
  if (error) return <div className="bg-red-100 p-4 rounded-md text-red-700">{error}</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Your Documents</h1>
      {documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No documents yet. Upload your first PDF document.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((document) => (
            <DocumentCard key={document.id} document={document} />
          ))}
        </div>
      )}
    </div>
  )
}

export default Home
```

### Upload Page (`frontend/src/pages/Upload.jsx`)

Provides interface for uploading new documents.

```jsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '../components/FileUpload'
import { uploadDocument } from '../services/api'

const Upload = () => {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleFileChange = (selectedFile) => {
    setFile(selectedFile)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      setError('Please select a PDF file')
      return
    }
    
    if (!title.trim()) {
      setError('Please enter a document title')
      return
    }
    
    try {
      setUploading(true)
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title)
      
      const response = await uploadDocument(formData)
      
      navigate(`/documents/${response.id}`)
    } catch (err) {
      setError('Failed to upload document. Please try again.')
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-center">Upload PDF Document</h1>
      
      {error && (
        <div className="bg-red-100 p-4 rounded-md text-red-700 mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-6">
          <FileUpload onFileChange={handleFileChange} />
        </div>
        
        <div className="mb-6">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Document Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter document title"
          />
        </div>
        
        <button
          type="submit"
          disabled={!file || !title.trim() || uploading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
        >
          {uploading ? 'Uploading Document...' : 'Upload Document'}
        </button>
      </form>
    </div>
  )
}

export default Upload
```

### Document View Page (`frontend/src/pages/DocumentView.jsx`)

Displays document details and provides interface for asking questions.

```jsx
import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getDocument, askQuestion } from '../services/api'
import QuestionForm from '../components/QuestionForm'
import AnswerDisplay from '../components/AnswerDisplay'

const DocumentView = () => {
  const { id } = useParams()
  const [document, setDocument] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [questions, setQuestions] = useState([])
  const [asking, setAsking] = useState(false)

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const data = await getDocument(id)
        setDocument(data)
        setLoading(false)
      } catch (err) {
        setError('Failed to load document')
        setLoading(false)
      }
    }

    fetchDocument()
  }, [id])

  const handleAskQuestion = async (questionText) => {
    try {
      setAsking(true)
      
      const response = await askQuestion(id, { question: questionText })
      
      setQuestions([response, ...questions])
      setAsking(false)
    } catch (err) {
      setError('Failed to get answer. Please try again.')
      setAsking(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading document...</div>
  if (error) return <div className="bg-red-100 p-4 rounded-md text-red-700">{error}</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">{document.title}</h1>
      <p className="text-gray-500 mb-6">
        Uploaded on {new Date(document.upload_date).toLocaleDateString()}
      </p>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Ask a Question</h2>
        <QuestionForm onSubmit={handleAskQuestion} isLoading={asking} />
      </div>
      
      {questions.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Questions & Answers</h2>
          
          <div className="space-y-6">
            {questions.map((item, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-6">
                <h3 className="font-medium text-lg mb-2">Q: {item.question}</h3>
                <AnswerDisplay answer={item.answer} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentView
```

### File Upload Component (`frontend/src/components/FileUpload.jsx`)

Handles file selection and upload.

```jsx
import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FiUpload } from 'react-icons/fi'

const FileUpload = ({ onFileChange }) => {
  const onDrop = useCallback(
    (acceptedFiles) => {
      const file = acceptedFiles[0]
      if (file) {
        onFileChange(file)
      }
    },
    [onFileChange]
  )

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  })

  const selectedFile = acceptedFiles[0]

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-500'
        }`}
      >
        <input {...getInputProps()} />
        
        <FiUpload className="mx-auto h-12 w-12 text-gray-400" />
        
        <p className="mt-2 text-sm text-gray-600">
          Drag & drop a PDF file here, or click to select
        </p>
        
        <p className="mt-1 text-xs text-gray-500">
          Only PDF files are accepted
        </p>
      </div>

      {selectedFile && (
        <div className="mt-4 p-3 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-700">
            Selected file: <span className="font-medium">{selectedFile.name}</span> ({(
              selectedFile.size / 1024 / 1024
            ).toFixed(2)} MB)
          </p>
        </div>
      )}
    </div>
  )
}

export default FileUpload
```

### Question Form Component (`frontend/src/components/QuestionForm.jsx`)

Provides input for asking questions.

```jsx
import React, { useState } from 'react'

const QuestionForm = ({ onSubmit, isLoading }) => {
  const [question, setQuestion] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (question.trim()) {
      onSubmit(question)
      setQuestion('')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="flex flex-col md:flex-row gap-4">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this document..."
          className="flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
        >
          {isLoading ? 'Processing...' : 'Ask'}
        </button>
      </div>
    </form>
  )
}

export default QuestionForm
```

### Answer Display Component (`frontend/src/components/AnswerDisplay.jsx`)

Renders answers with markdown support.

```jsx
import React from 'react'
import ReactMarkdown from 'react-markdown'

const AnswerDisplay = ({ answer }) => {
  return (
    <div className="mt-2 prose prose-blue max-w-none">
      <ReactMarkdown>{answer}</ReactMarkdown>
    </div>
  )
}

export default AnswerDisplay
```

## Configuration Files

### Backend Requirements (`backend/requirements.txt`)

```
fastapi
uvicorn
python-multipart
pydantic
langchain
langchain-community
pymupdf
python-dotenv
sqlalchemy
aiofiles
openai
faiss-cpu
```

### Frontend Package Configuration (`frontend/package.json`)

```json
{
  "name": "pdf-qa-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.3.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "react-icons": "^4.8.0",
    "react-markdown": "^8.0.5",
    "react-router-dom": "^6.9.0"
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.3",
    "@tailwindcss/typography": "^0.5.9",
    "@vitejs/plugin-react": "^3.1.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.21",
    "tailwindcss": "^3.2.7",
    "vite": "^4.2.0"
  }
}
```

### Vite Configuration (`frontend/vite.config.js`)

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 12001,
    strictPort: true,
    cors: true,
    hmr: {
      clientPort: 12001
    },
    allowedHosts: [
      'work-2-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev',
      'work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev'
    ]
  }
})
```

### Run Script (`run.sh`)

```bash
#!/bin/bash

# Install backend dependencies
echo "Installing backend dependencies..."
cd /workspace/backend && pip install -r requirements.txt

# Start backend server
echo "Starting backend server..."
cd /workspace/backend && uvicorn app.main:app --host 0.0.0.0 --port 12000 &

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd /workspace/frontend && npm install

# Start frontend server
echo "Starting frontend server..."
cd /workspace/frontend && npm run dev
```

## Environment Variables

### Backend Environment Variables (`.env`)

```
OPENAI_API_KEY=your_openai_api_key
```

## Conclusion

This documentation provides a comprehensive overview of the PDF Question Answering application's code structure and implementation. The application follows a clean architecture with separation of concerns between the frontend and backend components. The backend handles document processing and question answering using LangChain and OpenAI, while the frontend provides an intuitive user interface for interacting with the system.

The code is organized in a modular way, making it easy to maintain and extend. Each component has a specific responsibility, and the interactions between components are well-defined through APIs and services.