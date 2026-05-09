import re

_SENTENCE_END = re.compile(r'[.!?]\s')


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks, snapping boundaries to sentence ends.

    After the character-count cut point, looks ahead up to 200 chars for the
    nearest sentence boundary (.!? followed by whitespace) to avoid splitting
    mid-sentence. Falls back to exact character cut if none is found.
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            lookahead_end = min(end + 200, len(text))
            match = _SENTENCE_END.search(text, end, lookahead_end)
            if match:
                end = match.end()

        chunks.append(text[start:end])
        start = end - overlap

    return chunks