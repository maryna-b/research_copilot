"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from pydantic import BaseModel


class ChunkResponse(BaseModel):
    """Schema for a single text chunk in response."""
    chunk_id: int
    text: str
    char_count: int


class ProcessPDFResponse(BaseModel):
    """Schema for PDF processing response."""
    document_id: int
    filename: str
    total_pages: int
    total_chunks: int
    chunks: list[ChunkResponse]


class DocumentListItem(BaseModel):
    """Schema for document in list response."""
    id: int
    filename: str
    total_pages: int
    total_chunks: int
    uploaded_at: str  # ISO format datetime string

    class Config:
        from_attributes = True  # Allows creation from SQLAlchemy models


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    service: str
