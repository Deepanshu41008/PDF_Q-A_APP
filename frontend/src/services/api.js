import axios from 'axios'
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api'
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