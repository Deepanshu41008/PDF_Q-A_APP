/* eslint-disable consistent-return */
import axios from 'axios';

/**
 * Always use /api prefix for backend API (Vite proxy required for local dev).
 */
const API_URL =
  import.meta.env.VITE_API_URL?.replace(/\/+$/, '') ||
  `${window.location.origin}/api`;

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000, // 30 seconds
});

// Global error interceptor – converts all errors to a uniform shape
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const msg =
      error?.response?.data?.detail ||
      error?.message ||
      'Unexpected network error';
    return Promise.reject(
      new Error(
        error?.response?.status ? `[${error.response.status}] ${msg}` : msg,
      ),
    );
  },
);

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

/**
 * Converts snake_case backend fields to camelCase as expected by React.
 * Fallbacks in case backend is changed or fields missing.
 */
function normaliseDocument(raw) {
  if (!raw || typeof raw !== 'object') return raw;
  // Accept both snake_case and camelCase backend for backward compat
  return {
    id: raw.id,
    filename: raw.filename,
    title: raw.title,
    uploadDate: raw.upload_date || raw.uploadDate,
    indexPath: raw.index_path || raw.indexPath,
    fileSize: raw.file_size || raw.fileSize,
    pageCount: raw.page_count || raw.pageCount,
    isIndexed: raw.is_indexed ?? !!raw.index_path,
  };
}

/**
 * Upload a PDF (multipart/form-data, always through /api prefix).
 * @param {FormData} formData – must include `file` and optionally `title`
 */
export async function uploadDocument(formData) {
  const { data } = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return normaliseDocument(data);
}

/**
 * Fetch all documents.
 */
export async function getDocuments() {
  const { data } = await api.get('/documents');
  return data.map(normaliseDocument);
}

/**
 * Fetch a single document by ID.
 * @param {number|string} id
 */
export async function getDocument(id) {
  const { data } = await api.get(`/documents/${encodeURIComponent(id)}`);
  return normaliseDocument(data);
}

/**
 * Ask a question about a document.
 * @param {number|string} documentId
 * @param {{question: string}} questionData
 */
export async function askQuestion(documentId, questionData) {
  const { data } = await api.post(
    `/documents/${encodeURIComponent(documentId)}/ask`,
    questionData,
  );
  return data;
}

// Export the raw axios instance if needed elsewhere
export { api };
