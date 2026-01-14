import os
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

from config import settings as settings_module


def _get_upsert():
    # prefer chroma if available, otherwise fall back to annoy
    # prefer chroma if truly available
    try:
        import index.chroma_client as chroma_mod
        if getattr(chroma_mod, "chromadb", None) is not None:
            return chroma_mod.upsert
    except Exception:
        pass
    # try annoy (only if compiled dependency is present)
    try:
        import index.annoy_client as annoy_mod
        if getattr(annoy_mod, "AnnoyIndex", None) is not None:
            return annoy_mod.upsert
    except Exception:
        pass
    # final fallback: simple numpy-based store
    try:
        from index.simple_store import upsert as simple_upsert
        return simple_upsert
    except Exception:
        raise RuntimeError("No vector DB backend available (chromadb, annoy, or simple_store)")


def load_settings():
    return settings_module.load_settings()


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
        if len(current) + len(p) <= chunk_size * 4:  # rough char heuristic
            current = current + "\n\n" + p
        else:
            chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed")
    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return vectors.tolist()


def index_all_to_chroma(json_dir: str = "data/raw_docs", collection: str = "court-files", sample_limit: int = None):
    settings = load_settings()
    chunk_size = settings.get("chunk_size", 1200)
    chunk_overlap = settings.get("chunk_overlap", 200)

    files = list(Path(json_dir).glob("*.json"))
    if sample_limit:
        files = files[:sample_limit]

    ids_batch: List[str] = []
    emb_batch: List[List[float]] = []
    meta_batch: List[Dict[str, Any]] = []
    doc_batch: List[str] = []

    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        text = doc.get("raw_text", "")
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            continue
        vectors = embed_texts(chunks)
        for i, v in enumerate(vectors):
            cid = f"{doc.get('doc_id')}--{i}"
            ids_batch.append(cid)
            emb_batch.append(v)
            meta_batch.append({"doc_id": doc.get("doc_id"), "file_path": doc.get("file_path"), "chunk_index": i})
            doc_batch.append(chunks[i][:1000])

    if ids_batch:
        upsert_fn = _get_upsert()
        upsert_fn(collection, ids_batch, emb_batch, meta_batch, doc_batch)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json-dir", default="data/raw_docs")
    p.add_argument("--collection", default="court-files")
    p.add_argument("--sample", type=int, default=50, help="Number of documents to index (for testing)")
    args = p.parse_args()
    index_all_to_chroma(args.json_dir, collection=args.collection, sample_limit=args.sample)
