from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
from io import BytesIO

app = FastAPI(title="Ingestion Service")


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

        return {
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
