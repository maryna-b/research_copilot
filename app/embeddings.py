import chromadb
from openai import OpenAI

from config import settings
from schemas import SearchResult, SearchResponse

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

COLLECTION_NAME = "document_chunks"

_chroma_client = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return _chroma_client


def _get_or_create_collection():
    client = _get_chroma_client()
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Document text chunks with embeddings"}
        )


def embed_chunks(chunks: list[dict]) -> dict:
    collection = _get_or_create_collection()

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    response = openai_client.embeddings.create(model="text-embedding-3-small", input=texts)
    embeddings = [item.embedding for item in response.data]

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    return {"success": True, "chunks_embedded": len(chunks), "collection": COLLECTION_NAME}


def search_chunks(query: str, n_results: int = 5) -> SearchResponse:
    try:
        collection = _get_chroma_client().get_collection(name=COLLECTION_NAME)
    except Exception:
        raise ValueError(f"Collection '{COLLECTION_NAME}' not found. Upload a document first.")

    response = openai_client.embeddings.create(model="text-embedding-3-small", input=query)
    query_embedding = response.data[0].embedding

    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    search_results = []
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            search_results.append(SearchResult(
                chunk_id=results["ids"][0][i],
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                distance=distance,
                similarity=round(1 / (1 + distance), 4),
            ))

    return SearchResponse(query=query, results=search_results, total_results=len(search_results))
