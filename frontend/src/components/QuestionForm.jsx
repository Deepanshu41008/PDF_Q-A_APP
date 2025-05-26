import { useState } from 'react'
import { askQuestion } from '../services/api'

const QuestionForm = ({ documentId, onAnswerReceived }) => {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    try {
      setLoading(true)
      setError('')
      
      const response = await askQuestion(documentId, { question })
      onAnswerReceived(response)
      setQuestion('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get answer')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-6">
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col md:flex-row gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="flex-grow px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ask a question about this document..."
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className={`px-6 py-2 rounded-lg text-white font-medium ${
              loading || !question.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Asking...' : 'Ask'}
          </button>
        </div>
      </form>
      
      {error && (
        <div className="mt-2 text-red-600 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

export default QuestionForm