import os
import json
from typing import List, Dict, Any
from pathlib import Path

try:
    from annoy import AnnoyIndex
except Exception:
    AnnoyIndex = None


def _collection_dir(name: str):
    base = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "annoy"
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def upsert(collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]):
    if AnnoyIndex is None:
        raise RuntimeError("annoy not installed")
    if not embeddings:
        return
    dim = len(embeddings[0])
    d = _collection_dir(collection_name)
    meta_path = d / "meta.json"

    # load existing metadata
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
    else:
        meta = {"ids": [], "metadatas": {}, "documents": {}}

    start_index = len(meta["ids"])
    # append new items
    for i, _id in enumerate(ids):
        meta["ids"].append(_id)
        meta["metadatas"][_id] = metadatas[i]
        meta["documents"][_id] = documents[i]

    # save metadata
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh)

    # build annoy index from all embeddings (we'll store embeddings on disk)
    emb_path = d / "embeddings.json"
    if emb_path.exists():
        with open(emb_path, "r", encoding="utf-8") as fh:
            existing = json.load(fh)
    else:
        existing = []
    existing.extend(embeddings)
    with open(emb_path, "w", encoding="utf-8") as fh:
        json.dump(existing, fh)

    # build Annoy index
    idx = AnnoyIndex(dim, "angular")
    for i, vec in enumerate(existing):
        idx.add_item(i, vec)
    idx.build(10)
    idx.save(str(d / "index.ann"))


def query(collection_name: str, embedding: List[float], top_k: int = 5):
    if AnnoyIndex is None:
        raise RuntimeError("annoy not installed")
    d = _collection_dir(collection_name)
    meta_path = d / "meta.json"
    emb_path = d / "embeddings.json"
    idx_path = d / "index.ann"
    if not idx_path.exists():
        return {"ids": [], "metadatas": [], "documents": []}
    with open(meta_path, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    with open(emb_path, "r", encoding="utf-8") as fh:
        embeddings = json.load(fh)
    dim = len(embeddings[0])
    idx = AnnoyIndex(dim, "angular")
    idx.load(str(idx_path))
    ids = idx.get_nns_by_vector(embedding, top_k, include_distances=False)
    result_ids = [meta["ids"][i] for i in ids]
    metadatas = [meta["metadatas"][rid] for rid in result_ids]
    documents = [meta["documents"][rid] for rid in result_ids]
    return {"ids": result_ids, "metadatas": metadatas, "documents": documents}


if __name__ == "__main__":
    print("annoy_client ready")
