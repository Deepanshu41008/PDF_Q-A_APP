import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { FaFilePdf, FaUpload } from 'react-icons/fa'
import { uploadDocument } from '../services/api'
import { useNavigate } from 'react-router-dom'

const FileUpload = () => {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const onDrop = useCallback(acceptedFiles => {
    const selectedFile = acceptedFiles[0]
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile)
      setError('')
      // Set default title from filename
      if (!title) {
        const filename = selectedFile.name.replace(/\.[^/.]+$/, "")
        setTitle(filename)
      }
    } else {
      setError('Please upload a PDF file')
    }
  }, [title])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a file to upload')
      return
    }

    try {
      setUploading(true)
      setError('')
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title || file.name)
      
      const response = await uploadDocument(formData)
      navigate(`/documents/${response.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload document')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer mb-4 ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="flex flex-col items-center">
            <FaFilePdf className="text-red-500 text-5xl mb-2" />
            <p className="text-gray-700">{file.name}</p>
            <p className="text-gray-500 text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <FaUpload className="text-gray-400 text-4xl mb-2" />
            <p className="text-gray-700">Drag & drop a PDF file here, or click to select</p>
            <p className="text-gray-500 text-sm mt-1">Only PDF files are accepted</p>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="title" className="block text-gray-700 mb-1">Document Title</label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter document title"
          />
        </div>
        
        <button
          type="submit"
          disabled={uploading || !file}
          className={`w-full py-2 px-4 rounded-lg text-white font-medium ${
            uploading || !file
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </form>
    </div>
  )
}

export default FileUpload