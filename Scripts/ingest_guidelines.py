"""Ingest guideline PDFs/TXT/MD from data/guidelines into ChromaDB.

Usage (from project root):
    venv\Scripts\python scripts/ingest_guidelines.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.rag import GUIDELINE_DIR, ingest_text


def _extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        text = ""
        # Try PyMuPDF first
        try:
            import fitz
            doc = fitz.open(path)
            pages = [page.get_text() for page in doc]
            doc.close()
            text = "\n\n".join(pages)
        except Exception:
            pass

        # Fallback to pdfplumber
        if not text.strip():
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    pages = [page.extract_text() or "" for page in pdf.pages]
                text = "\n\n".join(pages)
            except Exception:
                pass

        # Fallback to PyPDF2
        if not text.strip():
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(path))
                pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n\n".join(pages)
            except Exception:
                pass

        if not text.strip():
            raise RuntimeError(f"Could not extract text from PDF: {path.name}")
        return text

    return path.read_text(encoding="utf-8", errors="ignore")


def main():
    GUIDELINE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        f for f in GUIDELINE_DIR.iterdir()
        if f.suffix.lower() in (".pdf", ".txt", ".md")
    )
    if not files:
        print(f"No PDF/TXT files found in {GUIDELINE_DIR}.")
        print("Drop 2-5 public guideline documents there (see README notes), then re-run.")
        return

    total = 0
    for f in files:
        try:
            n = ingest_text(_extract_text(f), source=f.name)
            total += n
            print(f"  {f.name}: {n} chunks")
        except Exception as exc:
            print(f"  {f.name}: FAILED ({exc})")

    print(f"Done. {total} chunks stored in data/chroma_db.")


if __name__ == "__main__":
    main()
