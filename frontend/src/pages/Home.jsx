import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import DocumentCard from '../components/DocumentCard'
import { getDocuments } from '../services/api'
import { FaUpload, FaSpinner } from 'react-icons/fa'

const Home = () => {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true)
        const data = await getDocuments()
        setDocuments(data)
      } catch (err) {
        setError('Failed to load documents')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchDocuments()
  }, [])

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
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Your Documents</h1>
        <Link 
          to="/upload" 
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center"
        >
          <FaUpload className="mr-2" />
          Upload New
        </Link>
      </div>

      {documents.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">No documents yet</h2>
          <p className="text-gray-600 mb-6">Upload your first PDF document to get started</p>
          <Link 
            to="/upload" 
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg inline-flex items-center"
          >
            <FaUpload className="mr-2" />
            Upload Document
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map(doc => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      )}
    </div>
  )
}

export default Home