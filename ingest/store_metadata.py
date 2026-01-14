import os
import json
import hashlib
from typing import Dict


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def doc_id_for(path: str, mtime: float) -> str:
    h = hashlib.sha256(f"{path}|{mtime}".encode("utf-8")).hexdigest()
    return h


def save_doc_json(doc: Dict, out_dir: str = None) -> str:
    """Save the document dict as a JSON file in `data/raw_docs/` (relative to project root).
    Returns the path to the written JSON file."""
    root = out_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_docs")
    _ensure_dir(root)
    doc_id = doc.get("doc_id") or doc_id_for(doc.get("file_path", ""), doc.get("modified_time", 0))
    out_path = os.path.join(root, f"{doc_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return out_path


if __name__ == "__main__":
    print("store_metadata module")
