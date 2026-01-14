import os
from typing import Tuple, Dict


def extract_text_from_docx(path: str) -> Tuple[str, Dict]:
    """Extract text from a .docx file. Returns (text, metadata)."""
    text = ""
    meta: Dict = {"method": None}
    try:
        from docx import Document

        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs]
        text = "\n".join(paragraphs).strip()
        meta["method"] = "python-docx"
    except Exception:
        meta["method"] = "failed"

    try:
        st = os.stat(path)
        meta.update({"size": st.st_size, "modified_time": st.st_mtime})
    except Exception:
        pass

    return text, meta


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingest/extract_docx.py <path-to-docx>")
        raise SystemExit(1)
    t, m = extract_text_from_docx(sys.argv[1])
    print(m)
    print(t[:1000])
