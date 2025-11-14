"""
Authentication middleware for API Gateway.
"""
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
import os
import logging

logger = logging.getLogger(__name__)

# Get API key from environment
API_KEY = os.getenv("API_KEY", "dev-key-change-in-production")

# Define the header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/health",
    "/metrics",  # Prometheus metrics endpoint
    "/docs",
    "/openapi.json",
    "/redoc"
}


def is_public_endpoint(path: str) -> bool:
    """Check if endpoint is public and doesn't require authentication."""
    # Check exact match
    if path in PUBLIC_ENDPOINTS:
        return True

    # Also allow static files for docs UI
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return True

    return False


async def verify_api_key(request: Request) -> None:
    """
    Verify API key from request header.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Skip authentication for public endpoints
    if is_public_endpoint(request.url.path):
        logger.debug(f"Skipping auth for public endpoint: {request.url.path}")
        return

    # Get API key from header
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        logger.warning(f"Missing API key for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    logger.debug(f"API key verified for {request.url.path}")
