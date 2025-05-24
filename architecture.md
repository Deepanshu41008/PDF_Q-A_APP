# PDF Question Answering Application - Architecture Documentation

## High Level Design (HLD)

### System Overview
The PDF Question Answering application is a full-stack web application that allows users to upload PDF documents and ask questions about their content. The system uses natural language processing to analyze the documents and provide relevant answers based on the document content.

### Architecture Components
The application follows a client-server architecture with the following main components:

1. **Frontend (Client)**
   - Built with React.js
   - Provides user interface for document upload, management, and question asking
   - Communicates with the backend via RESTful API calls

2. **Backend (Server)**
   - Built with FastAPI
   - Handles document processing, storage, and retrieval
   - Processes natural language questions and generates answers
   - Manages database operations

3. **Database**
   - SQLite for storing document metadata
   - File system for storing the actual PDF files

4. **NLP Processing**
   - Uses LangChain for document processing and question answering
   - Integrates with OpenAI for natural language understanding
   - Uses FAISS for vector storage and similarity search

### Data Flow
1. User uploads a PDF document through the frontend interface
2. Frontend sends the document to the backend via API
3. Backend processes the document:
   - Extracts text from the PDF
   - Creates vector embeddings of the text
   - Stores the document metadata in the database
   - Stores the document file in the file system
4. User asks a question about a document
5. Frontend sends the question to the backend
6. Backend processes the question:
   - Retrieves the document's vector embeddings
   - Uses LangChain to find relevant context from the document
   - Generates an answer using OpenAI
7. Backend returns the answer to the frontend
8. Frontend displays the answer to the user

## Low Level Design (LLD)

### Backend Components

#### 1. FastAPI Application
- **Main Application (`main.py`)**
  - Initializes the FastAPI application
  - Sets up CORS middleware
  - Includes API routers

- **API Routes**
  - **Documents Router (`routes/documents.py`)**
    - `/api/documents/upload` - Endpoint for uploading PDF documents
    - `/api/documents` - Endpoint for retrieving all documents
    - `/api/documents/{id}` - Endpoint for retrieving a specific document
  
  - **Questions Router (`routes/questions.py`)**
    - `/api/documents/{id}/ask` - Endpoint for asking questions about a document

#### 2. Database Models
- **Document Model (`models/document.py`)**
  - Represents a document in the database
  - Fields: id, title, filename, upload_date, file_path, vector_store_path

#### 3. Services
- **Document Service (`services/document_service.py`)**
  - Handles PDF processing
  - Extracts text from PDFs using PyMuPDF
  - Creates vector embeddings using LangChain
  - Stores documents in the database and file system

- **QA Service (`services/qa_service.py`)**
  - Handles question answering
  - Uses LangChain's RetrievalQA to find relevant context
  - Generates answers using OpenAI

#### 4. Database
- **Database Connection (`database.py`)**
  - Sets up SQLAlchemy connection
  - Creates database tables

### Frontend Components

#### 1. React Application
- **Main Application (`App.jsx`)**
  - Sets up routing using React Router
  - Defines the main layout

- **Pages**
  - **Home Page (`pages/Home.jsx`)**
    - Displays a list of uploaded documents
    - Allows navigation to document view
  
  - **Upload Page (`pages/Upload.jsx`)**
    - Provides interface for uploading new documents
  
  - **Document View Page (`pages/DocumentView.jsx`)**
    - Displays document details
    - Provides interface for asking questions
    - Shows question history and answers

#### 2. Components
- **Document Card (`components/DocumentCard.jsx`)**
  - Displays a card for each document in the list
  
- **File Upload (`components/FileUpload.jsx`)**
  - Handles file selection and upload
  - Validates file types
  
- **Question Form (`components/QuestionForm.jsx`)**
  - Provides input for asking questions
  
- **Answer Display (`components/AnswerDisplay.jsx`)**
  - Renders answers with markdown support

#### 3. Services
- **API Service (`services/api.js`)**
  - Handles communication with the backend API
  - Methods for document upload, retrieval, and question asking

### Technology Stack Details

#### Backend
- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **PyMuPDF**: Library for PDF processing
- **LangChain**: Framework for building LLM applications
- **FAISS**: Vector database for similarity search
- **OpenAI**: LLM provider for natural language understanding

#### Frontend
- **React**: JavaScript library for building user interfaces
- **React Router**: Library for routing in React applications
- **Axios**: HTTP client for API requests
- **TailwindCSS**: Utility-first CSS framework
- **React Dropzone**: Library for file uploads
- **React Markdown**: Library for rendering markdown content

## Deployment Architecture

The application is deployed with the following components:

1. **Backend Server**
   - Runs on port 12000
   - Handles API requests
   - Processes documents and questions

2. **Frontend Server**
   - Runs on port 12001
   - Serves the React application
   - Communicates with the backend server

3. **File Storage**
   - Local file system for storing uploaded PDFs
   - Separate directory for vector stores

4. **Database**
   - SQLite database file for storing document metadata

## Security Considerations

1. **CORS Configuration**
   - Backend configured to accept requests only from allowed origins

2. **File Validation**
   - Frontend and backend validate file types (PDF only)
   - Size limits for uploaded files

3. **Error Handling**
   - Proper error handling for API requests
   - User-friendly error messages

## Performance Considerations

1. **Document Processing**
   - Asynchronous processing of PDF documents
   - Efficient text extraction and chunking

2. **Vector Storage**
   - FAISS for efficient similarity search
   - Persistent storage of vector embeddings

3. **API Optimization**
   - Efficient database queries
   - Proper indexing for document retrieval

## Future Enhancements

1. **Authentication and Authorization**
   - User accounts and authentication
   - Document access control

2. **Advanced Document Processing**
   - Support for more document types (DOCX, TXT, etc.)
   - OCR for scanned documents

3. **Enhanced Question Answering**
   - Multi-document question answering
   - Follow-up question handling with context

4. **UI Improvements**
   - Document preview
   - Advanced search functionality
   - Mobile-responsive design improvements