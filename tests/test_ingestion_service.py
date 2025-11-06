"""
Tests for Ingestion Service - Utility Functions.
"""
from pathlib import Path
import sys
import importlib.util

# Add ingestion_service directory to Python path so imports work
ingestion_service_dir = Path(__file__).parent.parent / "services" / "ingestion_service"
sys.path.insert(0, str(ingestion_service_dir))

# Load the ingestion service main module directly
ingestion_main_path = ingestion_service_dir / "main.py"
spec = importlib.util.spec_from_file_location("ingestion_main", ingestion_main_path)
ingestion_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingestion_main)

# Get the chunk_text function
chunk_text = ingestion_main.chunk_text


def test_chunk_text_function():
    """Test the chunk_text utility function."""

    text = "A" * 2500  # 2500 characters
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    # Should create 3 chunks
    assert len(chunks) == 3
    # First chunk should be 1000 chars
    assert len(chunks[0]) == 1000


def test_chunk_text_small():
    """Test chunking with text smaller than chunk size."""
    text = "Small text"
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_exact_size():
    """Test chunking when text is exactly chunk size."""
    text = "B" * 1000  # Exactly 1000 characters
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    # With overlap=100, algorithm creates 2 chunks even for exact size
    # Chunk 1: 0-1000, Chunk 2: 900-1000 (last 100 chars due to overlap)
    assert len(chunks) == 2
    assert len(chunks[0]) == 1000
    assert len(chunks[1]) == 100  # Only the remaining chars after overlap


def test_chunk_text_overlap():
    """Test that overlapping chunks contain expected overlap."""
    text = "ABCDEFGHIJ" * 150  # 1500 characters
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    # Should have 2 chunks
    assert len(chunks) == 2
    # Last 100 chars of first chunk should match first 100 of second chunk
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_text_empty():
    """Test chunking empty string."""
    text = ""
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")
