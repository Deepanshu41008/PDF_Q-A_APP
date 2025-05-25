from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, questions

app = FastAPI(title="PDF QA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:12001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(questions.router, prefix="/api", tags=["questions"])

@app.get("/")
async def root():
    return {"message": "Welcome to PDF QA API"}