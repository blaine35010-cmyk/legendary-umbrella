import os
from typing import List

try:
    import openai
except Exception:
    openai = None

from index.pinecone_client import query_index


def get_answer(question: str, index_name: str, top_k: int = 5) -> str:
    if openai is None:
        raise RuntimeError("openai package not installed")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set in env")
    openai.api_key = api_key

    # get question embedding
    emb = openai.Embedding.create(model="text-embedding-3-small", input=[question])
    qvec = emb["data"][0]["embedding"]

    res = query_index(index_name, qvec, top_k=top_k)
    hits = res.get("matches", [])
    contexts: List[str] = []
    for h in hits:
        md = h.get("metadata", {})
        contexts.append(f"Doc: {md.get('file_path')}\n{md.get('text_preview')}\n")

    prompt = (
        "You are an assistant that answers questions using the provided document excerpts.\n\n"
        + "Context:\n"
        + "\n---\n".join(contexts)
        + "\n\nQuestion: "
        + question
    )

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )
    return resp["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("question")
    p.add_argument("--index", default=os.environ.get("PINECONE_INDEX", "court-files"))
    args = p.parse_args()
    print(get_answer(args.question, args.index))
