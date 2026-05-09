import pdfplumber
from io import BytesIO
from fastapi import HTTPException

from config import settings
from models import Document
from utils import chunk_text
from embeddings import embed_chunks


def process_pdf_file(filename: str, content: bytes, db) -> dict:
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            text_by_page = []
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    text_by_page.append({"page": page_num, "text": text})

        full_text = " ".join([p["text"] for p in text_by_page])
        chunks = chunk_text(full_text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)

        doc = Document(filename=filename, total_pages=len(text_by_page), total_chunks=len(chunks))
        db.add(doc)
        db.commit()
        db.refresh(doc)
        document_id = doc.id

        embed_payload = [
            {
                "chunk_id": f"{document_id}_chunk_{i}",
                "text": chunk,
                "metadata": {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]

        try:
            embed_chunks(embed_payload)
        except Exception as e:
            # Embedding failure is non-fatal — document metadata is already saved
            print(f"Warning: Failed to generate embeddings: {e}")

        return {
            "document_id": document_id,
            "filename": filename,
            "total_pages": len(text_by_page),
            "total_chunks": len(chunks),
            "chunks": [
                {"chunk_id": i, "text": chunk, "char_count": len(chunk)}
                for i, chunk in enumerate(chunks)
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
