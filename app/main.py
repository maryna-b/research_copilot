from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import logging
import uuid
import time
from prometheus_fastapi_instrumentator import Instrumentator

from auth import verify_api_key
from database import Base, engine
from router import router

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


app.include_router(router)
