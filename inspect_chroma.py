import chromadb
from collections import defaultdict

client = chromadb.HttpClient(host="localhost", port=8002)

collections = client.list_collections()
print(f"Collections: {[c.name for c in collections]}\n")

collection = client.get_collection("document_chunks")
total = collection.count()
print(f"Total chunks stored: {total}\n")

if total == 0:
    print("No chunks stored yet.")
    exit()

# Fetch all chunks (metadata + documents, no embeddings)
results = collection.get(include=["metadatas", "documents"])

# Group by document
docs = defaultdict(list)
for chunk_id, metadata, text in zip(results["ids"], results["metadatas"], results["documents"]):
    filename = metadata.get("filename", "unknown")
    docs[filename].append({
        "chunk_id": chunk_id,
        "chunk_index": metadata.get("chunk_index"),
        "total_chunks": metadata.get("total_chunks"),
        "text_preview": text[:150],
    })

print(f"Documents stored: {len(docs)}\n")
print("=" * 60)

for filename, chunks in docs.items():
    chunks.sort(key=lambda c: c["chunk_index"] or 0)
    print(f"File:         {filename}")
    print(f"Chunks:       {len(chunks)} / {chunks[0]['total_chunks']}")
    print(f"First chunk:  {chunks[0]['text_preview']}...")
    print("-" * 60)
