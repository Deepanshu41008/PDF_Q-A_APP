import { Link } from 'react-router-dom'
import { FaFilePdf } from 'react-icons/fa'

const DocumentCard = ({ document }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <Link to={`/documents/${document.id}`} className="block">
      <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
        <div className="flex items-center mb-4">
          <FaFilePdf className="text-red-500 text-3xl mr-3" />
          <h3 className="text-lg font-semibold text-gray-800 truncate">{document.title}</h3>
        </div>
        <div className="text-sm text-gray-500">
          <p>Uploaded: {formatDate(document.upload_date)}</p>
          <p className="truncate">{document.filename}</p>
        </div>
      </div>
    </Link>
  )
}

export default DocumentCard