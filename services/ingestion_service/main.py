from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
from io import BytesIO
from datetime import datetime
import os

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="Ingestion Service")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./documents.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Document(Base):
    """
    Stores metadata about processed documents.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    total_pages = Column(Integer)
    total_chunks = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap 

    return chunks

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion-service"}


@app.get("/documents")
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

@app.post("/process_pdf")
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
        # Extract text
        with pdfplumber.open(BytesIO(content)) as pdf:
            text_by_page = []
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text: 
                    text_by_page.append({
                        "page": page_num,
                        "text": text
                    })

        full_text = " ".join([page["text"] for page in text_by_page])

        chunks = chunk_text(full_text)

        # Save to database
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
