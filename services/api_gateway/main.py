from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
import httpx
import os
import logging
import uuid
import time
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from auth import verify_api_key

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="0.1.0")

# Initialize Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],  # Don't track metrics endpoint itself
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument the app and expose metrics
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8001")

# File upload limits
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB default
ALLOWED_EXTENSIONS = {".pdf"}


@app.middleware("http")
async def authenticate_and_log(request: Request, call_next):
    """Authenticate requests and log with timing and request ID for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Add request_id to logging context
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)

    start_time = time.time()

    logger.info(f"Request started: {request.method} {request.url.path}")

    try:
        # Verify API key before processing request
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
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"error={str(e)} duration={process_time:.3f}s",
            exc_info=True
        )
        raise
    finally:
        logging.setLogRecordFactory(old_factory)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "ok", "service": "api-gateway"}


@app.get("/info")
async def info():
    """Service information endpoint."""
    logger.debug("Info requested")
    return {
        "name": "Research Copilot",
        "version": "0.1.0",
        "ingestion_service": INGESTION_SERVICE_URL
    }


def validate_file(file: UploadFile, content: bytes) -> None:
    """
    Validate uploaded file.

    Args:
        file: The uploaded file
        content: File content in bytes

    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    if not file.filename:
        logger.warning("Upload attempt with no filename")
        raise HTTPException(status_code=400, detail="Filename is required")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Upload attempt with invalid extension: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are allowed. Got: {file_ext}"
        )

    # Check file size
    file_size = len(content)
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"Upload attempt with oversized file: {file_size} bytes")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )

    if file_size == 0:
        logger.warning("Upload attempt with empty file")
        raise HTTPException(status_code=400, detail="File is empty")

    logger.info(f"File validation passed: {file.filename} ({file_size} bytes)")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accept a file upload and forward it to the ingestion service for processing.
    Returns extracted text chunks from the PDF.
    """
    logger.info(f"Upload started: {file.filename}")

    try:
        # Read file content
        content = await file.read()

        # Validate file
        validate_file(file, content)

        # Forward to ingestion service
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                files = {"file": (file.filename, content, file.content_type)}

                logger.info(f"Forwarding to ingestion service: {INGESTION_SERVICE_URL}")
                response = await client.post(
                    f"{INGESTION_SERVICE_URL}/process_pdf",
                    files=files
                )

                if response.status_code != 200:
                    logger.error(
                        f"Ingestion service error: status={response.status_code} "
                        f"detail={response.text}"
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="PDF processing failed. Please check the file and try again."
                    )

                result = response.json()
                logger.info(
                    f"Upload successful: {file.filename} - "
                    f"{result.get('total_chunks', 0)} chunks created"
                )
                return result

            except httpx.TimeoutException:
                logger.error(f"Timeout connecting to ingestion service: {INGESTION_SERVICE_URL}")
                raise HTTPException(
                    status_code=504,
                    detail="Processing timeout. The file may be too large or complex."
                )

            except httpx.RequestError as e:
                logger.error(f"Connection error to ingestion service: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable. Please try again later."
                )

    except HTTPException:
        # Re-raise HTTPExceptions (already logged)
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please contact support."
        )
