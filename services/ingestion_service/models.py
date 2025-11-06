"""
SQLAlchemy database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from database import Base


class Document(Base):
    """
    Stores metadata about processed documents.

    Attributes:
        id: Primary key
        filename: Original filename of uploaded document
        total_pages: Number of pages in the PDF
        total_chunks: Number of text chunks created
        uploaded_at: Timestamp when document was processed
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    total_pages = Column(Integer)
    total_chunks = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"
