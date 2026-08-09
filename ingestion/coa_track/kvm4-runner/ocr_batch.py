#!/usr/bin/env python3
"""
ocr_batch.py — OCR a tree of scanned CoA PDFs with GPT-4o vision.

Single model, no fallback chain, no quota juggling: every page goes to gpt-4o.
Verified on Macedonian Cyrillic Certificates of Analysis (Farmahem and UKIM
Center for Natural Products): zero Cyrillic-character errors and faithful
transcription of cannabinoid result tables, batch numbers, signatories and
laboratory identifiers.

One request per PDF page (the OpenAI vision API does not accept multi-image
requests as efficiently as Gemini does); pages of one PDF are concatenated
into a single .txt with explicit "page break" markers.  Resumable: a PDF
whose .txt already exists and is non-empty is skipped, so a re-run only
fills gaps.  Every file's outcome is appended to ocr_manifest.jsonl.

Env:
    OPENAI_API_KEY   required
Usage:
    python3 ocr_batch.py <SRC_DIR> <OUT_DIR>
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF

DPI = int(os.environ.get("OCR_DPI", "200"))
MODEL = "gpt-4o"
MAX_TOKENS = int(os.environ.get("OCR_MAX_TOKENS", "4096"))

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

PROMPT = (
    "Transcribe ALL text from this scanned pharmaceutical Certificate of Analysis page "
    "verbatim, preserving Macedonian Cyrillic, English, table layouts (as markdown tables), "
    "numerical values, units, and laboratory report identifiers exactly as shown. "
    "Do not summarise. Do not translate. If a character is unreadable, write [?]."
)


def render_pages(pdf_path: Path) -> list[bytes]:
    doc = fitz.open(pdf_path)
    return [doc[i].get_pixmap(dpi=DPI).tobytes("png") for i in range(doc.page_count)]


def ocr_page(client, png: bytes) -> str:
    b64 = base64.b64encode(png).decode()
    resp = client.chat.completions.create(
        model=MODEL, max_tokens=MAX_TOKENS, temperature=0,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{b64}", "detail": "high"}},
        ]}],
    )
    return resp.choices[0].message.content or ""


def ocr_pdf(client, pngs: list[bytes]) -> str:
    parts = []
    for i, png in enumerate(pngs, 1):
        for attempt in range(3):
            try:
                parts.append(f"[page {i}]\n" + ocr_page(client, png))
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    parts.append(f"[page {i} OCR FAILED: {e}]")
                else:
                    time.sleep(4 * (attempt + 1))
    return "\n\n----- page break -----\n\n".join(parts)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    if not OPENAI_KEY:
        print("ERROR: OPENAI_API_KEY must be set")
        return 1
    import openai
    client = openai.OpenAI(api_key=OPENAI_KEY)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "ocr_manifest.jsonl"

    pdfs = sorted(p for p in src.rglob("*.pdf"))
    print(f"found {len(pdfs)} PDFs under {src}")
    print(f"model: {MODEL} (single-model, no fallback)")
    done = skipped = failed = 0
    t_start = time.time()

    for idx, pdf in enumerate(pdfs, 1):
        rel = pdf.relative_to(src)
        target = out / rel.with_suffix(".txt")
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        try:
            pngs = render_pages(pdf)
            text = ocr_pdf(client, pngs)
            target.write_text(text, encoding="utf-8")
            el = round(time.time() - t0, 1)
            rec = {"file": str(rel), "pages": len(pngs), "chars": len(text),
                   "model": MODEL, "elapsed_s": el, "ok": True}
            done += 1
            print(f"[{idx}/{len(pdfs)}] {rel}  {len(pngs)}p {len(text)}ch {el}s")
        except Exception as e:  # noqa: BLE001
            rec = {"file": str(rel), "ok": False, "error": str(e)[:300]}
            failed += 1
            print(f"[{idx}/{len(pdfs)}] {rel}  FAILED: {e}")
        with manifest.open("a", encoding="utf-8") as mf:
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nDONE in {round(time.time()-t_start,1)}s: {done} ocr'd, {skipped} skipped, {failed} failed")
    print(f"output: {out}\nmanifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
