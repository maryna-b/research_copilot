from fastapi import Request, HTTPException, status
import logging

from config import settings

logger = logging.getLogger(__name__)

PUBLIC_ENDPOINTS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}


def is_public_endpoint(path: str) -> bool:
    if path in PUBLIC_ENDPOINTS:
        return True
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return True
    return False


async def verify_api_key(request: Request) -> None:
    if is_public_endpoint(request.url.path):
        return

    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
