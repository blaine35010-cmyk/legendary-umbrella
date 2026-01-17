import os
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    chromadb = None


def get_client(persist_directory: str = None):
    if chromadb is None:
        raise RuntimeError("chromadb not installed. Install 'chromadb' to use local Chroma.")
    persist_directory = persist_directory or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma")
    settings = Settings(persist_directory=persist_directory, anonymized_telemetry=False)
    client = chromadb.Client(settings=settings)
    return client


def get_collection(name: str = "court-files"):
    client = get_client()
    try:
        coll = client.get_collection(name)
    except Exception:
        coll = client.create_collection(name)
    return coll


def upsert(collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]):
    coll = get_collection(collection_name)
    coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)


def query(collection_name: str, embedding: List[float], top_k: int = 5):
    coll = get_collection(collection_name)
    res = coll.query(query_embeddings=[embedding], n_results=top_k)
    return res


if __name__ == "__main__":
    print("chroma_client ready")
