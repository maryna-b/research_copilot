"""
Utility functions for text processing.
"""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks.

    This function creates overlapping chunks to preserve context across boundaries,
    which is important for semantic search and LLM processing.

    Args:
        text: The text to chunk
        chunk_size: Size of each chunk in characters (default: 1000)
        overlap: Number of characters to overlap between chunks (default: 100)

    Returns:
        List of text chunks

    Example:
        >>> text = "A" * 2500
        >>> chunks = chunk_text(text, chunk_size=1000, overlap=100)
        >>> len(chunks)
        3
        >>> len(chunks[0])
        1000
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks
