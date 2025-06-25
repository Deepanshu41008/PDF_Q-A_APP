import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import io # For io.BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Assuming your FastAPI app instance is in app.main
from app.main import app
from app.models.database import Base, get_db
from app.models.document import Document
from app.core.config import UPLOAD_DIR, DATABASE_URL, DATA_DIR

# Ensure DATA_DIR and UPLOAD_DIR exist for the test environment
# This should ideally be handled by config.py, but for tests, explicit creation is safer.
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Setup a test database session
# Use the actual DATABASE_URL from config for this integration test
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency for tests
def override_get_db() -> Session:
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestDocumentUpload(unittest.TestCase):

    client = TestClient(app)

    def setUp(self):
        # Create tables for each test
        Base.metadata.create_all(bind=engine)
        self.db = next(override_get_db()) # Get a session for setup/assertions

    def tearDown(self):
        # Clean up database
        self.db.query(Document).delete()
        self.db.commit()
        self.db.close()
        # For a more thorough cleanup, you might drop tables, but for this scope, deleting data is fine.
        # Base.metadata.drop_all(bind=engine)


        # Clean up UPLOAD_DIR: remove all files and subdirectories
        for item in UPLOAD_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    # The path to mock is where create_document_index is *imported and called* by the route handler's logic
    # In this case, routes.documents imports it and its _index_wrapper calls it.
    @patch("app.api.routes.documents.create_document_index")
    def test_upload_successful_pdf(self, mock_create_document_index: MagicMock):
        # Mock the return value of the (backgrounded) create_document_index
        mock_create_document_index.return_value = True

        fake_pdf_content = b"%PDF-1.4 fake content for test"
        fake_pdf_filename = "test_upload.pdf"

        # 1. Make the POST request using TestClient
        response = self.client.post(
            "/api/documents/upload",
            files={"file": (fake_pdf_filename, io.BytesIO(fake_pdf_content), "application/pdf")},
            data={"title": "My Test PDF Upload"}
        )

        # 2. Assert HTTP response
        self.assertEqual(response.status_code, 201, f"Response content: {response.text}")
        data = response.json()

        self.assertIn("id", data)
        self.assertEqual(data["title"], "My Test PDF Upload")
        # Filename might be different due to generate_unique_name in document_service
        self.assertTrue(data["filename"].startswith(Path(fake_pdf_filename).stem))
        self.assertTrue(data["filename"].endswith(".pdf"))
        # is_indexed is True if index_path is not None. index_path is set before actual indexing.
        self.assertTrue(data["is_indexed"], "is_indexed should be true as index_path is set")

        doc_id = data["id"]
        saved_filename_from_response = data["filename"]

        # 3. Verify file saved in UPLOAD_DIR by the application
        # The filename in the response is the one to check for.
        expected_file_path = UPLOAD_DIR / saved_filename_from_response
        self.assertTrue(expected_file_path.exists(), f"File {expected_file_path} not found.")
        self.assertEqual(expected_file_path.read_bytes(), fake_pdf_content)

        # 4. Verify database record
        db_doc = self.db.query(Document).filter(Document.id == doc_id).first()
        self.assertIsNotNone(db_doc, "Document not found in database.")
        self.assertEqual(db_doc.title, "My Test PDF Upload")
        self.assertEqual(db_doc.filename, saved_filename_from_response)
        self.assertEqual(Path(db_doc.file_path), expected_file_path, "Database file_path incorrect.")
        # index_path should be set to <INDEX_DIR>/<doc_id>
        # We don't import INDEX_DIR here, but can reconstruct or check parts of it.
        self.assertIsNotNone(db_doc.index_path, "index_path should be set in the database.")
        self.assertTrue(str(doc_id) in db_doc.index_path, "Document ID not in index_path.")


        # 5. Verify that the mocked create_document_index was called correctly
        # The background task _index_wrapper calls create_document_index with (doc_id, file_path_obj)
        mock_create_document_index.assert_called_once_with(doc_id, expected_file_path)

        # 6. Cleanup the specific file created by this test (already handled by tearDown, but good for clarity)
        # expected_file_path.unlink(missing_ok=True) # tearDown will clean UPLOAD_DIR

if __name__ == "__main__":
    unittest.main()
