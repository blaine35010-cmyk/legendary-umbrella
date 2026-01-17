import os
import time
from typing import Optional

from .scan_files import scan_case_files
from .store_metadata import save_doc_json, doc_id_for


EXT_HANDLERS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}


def process_file(path: str) -> Optional[str]:
    """Process a single file: extract text + metadata and save JSON. Returns path to JSON file."""
    ext = os.path.splitext(path)[1].lower()
    handler = EXT_HANDLERS.get(ext)
    if not handler:
        return None

    doc = {"file_path": path, "file_name": os.path.basename(path)}

    try:
        st = os.stat(path)
        mtime = st.st_mtime
        doc.update({"modified_time": mtime, "size": st.st_size})
    except Exception:
        mtime = time.time()

    # Lazy imports and extraction
    text = ""
    meta = {}
    if handler == "pdf":
        try:
            from .extract_pdf import extract_text_from_pdf

            text, meta = extract_text_from_pdf(path)
        except Exception:
            text, meta = "", {"method": "failed"}

    elif handler == "docx":
        try:
            from .extract_docx import extract_text_from_docx

            text, meta = extract_text_from_docx(path)
        except Exception:
            text, meta = "", {"method": "failed"}

    elif handler == "image":
        try:
            from .extract_images import extract_text_from_image

            text, meta = extract_text_from_image(path)
        except Exception:
            text, meta = "", {"method": "failed"}

    elif handler == "text":
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            meta = {"method": "plain"}
        except Exception:
            text, meta = "", {"method": "failed"}

    # Assemble standardized doc
    doc_id = doc_id_for(path, mtime)
    doc_payload = {
        "doc_id": doc_id,
        "file_path": path,
        "file_name": os.path.basename(path),
        "doc_type": handler,
        "date": None,
        "parties": [],
        "raw_text": text,
        "source_metadata": meta,
        "modified_time": mtime,
    }

    out = save_doc_json(doc_payload)
    return out


def run_all(dry_run: bool = False):
    files = scan_case_files()
    results = []
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f}")
        if dry_run:
            results.append(None)
            continue
        try:
            out = process_file(f)
            print(" ->", out)
            results.append(out)
        except Exception as e:
            print(" failed:", e)
            results.append(None)
    return results


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Only list files, don't extract")
    args = p.parse_args()
    run_all(dry_run=args.dry_run)
