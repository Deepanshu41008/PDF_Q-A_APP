# PDF Question-Answering Application – Architecture Documentation (2024 rev.)

---

## 1 · High-Level Design (HLD)

### 1.1 System Overview  
The application lets users upload PDF documents and ask natural-language
questions about their content.  
Uploaded files are persisted on disk, vectorised with FAISS, and queried by an
LLM chain (LangChain + OpenAI).

```
┌──────────┐     REST/JSON      ┌──────────┐
│ React UI │  ───────────────▶ │ FastAPI  │───┐
└──────────┘                   └──────────┘   │
   ▲   ▲                                  ┌───▼─────────┐
   │   └──── file upload / QA ───────────▶│ Services    │
   │                                       │  Document  │─► Disk (PDFs)
   │                                       │  Vector    │─► Disk (FAISS)
   │                                       │  QA/LLM    │─► OpenAI
   │                                       └────────────┘
   │
   └────────── rendered answers ◀───────────────┘
```

---

## 2 · Component Breakdown

### 2.1 Frontend (React 18 + Vite)
* **Pages**  
  `Home.jsx`, `Upload.jsx`, `DocumentView.jsx`
* **Components**  
  `DocumentCard`, `FileUpload`, `QuestionForm`, `AnswerDisplay`
* **Services**  
  `src/services/api.js` – Axios wrapper (env-driven `VITE_API_URL`)
* **Build / Dev**  
  Vite (`vite.config.js`) – proxy to backend (`VITE_BACKEND_URL`, default :12000)

### 2.2 Backend (FastAPI 0.110)
* **Application factory** `app/main.py`  
  – Loads config, initialises DB, registers routers, CORS, global error handler.
* **Routers**
  * `/api/documents` → `app/api/routes/documents.py`
    * `POST /upload`
    * `GET /` (list)
    * `GET /{id}`
    * `DELETE /{id}`
  * `/api/documents/{id}/ask` → `app/api/routes/questions.py`
* **Services**  
  * `app/services/document_service.py` – file I/O, FAISS indexing, helpers  
  * `app/services/qa_service.py`      – RetrievalQA wrapper (LangChain v0.1)
* **Models / DB**
  * `app/models/document.py` (SQLAlchemy 2 typed-ORM)  
    `id, filename, file_path, index_path, upload_date, title`
  * `app/models/database.py` – engine, `Base`, `get_db`, `init_db`
* **Configuration** `app/core/config.py`  
  Env vars (`OPENAI_API_KEY`, `CORS_ORIGINS`, …), directory constants, OpenAI
  client bootstrap.

### 2.3 Data Stores
* **SQLite** file `data/pdf_qa.db` – document metadata
* **File System**  
  `data/documents/` (PDFs), `data/indices/<id>/vectorstore.pkl` (FAISS)

---

## 3 · Detailed Flows

### 3.1 Document Upload
1. `FileUpload` sends `multipart/form-data` ⇒ `POST /api/documents/upload`  
2. Backend validation → `save_uploaded_file()` writes atomically.  
3. Row inserted; `index_path` set after `db.flush()` to get PK.  
4. FAISS index built in a background thread (`anyio.to_thread`).  
5. JSON response → UI updates list.

### 3.2 Ask Question
1. `QuestionForm` posts `{question}` ⇒ `POST /api/documents/{id}/ask`.  
2. Router off-loads blocking `answer_question()` to a worker thread.  
3. Service loads FAISS store, runs `RetrievalQA` (OpenAI embeddings).  
4. Returns `{answer, source_nodes[]}` → displayed in `AnswerDisplay`.

---

## 4 · Technology Stack

| Layer         | Library / Tool | Version Pin |
| ------------- | -------------- | ----------- |
| API           | FastAPI        | 0.110.1     |
| ORM / DB      | SQLAlchemy 2   | 2.0.29      |
| Vector Store  | FAISS-cpu      | 1.8.0       |
| LLM Orchestration | LangChain | 0.1.16      |
| PDF Parsing   | PyMuPDF        | 1.23.15     |
| Client UI     | React          | 18.2.0      |
| Bundler       | Vite           | 4.4.5       |

---

## 5 · Deployment

| Service  | Default Port | Command                                        |
| -------- | ------------ | ---------------------------------------------- |
| Backend  | 12000        | `uvicorn app.main:app --host 0.0.0.0 --port 12000` |
| Frontend | 12001        | `npm run dev` (Vite proxy → backend)           |

Static files are written to `./data` which must be writable by the API
container / process.

---

## 6 · Security & Ops Notes

* CORS origins configurable via `CORS_ORIGINS` env (comma-sep).  
* Upload validation: MIME & extension (`.pdf` only).  
* Large-file limit enforced at reverse-proxy level (recommend ≤ 20 MB).  
* Unhandled exceptions logged server-side; client receives `{"detail":"Internal Server Error"}`.  
* Background tasks use thread-pool (not asyncio) to avoid GIL-bound CPU spikes.

---

## 7 · Roadmap

1. User auth (JWT + role-based doc access)  
2. Multi-document / cross-doc QA  
3. OCR + support for scanned PDFs / images  
4. Docker / K8s deployment manifests  
5. Streaming answers with SSE for long responses  

---

