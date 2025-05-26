import uvicorn
from app.models.database import init_db
from app.core.config import UPLOAD_DIR, INDEX_DIR
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Create data directories using paths from config
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directories: {UPLOAD_DIR} and {INDEX_DIR}")
        
        # Run server
        logger.info("Starting server on port 12000")
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=12000, 
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        sys.exit(1)
