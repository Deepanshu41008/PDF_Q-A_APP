import ReactMarkdown from 'react-markdown'

const AnswerDisplay = ({ qa }) => {
  if (!qa) return null

  return (
    <div className="mt-6 bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Question:</h3>
        <p className="text-gray-700">{qa.question}</p>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Answer:</h3>
        <div className="prose max-w-none text-gray-700">
          <ReactMarkdown>{qa.answer}</ReactMarkdown>
        </div>
      </div>
      
      {qa.source_nodes && qa.source_nodes.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Sources:</h4>
          <div className="max-h-40 overflow-y-auto text-sm text-gray-600 bg-gray-50 p-3 rounded">
            {qa.source_nodes.map((node, index) => (
              <div key={index} className="mb-2 pb-2 border-b border-gray-200 last:border-0">
                <p>{node.text.substring(0, 200)}...</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default AnswerDisplay