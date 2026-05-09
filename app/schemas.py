from typing import Any
from pydantic import BaseModel


class ChunkResponse(BaseModel):
    chunk_id: int
    text: str
    char_count: int


class ProcessPDFResponse(BaseModel):
    document_id: int
    filename: str
    total_pages: int
    total_chunks: int
    chunks: list[ChunkResponse]


class DocumentListItem(BaseModel):
    id: int
    filename: str
    total_pages: int
    total_chunks: int
    uploaded_at: str

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int
