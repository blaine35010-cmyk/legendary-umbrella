import argparse
from sentence_transformers import SentenceTransformer
from index.simple_store import query as simple_query


def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    vec = model.encode([text], convert_to_numpy=True)
    return vec[0].tolist()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--question", required=True)
    p.add_argument("--collection", default="court-files")
    args = p.parse_args()

    qvec = embed_text(args.question)
    res = simple_query(args.collection, qvec, top_k=5)
    print(f"Top {len(res.get('ids', []))} results for: {args.question}\n")
    for i, rid in enumerate(res.get("ids", [])):
        md = res["metadatas"][i]
        doc = res["documents"][i]
        print(f"{i+1}. id={rid} chunk_index={md.get('chunk_index')} file={md.get('file_path')}")
        print(doc[:800].replace('\n',' ') + "\n---\n")


if __name__ == "__main__":
    main()
