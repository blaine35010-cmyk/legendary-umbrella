import pytest
from index.chunk_and_embed import chunk_text, embed_texts
from ingest.scan_files import scan_case_files
from agent.ask import ask

def test_chunk_text():
    text = "This is a test.\n\nThis is another paragraph."
    chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0
    assert "test" in chunks[0].lower()

def test_embed_texts():
    texts = ["Hello world", "Test embedding"]
    vectors = embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384  # all-MiniLM-L6-v2 dimension

def test_scan_case_files():
    # Assuming test files exist, but for CI, mock
    files = scan_case_files()
    assert isinstance(files, list)

def test_ask_no_data():
    result = ask("test question")
    assert "error" in result or "answer" in result