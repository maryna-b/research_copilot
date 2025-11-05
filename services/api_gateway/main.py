from fastapi import FastAPI, UploadFile, File, HTTPException
import httpx
import os

app = FastAPI(title="API Gateway")

INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8001")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}

@app.get("/info")
async def info():
    return {"name": "Research Copilot", "version": "0.1.0"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accept a file upload and forward it to the ingestion service for processing.
    Returns extracted text chunks from the PDF.
    """
    content = await file.read()

    # Forward to ingestion service
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            files = {"file": (file.filename, content, file.content_type)}

            response = await client.post(
                f"{INGESTION_SERVICE_URL}/process_pdf",
                files=files
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ingestion service error: {response.text}"
                )

            return response.json()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Could not connect to ingestion service: {str(e)}"
            )
