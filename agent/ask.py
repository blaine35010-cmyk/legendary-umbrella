import os
from typing import Optional

try:
    from agent.answer_question import get_answer as cloud_get_answer
except Exception:
    cloud_get_answer = None

try:
    from agent.answer_local import answer_local as local_answer
except Exception:
    local_answer = None


def ask(
    question: str,
    collection: str = "court-files",
    top_k: int = 5,
    format_mode: str = "compact",
    path_contains: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    file_ext: str | None = None,
) -> str:
    # Prefer cloud if OpenAI + Pinecone env vars are present and cloud code available
    openai_key = os.environ.get("OPENAI_API_KEY")
    pine_key = os.environ.get("PINECONE_API_KEY")
    pine_env = os.environ.get("PINECONE_ENV")
    if openai_key and pine_key and pine_env and cloud_get_answer is not None:
        try:
            return cloud_get_answer(question, index_name=collection, top_k=top_k)
        except Exception:
            pass

    # Fall back to local answer
    if local_answer is not None:
        return local_answer(
            question,
            collection=collection,
            top_k=top_k,
            format_mode=format_mode,
            path_contains=path_contains,
            date_from=date_from,
            date_to=date_to,
            file_ext=file_ext,
        )

    raise RuntimeError("No available QA backend (cloud or local)")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--question", required=True)
    p.add_argument("--collection", default="court-files")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--format", choices=["compact", "detailed"], default="compact", help="Output format: compact summary or detailed snippets")
    p.add_argument("--path-contains", default=None, help="Only consider documents whose file path contains this substring")
    p.add_argument("--date-from", default=None, help="ISO date (YYYY-MM-DD) to filter documents modified on/after this date")
    p.add_argument("--date-to", default=None, help="ISO date (YYYY-MM-DD) to filter documents modified on/before this date")
    p.add_argument("--file-ext", default=None, help="Filter by file extension, e.g. .pdf or .docx")
    args = p.parse_args()
    print(
        ask(
            args.question,
            collection=args.collection,
            top_k=args.top_k,
            format_mode=args.format,
            path_contains=args.path_contains,
            date_from=args.date_from,
            date_to=args.date_to,
            file_ext=args.file_ext,
        )
    )
