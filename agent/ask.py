import numpy as np
from sentence_transformers import SentenceTransformer
from index.simple_store import SimpleStore
import os
from openai import OpenAI

model = SentenceTransformer('all-MiniLM-L6-v2')

def ask(question, collection="court-files", top_k=10, format="compact", path_contains=None):
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
        # Truncate each chunk to 600 chars for context  
        chunk_text = result['text'][:600] + "..." if len(result['text']) > 600 else result['text']
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
                prompt = f"""You are an expert legal assistant specializing in Alabama family law and court procedures. Your role is to analyze court documents and provide informed, actionable guidance.

Analyze the provided court documents to answer the question. Guidelines:
- Synthesize information across multiple documents when relevant
- IMPORTANT: For trial planning requests, first identify the CORE DISPUTE (custody, visitation, child support, property division, contempt, etc.) from the documents
- Extract and highlight the substantive legal issues (not just procedural matters like hearing dates)
- Identify what each party is claiming/defending
- For trial preparation, organize with: Core Dispute, Your Party's Position, Opposing Position, Key Evidence Needed, Trial Strategy
- Reference specific dates, names, case numbers, and facts from the documents
- Provide practical, actionable recommendations based on Alabama law and the actual issues at stake
- If the question is vague about what's being disputed, analyze the documents to determine the actual dispute and provide comprehensive trial prep
- Be specific and direct, not vague

Court Documents:
{context}

Question: {question}"""
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.3
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
