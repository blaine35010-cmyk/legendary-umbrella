import os
import json
from typing import List, Dict, Any

from pathlib import Path

try:
    import openai
except Exception:
    openai = None

try:
    import tiktoken
except Exception:
    tiktoken = None

from config import settings as settings_module


def load_settings():
    return settings_module.load_settings()


def _count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    if tiktoken:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    # fallback heuristic
    return max(1, len(text) // 4)


def chunk_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 200) -> List[str]:
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""
    for p in paragraphs:
        if not current:
            current = p
            continue
        # estimate tokens
        if _count_tokens(current + "\n\n" + p) <= chunk_size:
            current = current + "\n\n" + p
        else:
            chunks.append(current)
            current = p
    if current:
        chunks.append(current)

    # enforce overlap by merging small boundaries
    final: List[str] = []
    for i, c in enumerate(chunks):
        if i == 0:
            final.append(c)
            continue
        prev = final[-1]
        # if previous + current small, merge
        if _count_tokens(prev) + _count_tokens(c) <= chunk_size:
            final[-1] = prev + "\n\n" + c
        else:
            final.append(c)
    return final


def embed_texts(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    if openai is None:
        raise RuntimeError("openai package not installed")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set in env")
    openai.api_key = api_key
    # batch embeddings
    resp = openai.Embedding.create(model=model, input=texts)
    vectors = [r["embedding"] for r in resp["data"]]
    return vectors


def index_all(json_dir: str, index_name: str, batch_size: int = 100):
    from index.pinecone_client import upsert_vectors

    settings = load_settings()
    chunk_size = settings.get("chunk_size", 1200)
    chunk_overlap = settings.get("chunk_overlap", 200)

    files = list(Path(json_dir).glob("*.json"))
    to_upsert: List[Dict[str, Any]] = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        text = doc.get("raw_text", "")
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            continue
        # create embeddings in batches
        for i in range(0, len(chunks), batch_size):
            batch_texts = chunks[i : i + batch_size]
            vectors = embed_texts(batch_texts)
            for j, vec in enumerate(vectors):
                cid = f"{doc.get('doc_id')}--{i+j}"
                meta = {
                    "doc_id": doc.get("doc_id"),
                    "file_path": doc.get("file_path"),
                    "chunk_index": i + j,
                    "text_preview": batch_texts[j][:300],
                }
                to_upsert.append({"id": cid, "values": vec, "metadata": meta})
        # upsert in batches to Pinecone
        if len(to_upsert) >= batch_size:
            upsert_vectors(index_name, to_upsert, batch_size=batch_size)
            to_upsert = []
    if to_upsert:
        upsert_vectors(index_name, to_upsert, batch_size=batch_size)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--json-dir", default="data/raw_docs")
    p.add_argument("--index", default=os.environ.get("PINECONE_INDEX", "court-files"))
    args = p.parse_args()
    index_all(args.json_dir, args.index)
