# backend/utils/chunker.py

from typing import List

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Splits text into overlapping chunks.
    
    Args:
        text (str): The input text to split.
        chunk_size (int): Maximum size of each chunk.
        overlap (int): Number of characters to overlap between chunks.
    
    Returns:
        List[str]: List of text chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap if chunk_size > overlap else chunk_size

    return chunks
