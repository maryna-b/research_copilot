from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    total_pages = Column(Integer)
    total_chunks = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"
