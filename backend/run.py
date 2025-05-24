import uvicorn
from app.models.database import init_db
import os

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Create upload and index directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("indices", exist_ok=True)
    
    # Run server
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=12000, 
        reload=True
    )