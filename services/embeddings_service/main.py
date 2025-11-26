from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import chromadb
from openai import OpenAI

app = FastAPI(title="Embeddings Service", version="1.0.0")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

COLLECTION_NAME = "document_chunks"

# Pydantic models
class TextChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]

class EmbedRequest(BaseModel):
    chunks: List[TextChunk]

class EmbedResponse(BaseModel):
    success: bool
    chunks_embedded: int
    collection: str

class SearchRequest(BaseModel):
    query: str
    n_results: int = 5

class SearchResult(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    distance: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "embeddings-service"}

@app.post("/embed", response_model=EmbedResponse)
async def embed_chunks(request: EmbedRequest):
    """
    Generate embeddings for text chunks and store in Chroma
    """
    try:
        try:
            collection = chroma_client.get_collection(name=COLLECTION_NAME)
        except Exception:
            collection = chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Document text chunks with embeddings"}
            )

        texts = [chunk.text for chunk in request.chunks]
        ids = [chunk.chunk_id for chunk in request.chunks]
        metadatas = [chunk.metadata for chunk in request.chunks]

        # Generate embeddings using OpenAI
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        return EmbedResponse(
            success=True,
            chunks_embedded=len(request.chunks),
            collection=COLLECTION_NAME
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_chunks(request: SearchRequest):
    """
    Search for similar text chunks using semantic similarity
    """
    try:
        try:
            collection = chroma_client.get_collection(name=COLLECTION_NAME)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Collection '{COLLECTION_NAME}' not found. Please embed some documents first.")

        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=request.query
        )
        query_embedding = response.data[0].embedding

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.n_results
        )

        # Format results
        search_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                search_results.append(SearchResult(
                    chunk_id=results['ids'][0][i],
                    text=results['documents'][0][i],
                    metadata=results['metadatas'][0][i],
                    distance=results['distances'][0][i]
                ))

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
