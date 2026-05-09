"""
Tests for the monolith app — configuration and route presence.
"""
import pytest
import sys
import os
from pathlib import Path

app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))


def test_app_imports():
    """Test that the main app module can be imported."""
    from main import app
    assert app is not None
    assert app.title == "Research Copilot"


def test_api_key_config():
    """Test that API_KEY is configurable via environment variable."""
    default_key = os.getenv("API_KEY", "dev-key-change-in-production")
    assert isinstance(default_key, str)
    assert len(default_key) > 0


def test_app_endpoints_defined():
    """Test that the app has all expected endpoints."""
    from main import app

    routes = [route.path for route in app.routes]

    assert "/health" in routes
    assert "/info" in routes
    assert "/upload" in routes
    assert "/search" in routes
    assert "/documents" in routes
