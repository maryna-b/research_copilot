from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import Annotated
import logging
import os

from config import settings
from database import get_db
from models import Document
from schemas import ProcessPDFResponse, DocumentListItem, SearchRequest, SearchResponse
from ingestion import process_pdf_file
from embeddings import search_chunks

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/health")
async def health():
    return {"status": "ok", "service": "research-copilot"}


@router.get("/info")
async def info():
    return {"name": "Research Copilot", "version": "0.2.0"}


@router.get("/documents", response_model=list[DocumentListItem])
async def list_documents(db: DbSession):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "total_pages": doc.total_pages,
            "total_chunks": doc.total_chunks,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
    ]


@router.post(
    "/upload",
    response_model=ProcessPDFResponse,
    responses={
        "400": {"description": "Invalid request (missing filename, invalid extension, or empty file)"},
        "413": {"description": "Uploaded file exceeds maximum allowed size"},
        "500": {"description": "Internal server error while processing upload"},
    },
)
async def upload(file: Annotated[UploadFile, File(...)], db: DbSession):
    logger.info("Upload started")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. Got: {ext}")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB",
        )

    result = process_pdf_file(file.filename, content, db)
    logger.info(f"Upload successful: {result['total_chunks']} chunks")
    return result


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        "404": {"description": "Search index not found. Upload a document first."},
        "500": {"description": "Internal server error while executing search"},
    },
)
async def search(request: SearchRequest):
    logger.info(f"Search started: query='{request.query}' n_results={request.n_results}")

    try:
        result = search_chunks(request.query, request.n_results)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed. Please try again.")

    logger.info(f"Search successful: {result.total_results} results")
    return result
