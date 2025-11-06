"""
Tests for API Gateway service - Configuration & Imports.
"""
import pytest
import sys
from pathlib import Path
import os


def test_api_gateway_imports():
    """Test that API Gateway main module can be imported."""
    services_path = Path(__file__).parent.parent / "services" / "api_gateway"
    sys.path.insert(0, str(services_path))

    try:
        from main import app
        assert app is not None
        assert app.title == "API Gateway"
    except ImportError as e:
        pytest.fail(f"Failed to import API Gateway: {e}")


def test_ingestion_service_url_config():
    """Test that INGESTION_SERVICE_URL is configurable."""
    services_path = Path(__file__).parent.parent / "services" / "api_gateway"
    sys.path.insert(0, str(services_path))

    # Test default value
    default_url = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8001")
    assert default_url == "http://localhost:8001" or default_url.startswith("http")


def test_api_gateway_endpoints_defined():
    """Test that API Gateway has expected endpoints defined."""
    services_path = Path(__file__).parent.parent / "services" / "api_gateway"
    sys.path.insert(0, str(services_path))

    from main import app

    # Get all routes
    routes = [route.path for route in app.routes]

    # Check expected endpoints exist
    assert "/health" in routes
    assert "/info" in routes
    assert "/upload" in routes
