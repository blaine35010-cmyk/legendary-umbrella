import os
from typing import Tuple, Dict


def extract_text_from_image(path: str) -> Tuple[str, Dict]:
    """Extract text from an image file using pytesseract. Returns (text, metadata)."""
    text = ""
    meta: Dict = {"method": None}
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(path)
        text = pytesseract.image_to_string(img).strip()
        meta["method"] = "pytesseract"
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
        print("Usage: python ingest/extract_images.py <path-to-image>")
        raise SystemExit(1)
    t, m = extract_text_from_image(sys.argv[1])
    print(m)
    print(t[:1000])
