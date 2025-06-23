from __future__ import annotations

import logging
from typing import Any, Dict, List

from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI

from app.core.config import OPENROUTER_API_KEY, LLM_API_BASE, CHAT_MODEL_NAME
from app.services.document_service import get_document_index

logger = logging.getLogger(__name__)

def answer_question(document_id: int, question: str) -> Dict[str, Any]:
    """
    Answer a question using the document's vector index.
    
    Args:
        document_id: ID of the document to query
        question: User's question
        
    Returns:
        Dict with 'answer' and 'source_nodes' or 'error'
    """
    try:
        # Check for OpenRouter API key
        if not OPENROUTER_API_KEY:
            logger.error("OpenRouter API key not configured")
            return {"error": "OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable."}
        
        # Get vector store
        vectorstore = get_document_index(document_id)
        if not vectorstore:
            logger.warning(f"Document index not found for document {document_id}")
            return {"error": "Document index not found. Please wait for indexing to complete."}
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # Create LLM with API key and base URL for OpenRouter
        llm = ChatOpenAI(
            model_name=CHAT_MODEL_NAME,
            temperature=0,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=LLM_API_BASE
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Get answer
        result = qa_chain({"query": question})
        
        # Format response
        return {
            "answer": result.get("result", "").strip(),
            "source_nodes": [
                {
                    "text": doc.page_content[:500],  # Limit text length
                    "score": 1.0  # Score not available in this implementation
                }
                for doc in result.get("source_documents", [])
            ]
        }
    except Exception as e:
        logger.error(f"Error answering question for document {document_id}: {str(e)}", exc_info=True)
        return {"error": f"Failed to process question: {str(e)}"}
