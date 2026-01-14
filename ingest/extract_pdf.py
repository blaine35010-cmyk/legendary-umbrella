import os
from typing import Tuple, Dict, Optional


def extract_metadata(path: str) -> Dict:
    st = os.stat(path)
    return {
        "file_path": path,
        "file_name": os.path.basename(path),
        "size": st.st_size,
        "modified_time": st.st_mtime,
    }


def extract_text_from_pdf(path: str, ocr_threshold: int = 200) -> Tuple[str, Dict]:
    """Extract text from PDF. Try pdfplumber first; if extracted text is small, fall back to OCR.

    Returns (text, metadata)
    """
    # Lazy imports so module can be imported even if dependencies aren't installed
    text = ""
    meta: Dict = {"method": None, "pages": 0}

    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            pages_text = []
            for p in pdf.pages:
                pg = p.extract_text()
                pages_text.append(pg or "")
            text = "\n".join(pages_text).strip()
            meta["pages"] = len(pdf.pages)
            if len(text) >= ocr_threshold:
                meta["method"] = "pdfplumber"
                return text, meta
    except Exception:
        # pdfplumber not available or failed — we'll try OCR
        text = ""

    # Fallback to OCR using pdf2image + pytesseract
    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(path)
        ocr_pages = []
        for img in images:
            ocr_pages.append(pytesseract.image_to_string(img))
        text = "\n".join(ocr_pages).strip()
        meta["method"] = "pytesseract"
        meta["pages"] = len(images)
        return text, meta
    except Exception:
        # If OCR also fails, return whatever we have and note failure
        if text:
            meta["method"] = meta.get("method") or "partial"
        else:
            meta["method"] = "failed"
        return text, meta


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingest/extract_pdf.py <path-to-pdf>")
        sys.exit(1)

    path = sys.argv[1]
    text, meta = extract_text_from_pdf(path)
    print(f"Method: {meta.get('method')}, pages: {meta.get('pages')}")
    print(text[:1000])
