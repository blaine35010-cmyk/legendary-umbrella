import os
from typing import List, Dict, Any

try:
    import pinecone
except Exception:
    pinecone = None


def init_pinecone():
    if pinecone is None:
        raise RuntimeError("pinecone client not installed. Install 'pinecone-client' to use Pinecone.")
    api_key = os.environ.get("PINECONE_API_KEY")
    env = os.environ.get("PINECONE_ENV")
    if not api_key or not env:
        raise RuntimeError("PINECONE_API_KEY and PINECONE_ENV must be set in env to initialize Pinecone")
    pinecone.init(api_key=api_key, environment=env)


def get_index(index_name: str, dimension: int = 1536):
    init_pinecone()
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=dimension)
    return pinecone.Index(index_name)


def upsert_vectors(index_name: str, vectors: List[Dict[str, Any]], batch_size: int = 100):
    idx = get_index(index_name)
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        # each vector must be tuple (id, vector, metadata)
        to_upsert = [(v["id"], v["values"], v.get("metadata")) for v in batch]
        idx.upsert(to_upsert)


def query_index(index_name: str, vector: List[float], top_k: int = 5, include_metadata: bool = True):
    idx = get_index(index_name)
    res = idx.query(vector=vector, top_k=top_k, include_metadata=include_metadata)
    return res


if __name__ == "__main__":
    print("pinecone_client module")
