/* eslint-disable consistent-return */
import axios from 'axios';

/**
 * Derive API base URL from env or fall back to same-origin `/api`.
 * Vite exposes env vars through `import.meta.env`.
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
  timeout: 30_000, // 30 s network timeout
});

// Global error interceptor – converts all errors to a uniform shape
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    // Normalise Axios / Fetch / Network errors to Error(message)
    const msg =
      error?.response?.data?.detail ||
      error?.message ||
      'Unexpected network error';
    return Promise.reject(
      new Error(
        // Include HTTP status if present
        error?.response?.status ? `[${error.response.status}] ${msg}` : msg,
      ),
    );
  },
);

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

/**
 * Upload a PDF (multipart/form-data). Returns created document JSON.
 * @param {FormData} formData – must include `file` and optionally `title`
 */
export async function uploadDocument(formData) {
  try {
    const { data } = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  } catch (err) {
    throw err; // already normalised by interceptor
  }
}

/**
 * Fetch all documents.
 * @returns {Promise<Array<Object>>}
 */
export async function getDocuments() {
  try {
    const { data } = await api.get('/documents');
    return data;
  } catch (err) {
    throw err;
  }
}

/**
 * Fetch a single document by ID.
 * @param {number|string} id
 */
export async function getDocument(id) {
  try {
    const { data } = await api.get(`/documents/${encodeURIComponent(id)}`);
    return data;
  } catch (err) {
    throw err;
  }
}

/**
 * Ask a question about a document.
 * @param {number|string} documentId
 * @param {{question: string}} questionData
 */
export async function askQuestion(documentId, questionData) {
  try {
    const { data } = await api.post(
      `/documents/${encodeURIComponent(documentId)}/ask`,
      questionData,
    );
    return data;
  } catch (err) {
    throw err;
  }
}

// Export the raw axios instance in case advanced callers need it
export { api };