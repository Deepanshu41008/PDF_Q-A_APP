import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getDocument } from '../services/api'
import QuestionForm from '../components/QuestionForm'
import AnswerDisplay from '../components/AnswerDisplay'
import { FaArrowLeft, FaFilePdf, FaSpinner } from 'react-icons/fa'

const DocumentView = () => {
  const { id } = useParams()
  const [document, setDocument] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [qaHistory, setQaHistory] = useState([])

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true)
        const data = await getDocument(id)
        setDocument(data)
      } catch (err) {
        setError('Failed to load document')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchDocument()
  }, [id])

  const handleAnswerReceived = (qaData) => {
    setQaHistory(prev => [qaData, ...prev])
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <FaSpinner className="animate-spin text-blue-600 text-4xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-100 text-red-700 p-4 rounded-lg">
        <p>{error}</p>
        <Link to="/" className="text-red-700 underline mt-2 inline-block">
          Back to Home
        </Link>
      </div>
    )
  }

  if (!document) return null

  return (
    <div>
      <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-6">
        <FaArrowLeft className="mr-2" />
        Back to Documents
      </Link>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center">
          <FaFilePdf className="text-red-500 text-4xl mr-4" />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{document.title}</h1>
            <p className="text-gray-600">{document.filename}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Ask a Question</h2>
        <p className="text-gray-600 mb-4">
          Ask any question about the content of this document, and our AI will provide an answer based on the information contained within.
        </p>
        
        <QuestionForm documentId={document.id} onAnswerReceived={handleAnswerReceived} />
      </div>

      {qaHistory.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Question History</h2>
          {qaHistory.map((qa, index) => (
            <AnswerDisplay key={index} qa={qa} />
          ))}
        </div>
      )}
    </div>
  )
}

export default DocumentView