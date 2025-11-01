from fastapi import FastAPI, UploadFile, File

app = FastAPI(title="API Gateway")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}

@app.get("/info")
async def info():
    return {"name": "Research Copilot", "version": "0.1.0"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accept a file upload and return basic metadata.
    Later, forward this to the ingestion service.
    """
    # Read file content to calculate size
    content = await file.read()
    size = len(content)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": size,
        "message": "File received successfully"
    }
