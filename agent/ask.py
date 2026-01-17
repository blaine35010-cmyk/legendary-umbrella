import numpy as np
from sentence_transformers import SentenceTransformer
from index.simple_store import SimpleStore
import os
from openai import OpenAI

model = SentenceTransformer('all-MiniLM-L6-v2')

def ask(question, collection="court-files", top_k=3, format="compact", path_contains=None):
    store_path = f"data/{collection}_embeddings.npy"
    metadata_path = f"data/{collection}_metadata.json"
    
    if not os.path.exists(store_path) or not os.path.exists(metadata_path):
        return {"error": f"Collection {collection} not found"}
    
    store = SimpleStore.load(store_path, metadata_path)
    
    question_embedding = model.encode([question])[0]
    
    results = store.search(question_embedding, top_k=top_k)
    
    context = ""
    sources = []
    
    for result in results:
        if path_contains and path_contains not in result['path']:
            continue
        # Truncate each chunk to 500 chars for context
        chunk_text = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
        context += chunk_text + "\n\n"
        sources.append({"path": result['path'], "chunk": result['chunk_id']})
    
    # Check if OpenAI API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)
        # Try GPT-4 first, fall back to GPT-3.5-turbo if access denied
        models_to_try = ["gpt-4", "gpt-3.5-turbo"]
        answer = None
        for model_name in models_to_try:
            try:
                prompt = f"You are a helpful assistant answering questions about court cases. Use the following context to answer the question accurately. If the context doesn't contain enough information, say so.\n\nContext:\n{context}\n\nQuestion: {question}"
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.1
                )
                answer = response.choices[0].message.content.strip()
                break  # Success, use this answer
            except Exception as e:
                error_str = str(e).lower()
                if "insufficient_quota" in error_str or "billing" in error_str:
                    # Quota issue, stop trying
                    answer = f"Error with OpenAI: {str(e)}. Falling back to retrieval.\n\n{context[:1000]}..."
                    break
                elif "model" in error_str and ("not found" in error_str or "access" in error_str):
                    # Model not accessible, try next
                    continue
                else:
                    # Other error, fall back
                    answer = f"Error with OpenAI: {str(e)}. Falling back to retrieval.\n\n{context[:1000]}..."
                    break
        if answer is None:
            # All models failed, fall back
            answer = f"Error with OpenAI: Unable to access any models. Falling back to retrieval.\n\n{context[:1000]}..."
    else:
        # Fallback to retrieval
        if format == "compact":
            answer = "\n\n".join([result['text'][:500] + "..." for result in results if not (path_contains and path_contains not in result['path'])])
        else:
            answer = "\n\n".join([result['text'] for result in results if not (path_contains and path_contains not in result['path'])])
    
    return {"answer": answer, "sources": sources}
