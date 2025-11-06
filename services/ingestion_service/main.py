"""
Ingestion Service - PDF processing and text extraction.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
from io import BytesIO

from config import settings
from database import Base, engine, SessionLocal
from models import Document
from schemas import HealthResponse, ProcessPDFResponse, DocumentListItem, ChunkResponse
from utils import chunk_text

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/documents", response_model=list[DocumentListItem])
async def list_documents():
    """
    List all processed documents with metadata.
    """
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "total_pages": doc.total_pages,
                "total_chunks": doc.total_chunks,
                "uploaded_at": doc.uploaded_at.isoformat()
            }
            for doc in docs
        ]
    finally:
        db.close()


@app.post("/process_pdf", response_model=ProcessPDFResponse)
async def process_pdf(file: UploadFile = File(...)):
    """
    Extract text from PDF file and return text chunks.

    The PDF is processed page-by-page, then all text is combined and split
    into overlapping chunks suitable for embeddings and retrieval.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    content = await file.read()

    try:
        # Extract text from PDF
        with pdfplumber.open(BytesIO(content)) as pdf:
            text_by_page = []
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    text_by_page.append({
                        "page": page_num,
                        "text": text
                    })

        # Combine all pages into single text
        full_text = " ".join([page["text"] for page in text_by_page])

        # Chunk the text
        chunks = chunk_text(
            full_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )

        # Save metadata to database
        db = SessionLocal()
        try:
            doc = Document(
                filename=file.filename,
                total_pages=len(text_by_page),
                total_chunks=len(chunks)
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            document_id = doc.id
        finally:
            db.close()

        # Build response
        return {
            "document_id": document_id,
            "filename": file.filename,
            "total_pages": len(text_by_page),
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "chunk_id": i,
                    "text": chunk,
                    "char_count": len(chunk)
                }
                for i, chunk in enumerate(chunks)
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )
