from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import logging
import uuid
import time
import os
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from auth import verify_api_key
from config import settings
from database import Base, engine, SessionLocal
from models import Document
from schemas import ProcessPDFResponse, DocumentListItem, SearchRequest, SearchResponse
from ingestion import process_pdf_file
from embeddings import search_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Research Copilot", version="0.2.0")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema.setdefault("components", {})["securitySchemes"] = {
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    }
    schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

ALLOWED_EXTENSIONS = {".pdf"}


@app.middleware("http")
async def authenticate_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)

    start_time = time.time()
    logger.info(f"Request started: {request.method} {request.url.path}")

    try:
        await verify_api_key(request)
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} duration={process_time:.3f}s"
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except HTTPException as e:
        process_time = time.time() - start_time
        logger.info(
            f"Request rejected: {request.method} {request.url.path} "
            f"status={e.status_code} duration={process_time:.3f}s"
        )
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"error={str(e)} duration={process_time:.3f}s",
            exc_info=True,
        )
        raise
    finally:
        logging.setLogRecordFactory(old_factory)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "research-copilot"}


@app.get("/info")
async def info():
    return {"name": "Research Copilot", "version": "0.2.0"}


@app.get("/documents", response_model=list[DocumentListItem])
async def list_documents():
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "total_pages": doc.total_pages,
                "total_chunks": doc.total_chunks,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
            for doc in docs
        ]
    finally:
        db.close()


@app.post("/upload", response_model=ProcessPDFResponse)
async def upload(file: UploadFile = File(...)):
    logger.info(f"Upload started: {file.filename}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. Got: {ext}")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB",
        )

    db = SessionLocal()
    try:
        result = process_pdf_file(file.filename, content, db)
    finally:
        db.close()

    logger.info(f"Upload successful: {file.filename} — {result['total_chunks']} chunks")
    return result


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    logger.info(f"Search started: query='{request.query}' n_results={request.n_results}")

    try:
        result = search_chunks(request.query, request.n_results)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed. Please try again.")

    logger.info(f"Search successful: {result.total_results} results")
    return result
