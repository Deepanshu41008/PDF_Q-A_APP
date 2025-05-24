import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
INDEX_DIR = os.path.join(os.getcwd(), "indices")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)