"""
Tests for text processing utilities.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from utils import chunk_text


def test_chunk_text_function():
    text = "A" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 3
    assert len(chunks[0]) == 1000


def test_chunk_text_small():
    text = "Small text"
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_exact_size():
    text = "B" * 1000
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 2
    assert len(chunks[0]) == 1000
    assert len(chunks[1]) == 100


def test_chunk_text_overlap():
    text = "ABCDEFGHIJ" * 150  # 1500 characters
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 2
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_text_empty():
    chunks = chunk_text("", chunk_size=1000, overlap=100)

    assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")


def test_chunk_text_sentence_boundary():
    # Natural cut at 1000 lands mid-word; sentence ends 5 chars later
    text = ("A" * 1000) + "end. " + ("B" * 500)
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert chunks[0].endswith("end. ")
    assert "B" in chunks[-1]
