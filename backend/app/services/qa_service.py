from app.services.document_service import get_document_index
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
import os

def answer_question(document_id, question):
    try:
        vectorstore = get_document_index(document_id)
        if not vectorstore:
            return {"error": "Document index not found"}
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # Create LLM
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0
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
            "answer": result["result"],
            "source_nodes": [
                {"text": doc.page_content, "score": 1.0}  # Score not available in this implementation
                for doc in result["source_documents"]
            ]
        }
    except Exception as e:
        print(f"Error answering question: {e}")
        return {"error": str(e)}