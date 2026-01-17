import os
import json
from typing import List, Dict, Any
from pathlib import Path
import numpy as np


def _dir(name: str):
    base = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "vector_store"
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def upsert(collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]):
    d = _dir(collection_name)
    meta_path = d / "meta.json"
    emb_path = d / "embeddings.npy"

    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        existing_emb = np.load(emb_path)
    else:
        meta = {"ids": [], "metadatas": {}, "documents": {}}
        existing_emb = None

    # append
    for i, _id in enumerate(ids):
        meta["ids"].append(_id)
        meta["metadatas"][_id] = metadatas[i]
        meta["documents"][_id] = documents[i]

    # save meta
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh)

    embs = np.array(embeddings, dtype=np.float32)
    if existing_emb is None:
        all_emb = embs
    else:
        all_emb = np.vstack([existing_emb, embs])
    np.save(emb_path, all_emb)


def query(collection_name: str, embedding: List[float], top_k: int = 5):
    d = _dir(collection_name)
    meta_path = d / "meta.json"
    emb_path = d / "embeddings.npy"
    if not meta_path.exists() or not emb_path.exists():
        return {"ids": [], "metadatas": [], "documents": []}
    with open(meta_path, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    embs = np.load(emb_path)
    vec = np.array(embedding, dtype=np.float32)
    # cosine similarity
    embs_norm = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    vec_norm = vec / np.linalg.norm(vec)
    sims = embs_norm.dot(vec_norm)
    if len(sims) <= top_k:
        idx = sims.argsort()[::-1]
    else:
        idx = np.argpartition(-sims, top_k)[:top_k]
        idx = idx[np.argsort(-sims[idx])]
    result_ids = [meta["ids"][int(i)] for i in idx]
    metadatas = [meta["metadatas"][rid] for rid in result_ids]
    documents = [meta["documents"][rid] for rid in result_ids]
    return {"ids": result_ids, "metadatas": metadatas, "documents": documents}


if __name__ == "__main__":
    print("simple_store ready")
