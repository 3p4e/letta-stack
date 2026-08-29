#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registered Letta-host tool: OCR a scanned certificate with a vision model.

This file is the version-controlled copy of a tool that lives on the Letta host, where it
is registered as `pp_ocr_scanned_pdf` (tool-dfe0dabf-9134-4d22-bc41-0c4b4f553705). The host
is the right home for it: that is where the RAG lives, where the OpenAI credentials are,
and where an ingested file has to end up. This copy exists so the source is reviewable and
can be re-registered if the host is rebuilt.

Why a vision model rather than tesseract
----------------------------------------
The Purely Plant certificates that were never ingested are CamScanner captures — a single
JPEG per page, no text layer at all. A filename search cannot see them, a text extractor
returns nothing but the CamScanner watermark, and that is exactly how GG1024's in-house
CoA sat unnoticed in Drive while its batch showed zero rows in the register.

Neither this container nor the Letta host has tesseract, poppler or ocrmypdf, and the
documents are Macedonian Cyrillic mixed with Latin chemical symbols, Greek letters and
superscripts — the case classical OCR handles worst. A vision model reads them directly
and needs no system packages. Only PyMuPDF had to be added, installed into the host's
existing vendored library directory (/root/.letta/pp-libs) rather than the system Python.

Host prerequisites, all verified present
----------------------------------------
    OPENAI_API_KEY, OPENAI_API_BASE   environment of the tool sandbox
    pymupdf 1.28.2                    pip install --target /root/.letta/pp-libs pymupdf
    openai 2.25.0, requests, PIL      already present

Fidelity
--------
The prompt carries the register's governing rule: transcribe what the paper says and never
improve it. Verified end-to-end against GG1024.pdf, whose values then matched the 29
register rows exactly.

One normalisation is deliberate. A vision model returns Cyrillic homoglyphs for Latin
chemical symbols — "ТНС" where the document prints "THC" — because the surrounding text is
Cyrillic. That is an artefact of the reader, not a feature of the document, so the prompt
pins chemical and unit symbols to Latin. Everything else, including misprints and
self-contradictory results, is copied as printed.

Usage
-----
Invoke on the host through letta_tool_manager.run_from_source, fetching this source from
the Letta API by name so it need not be re-sent:

    pp_ocr_scanned_pdf(
        pdf_url="https://drive.google.com/uc?export=download&id=<FILE_ID>",
        pdf_b64="", pages="all", model="gpt-4o", dpi=220,
        save_as="<batch>_ocr.txt")

pdf_url works for any Drive file shared with "anyone with the link" (the CoA folders are).
For a private file, pass the bytes as pdf_b64 instead.
"""


def pp_ocr_scanned_pdf(pdf_url: str, pdf_b64: str, pages: str, model: str, dpi: int,
                       save_as: str) -> str:
    """Transcribe a scanned, image-only PDF into text using a vision model on the Letta host.

    Built for the Purely Plant outsourced-laboratory certificates, which are CamScanner
    captures with no text layer: nothing in a filename search or a text extractor can see
    them, so they have to be read as pictures. PyMuPDF rasterises each page and an OpenAI
    vision model transcribes it.

    The prompt holds the register's governing rule — transcribe what the paper says and
    never improve it. A misprinted control-book number, a result that contradicts itself,
    a criterion that disagrees with the current monograph: all are copied as printed, and
    anything unreadable is marked [illegible] rather than guessed. The one normalisation
    allowed is Latin/Cyrillic homoglyphs on chemical symbols — a vision model will happily
    return Cyrillic "ТНС" for the Latin "THC" the document actually prints, and that is an
    OCR artefact, not the document.

    Output uses the transcription shape established by the ImB_QC_COAs corpus
    (that Letta source was retired 19.08.2026 — do not upload to a Letta source;
    per server/runbooks/ingestion_policy.md the target is RAGFlow):

        [page 1]
        ...text...
        ----- page break -----

    Args:
        pdf_url: URL the host can fetch the PDF from. Empty string if passing bytes.
        pdf_b64: base64-encoded PDF bytes. Empty string if passing a URL.
        pages: page range such as "1-4", "2", or "all".
        model: vision-capable model id, e.g. gpt-4o. gpt-4o reads these best.
        dpi: rasterisation resolution; 200 is enough for these scans, 300 for faint ones.
        save_as: filename to write under /root/.letta/pp-stage, or "" to skip saving.
    """
    import base64
    import io
    import os
    import re
    import sys

    if "/root/.letta/pp-libs" not in sys.path:
        sys.path.insert(0, "/root/.letta/pp-libs")

    import pymupdf
    import requests
    from openai import OpenAI

    if pdf_b64:
        raw = base64.b64decode(pdf_b64)
    elif pdf_url:
        rr = requests.get(pdf_url, timeout=180, allow_redirects=True)
        rr.raise_for_status()
        raw = rr.content
        if raw[:5] != b"%PDF-":
            head = raw[:400].decode("utf-8", "replace")
            return ("ERROR: URL did not return a PDF (got %d bytes starting %r).\n"
                    "If this is a Google Drive link the file is probably not link-shared; "
                    "pass pdf_b64 instead.\n%s" % (len(raw), raw[:8], head))
    else:
        return "ERROR: supply either pdf_url or pdf_b64."

    doc = pymupdf.open(stream=raw, filetype="pdf")
    n = doc.page_count

    if not pages or pages.strip().lower() == "all":
        want = list(range(n))
    else:
        want = []
        for part in pages.split(","):
            part = part.strip()
            m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
            if m:
                want.extend(range(int(m.group(1)) - 1, int(m.group(2))))
            elif part.isdigit():
                want.append(int(part) - 1)
        want = [p for p in want if 0 <= p < n]
    if not want:
        return "ERROR: page range %r selects nothing (document has %d pages)." % (pages, n)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.environ.get("OPENAI_API_BASE"))

    instruction = (
        "You are transcribing a scanned laboratory certificate for a pharmaceutical "
        "quality register. Transcribe EVERY character on the page verbatim.\n"
        "Rules:\n"
        "1. Copy exactly what is printed. Never correct, complete, reorder or improve "
        "anything — not a misspelled word, not a control-book number that looks wrong, "
        "not a result that contradicts itself, not a limit that looks outdated.\n"
        "2. Preserve Macedonian Cyrillic exactly. Do NOT transliterate.\n"
        "3. Chemical and unit symbols are printed in Latin script: THC, CBD, CBDA, CBN, "
        "CBNA, Pb, Cd, As, Hg, CFU/g, mg/kg, ug/kg, %w/w. Always render these in Latin "
        "letters even when surrounded by Cyrillic. Never output Cyrillic lookalikes such "
        "as ТНС for THC or СВD for CBD.\n"
        "4. Keep tables as markdown tables, preserving column order and every cell, "
        "including empty cells.\n"
        "5. Keep all document numbers, dates, stamps, signatures and footer codes.\n"
        "6. If something is genuinely unreadable, write [illegible] in its place. Never "
        "guess a digit.\n"
        "Output only the transcription, with no commentary.")

    chunks, errors = [], []
    for idx in want:
        page = doc.load_page(idx)
        pix = page.get_pixmap(dpi=dpi)
        img = pix.tobytes("png")
        if len(img) > 18 * 1024 * 1024:
            pix = page.get_pixmap(dpi=max(120, dpi // 2))
            img = pix.tobytes("png")
        b64 = base64.b64encode(img).decode()
        try:
            r = client.chat.completions.create(
                model=model, max_tokens=4096, temperature=0,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url",
                     "image_url": {"url": "data:image/png;base64," + b64,
                                   "detail": "high"}}]}])
            txt = (r.choices[0].message.content or "").strip()
            if not txt:
                txt = "[no text returned for this page]"
                errors.append("page %d: empty response" % (idx + 1))
        except Exception as e:
            txt = "[OCR FAILED for this page]"
            errors.append("page %d: %s: %s" % (idx + 1, type(e).__name__, str(e)[:200]))
        chunks.append("[page %d]\n%s" % (idx + 1, txt))

    doc.close()
    body = "\n\n----- page break -----\n\n".join(chunks)
    header = ("SOURCE: %s\nPAGES: %s of %d   DPI: %d   MODEL: %s\n"
              % (pdf_url or "(bytes supplied)", ",".join(str(p + 1) for p in want), n,
                 dpi, model))
    result = header + ("ERRORS: %s\n" % "; ".join(errors) if errors else "") + "\n" + body

    if save_as:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", save_as)
        path = os.path.join("/root/.letta/pp-stage", safe)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(result)
        result = "SAVED: %s (%d chars)\n\n%s" % (path, len(result), result)
    return result
