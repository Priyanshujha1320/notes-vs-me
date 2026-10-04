from __future__ import annotations
"""Turn PDFs into clean, retrievable chunks. PDFs only — no cloud OCR."""
import fitz  # PyMuPDF


def extract_text(pdf_bytes: bytes) -> str:
    pages = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            pages.append(page.get_text("text"))
    return "\n".join(pages)


def chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    """Paragraph-aware chunking; falls back to a sliding window."""
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
    if not paragraphs:
        paragraphs = [text]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > size and current:
            chunks.append(current.strip())
            current = current[-overlap:] if overlap else ""
        if len(para) > size:
            # a single monster paragraph: slide a window over it
            for i in range(0, len(para), size - overlap):
                piece = para[i:i + size]
                if len(piece) > 100:
                    chunks.append(piece)
            current = ""
        else:
            current = f"{current}\n{para}".strip()
    if len(current.strip()) > 100:
        chunks.append(current.strip())
    return chunks
