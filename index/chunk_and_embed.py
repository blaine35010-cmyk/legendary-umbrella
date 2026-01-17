import os
import json
from typing import List, Dict, Any

from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings as settings_module


def load_settings():
    return settings_module.load_settings()


def _count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    # simple heuristic
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


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def index_all(json_dir: str, index_name: str, batch_size: int = 100):
    settings = load_settings()
    chunk_size = settings.get("chunk_size", 1200)
    chunk_overlap = settings.get("chunk_overlap", 200)

    files = list(Path(json_dir).glob("*.json"))
    all_embeddings = []
    all_metadata = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        text = doc.get("raw_text", "")
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            continue
        # create embeddings
        vectors = embed_texts(chunks)
        for j, vec in enumerate(vectors):
            meta = {
                "text": chunks[j],
                "path": doc.get("file_path"),
                "chunk_id": f"{doc.get('doc_id')}--{j}",
                "doc_id": doc.get("doc_id"),
            }
            all_embeddings.append(vec)
            all_metadata.append(meta)

    # save to files
    embeddings_path = f"data/{index_name}_embeddings.npy"
    metadata_path = f"data/{index_name}_metadata.json"
    np.save(embeddings_path, np.array(all_embeddings, dtype=np.float32))
    with open(metadata_path, "w", encoding="utf-8") as fh:
        json.dump(all_metadata, fh)
    print(f"Saved {len(all_embeddings)} embeddings to {embeddings_path} and metadata to {metadata_path}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--json-dir", default="data/raw_docs")
    p.add_argument("--index", default="court-files")
    args = p.parse_args()
    index_all(args.json_dir, args.index)
