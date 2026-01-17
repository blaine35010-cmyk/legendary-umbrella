import numpy as np
from sentence_transformers import SentenceTransformer
from index.simple_store import SimpleStore
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

def ask(question, collection="court-files", top_k=5, format="compact", path_contains=None):
    store_path = f"data/{collection}_embeddings.npy"
    metadata_path = f"data/{collection}_metadata.json"
    
    if not os.path.exists(store_path) or not os.path.exists(metadata_path):
        return {"error": f"Collection {collection} not found"}
    
    store = SimpleStore.load(store_path, metadata_path)
    
    question_embedding = model.encode([question])[0]
    
    results = store.search(question_embedding, top_k=top_k)
    
    answer = ""
    sources = []
    
    for result in results:
        if path_contains and path_contains not in result['path']:
            continue
        if format == "compact":
            answer += result['text'][:500] + "...\n\n"
        else:
            answer += result['text'] + "\n\n"
        sources.append({"path": result['path'], "chunk": result['chunk_id']})
    
    return {"answer": answer.strip(), "sources": sources}
