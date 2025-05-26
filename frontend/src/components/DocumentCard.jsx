import { Link } from 'react-router-dom'
import { FaFilePdf, FaClock, FaCheckCircle, FaHourglassHalf } from 'react-icons/fa'

const DocumentCard = ({ document }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size'
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(2)} MB`
  }

  return (
    <Link to={`/documents/${document.id}`} className="block">
      <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200">
        <div className="flex items-start justify-between mb-4">
          <FaFilePdf className="text-red-500 text-3xl" />
          {document.isIndexed ? (
            <FaCheckCircle className="text-green-500 text-xl" title="Indexed" />
          ) : (
            <FaHourglassHalf className="text-yellow-500 text-xl animate-pulse" title="Indexing..." />
          )}
        </div>
        
        <h3 className="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">
          {document.title}
        </h3>
        
        <p className="text-sm text-gray-600 mb-1 truncate">
          {document.filename}
        </p>
        
        <div className="flex items-center text-xs text-gray-500 mt-3">
          <FaClock className="mr-1" />
          {formatDate(document.upload_date)}
        </div>
        
        {document.fileSize && (
          <p className="text-xs text-gray-500 mt-1">
            {formatFileSize(document.fileSize)}
          </p>
        )}
        
        {document.pageCount && (
          <p className="text-xs text-gray-500">
            {document.pageCount} pages
          </p>
        )}
      </div>
    </Link>
  )
}

export default DocumentCard
