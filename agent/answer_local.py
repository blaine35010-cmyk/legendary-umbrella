import os
import json
import re
from typing import List

from sentence_transformers import SentenceTransformer

try:
    from index.simple_store import query as simple_query
except Exception:
    simple_query = None

try:
    import openai
except Exception:
    openai = None


MODEL_NAME = os.environ.get("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")


def embed(text: str):
    model = SentenceTransformer(MODEL_NAME)
    vec = model.encode([text], convert_to_numpy=True)
    return vec[0].tolist()


def get_retriever():
    # prefer simple_store for local
    if simple_query is not None:
        return simple_query
    raise RuntimeError("No local retriever available")


def build_prompt(question: str, contexts: List[dict]) -> str:
    ctx_texts = []
    for i, c in enumerate(contexts):
        meta = c.get("metadata", {})
        src = meta.get("file_path", meta.get("doc_id", "unknown"))
        chunk = c.get("document", "")
        ctx_texts.append(f"Source {i+1} ({src}):\n{chunk}\n")
    joined = "\n---\n".join(ctx_texts)
    prompt = (
        "You are an assistant helping summarize and answer questions using the provided document excerpts.\n"
        "Use only the information in the excerpts. If the answer is not contained, say you don't know.\n\n"
        f"Question: {question}\n\n"
        "Context excerpts:\n"
        f"{joined}\n\n"
        "Provide a concise answer (2-4 sentences) and list sources by number."
    )
    return prompt


def answer_with_openai(prompt: str) -> str:
    if openai is None:
        raise RuntimeError("openai package not installed")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai.api_key = key
    resp = openai.ChatCompletion.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.0,
    )
    return resp["choices"][0]["message"]["content"].strip()


def answer_local(
    question: str,
    collection: str = "court-files",
    top_k: int = 5,
    format_mode: str = "compact",
    path_contains: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    file_ext: str | None = None,
) -> str:
    # instantiate model once and compute question embedding
    model = SentenceTransformer(MODEL_NAME)
    qvec = model.encode([question], convert_to_numpy=True)[0]
    retriever = get_retriever()
    res = retriever(collection, qvec.tolist(), top_k=top_k)
    ids = res.get("ids", [])
    contexts = []
    import datetime
    import time

    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            return datetime.datetime.fromisoformat(s)
        except Exception:
            # try date-only
            return datetime.datetime.fromisoformat(s + "T00:00:00")

    dt_from = _parse_iso(date_from)
    dt_to = _parse_iso(date_to)

    for i, rid in enumerate(ids):
        md = res.get("metadatas", [])[i]
        doc_txt = res.get("documents", [])[i]
        fp = md.get("file_path", "")

        # apply path_contains filter if specified
        if path_contains:
            if path_contains not in fp:
                continue

        # apply file extension filter
        if file_ext:
            if not fp.lower().endswith(file_ext.lower()):
                continue

        # apply date filters (based on file mtime when available)
        if (dt_from or dt_to) and fp:
            mtime = None
            # try filesystem mtime first
            try:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            except Exception:
                mtime = None

            # fallback: check metadata returned by the vector store
            if mtime is None:
                try:
                    meta_m = md.get("modified_time") or md.get("mtime") or md.get("file_mtime")
                    if meta_m:
                        # stored as epoch float or int
                        mtime = datetime.datetime.fromtimestamp(float(meta_m))
                except Exception:
                    mtime = None

            # fallback: try loading raw JSON by doc_id from data/raw_docs
            if mtime is None:
                try:
                    doc_id = md.get("doc_id") or md.get("id")
                    if doc_id:
                        raw_path = os.path.join("data", "raw_docs", f"{doc_id}.json")
                        if os.path.exists(raw_path):
                            with open(raw_path, "r", encoding="utf-8") as f:
                                rawj = json.load(f)
                            raw_m = rawj.get("modified_time") or rawj.get("mtime") or rawj.get("file_mtime") or rawj.get("modified")
                            if raw_m:
                                mtime = datetime.datetime.fromtimestamp(float(raw_m))
                except Exception:
                    mtime = None

            if dt_from and mtime and mtime < dt_from:
                continue
            if dt_to and mtime and mtime > (dt_to + datetime.timedelta(days=1)):
                continue

        contexts.append({"id": rid, "metadata": md, "document": doc_txt})

    prompt = build_prompt(question, contexts)

    # if OpenAI available and configured, call it for a natural answer
    try:
        if openai is not None and os.environ.get("OPENAI_API_KEY"):
            return answer_with_openai(prompt)
    except Exception:
        pass

    # Fallback local summarization: re-rank contexts by similarity to question
    docs = [c.get("document", "")[:2000] for c in contexts]
    if docs:
        doc_embs = model.encode(docs, convert_to_numpy=True)
        # cosine similarities
        import numpy as _np

        norms = _np.linalg.norm(doc_embs, axis=1) * (_np.linalg.norm(qvec) + 1e-12)
        sims = (_np.dot(doc_embs, qvec)) / norms
        order = _np.argsort(-sims)
    else:
        order = []

    # build summary from top-ranked docs
    def first_sentence(text: str) -> str:
        s = text.replace("\n", " ").strip()
        parts = re.split(r'(?<=[.!?])\s+', s)
        return parts[0].strip() if parts and parts[0] else s[:200]

    summary_sentences = []
    for idx in order[:3]:
        fs = first_sentence(contexts[int(idx)].get("document", ""))
        if fs:
            summary_sentences.append(fs)

    if not summary_sentences and contexts:
        summary = contexts[0].get("document", "")[:300].replace("\n", " ")
    else:
        summary = " ".join(summary_sentences)[:1000]

    if format_mode == "detailed":
        # include short extracted snippets plus metadata
        snippets = []
        for rank, idx in enumerate(order[:5], start=1):
            c = contexts[int(idx)]
            md = c.get("metadata", {})
            fp = md.get("file_path", md.get("doc_id", "unknown"))
            chunk = c.get("document", "").replace("\n", " ")[:800]
            snippets.append(f"[{rank}] {fp} (chunk {md.get('chunk_index')}): {chunk}")
        answer = f"{summary}\n\nDetails:\n" + "\n\n".join(snippets)
    else:
        # compact: summary + numbered citations
        citations = []
        for i, idx in enumerate(order[:5], start=1):
            md = contexts[int(idx)].get("metadata", {})
            fp = md.get("file_path", md.get("doc_id", "unknown"))
            ci = md.get("chunk_index")
            citations.append(f"[{i}] {fp} (chunk {ci})")
        answer = f"{summary}\n\nSources:\n" + "\n".join(citations)

    return answer


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--question", required=True)
    p.add_argument("--collection", default="court-files")
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()
    out = answer_local(args.question, collection=args.collection, top_k=args.top_k)
    print(out)
