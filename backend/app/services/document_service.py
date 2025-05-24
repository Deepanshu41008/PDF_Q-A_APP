import os
import fitz  # PyMuPDF
import shutil
from pathlib import Path
import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader

UPLOAD_DIR = "uploads"
INDEX_DIR = "indices"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

def save_uploaded_file(file, filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path

def extract_text_from_pdf(file_path):
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def create_document_index(document_id, file_path):
    try:
        # Load PDF with PyMuPDF
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
        
        if not documents:
            return False
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # Save index
        index_path = os.path.join(INDEX_DIR, f"{document_id}")
        os.makedirs(index_path, exist_ok=True)
        
        with open(os.path.join(index_path, "vectorstore.pkl"), "wb") as f:
            pickle.dump(vectorstore, f)
        
        return True
    except Exception as e:
        print(f"Error creating document index: {e}")
        return False

def get_document_index(document_id):
    try:
        index_path = os.path.join(INDEX_DIR, f"{document_id}")
        vectorstore_path = os.path.join(index_path, "vectorstore.pkl")
        
        if not os.path.exists(vectorstore_path):
            return None
        
        with open(vectorstore_path, "rb") as f:
            vectorstore = pickle.load(f)
        
        return vectorstore
    except Exception as e:
        print(f"Error loading document index: {e}")
        return None