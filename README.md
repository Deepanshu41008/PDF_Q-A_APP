# PDF Question Answering Application

A full-stack application that allows users to upload PDF documents and ask questions about their content. The application uses natural language processing to provide answers based on the document content.

## Features

- Upload PDF documents
- Ask questions about document content
- Get AI-generated answers based on document content
- View question and answer history

## Tech Stack

### Backend
- FastAPI - Python web framework
- LangChain/LlamaIndex - NLP processing
- SQLite - Database for document metadata
- PyMuPDF - PDF text extraction

### Frontend
- React.js - UI library
- React Router - Navigation
- Axios - API requests
- TailwindCSS - Styling
- React Dropzone - File uploads

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── uploads/
│   ├── indices/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the backend directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Run the server:
   ```
   python run.py
   ```
   The server will run on http://localhost:12000

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```
   The frontend will run on http://localhost:12001

## API Documentation

### Document Endpoints

- `POST /api/documents/upload` - Upload a PDF document
  - Request: Multipart form data with `file` and optional `title`
  - Response: Document metadata

- `GET /api/documents` - Get all documents
  - Response: Array of document metadata

- `GET /api/documents/{document_id}` - Get document by ID
  - Response: Document metadata

### Question Endpoints

- `POST /api/documents/{document_id}/ask` - Ask a question about a document
  - Request: JSON with `question` field
  - Response: Answer and source information

## Usage

1. Upload a PDF document through the upload page
2. Navigate to the document view page
3. Ask questions about the document content
4. View answers and question history