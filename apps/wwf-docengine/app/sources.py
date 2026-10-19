# docengine.app.sources — the text of a file uploaded to a Document Brief (Head of QC, 18.10.2026: "option to upload
# documents in .docx or .pdf or .json or .md format as sources in any stage of the questionare").
#
# Only text is kept: it is what the authors read and cite by file name. A scanned PDF has no text layer and says so;
# it is never OCR'd here.
from __future__ import annotations

import io
import json
from pathlib import PurePath

MAX_BYTES = 15 * 1024 * 1024
KINDS = {".docx": "docx", ".pdf": "pdf", ".json": "json", ".md": "md", ".markdown": "md", ".txt": "md"}


class SourceError(ValueError):
    pass


def kind_of(name: str) -> str:
    k = KINDS.get(PurePath(name).suffix.lower())
    if not k:
        raise SourceError(f"{name}: only .docx, .pdf, .json and .md are accepted")
    return k


def _docx(blob: bytes) -> str:
    from docx import Document
    d = Document(io.BytesIO(blob))
    out = [p.text for p in d.paragraphs if p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                out.append(" | ".join(cells))
    return "\n".join(out)


def _pdf(blob: bytes) -> str:
    from pypdf import PdfReader
    pages = [(p.extract_text() or "").strip() for p in PdfReader(io.BytesIO(blob)).pages]
    return "\n\n".join(f"[page {i}]\n{t}" for i, t in enumerate(pages, 1) if t)


def extract(name: str, blob: bytes) -> str:
    """The text of one uploaded file. Raises SourceError for a type not accepted, a file too large, or a file that
    cannot be read; returns "" for a PDF without a text layer (a scan)."""
    if len(blob) > MAX_BYTES:
        raise SourceError(f"{name}: larger than {MAX_BYTES // (1024 * 1024)} MB")
    k = kind_of(name)
    try:
        if k == "docx":
            return _docx(blob)
        if k == "pdf":
            return _pdf(blob)
        text = blob.decode("utf-8-sig")
        return json.dumps(json.loads(text), ensure_ascii=False, indent=1) if k == "json" else text
    except SourceError:
        raise
    except Exception as e:  # noqa: BLE001 — a broken upload is reported, never stored half-read
        raise SourceError(f"{name}: cannot be read as {k} ({type(e).__name__})") from e
