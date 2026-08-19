#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify a laboratory report by what is printed ON it, never by its filename.

A report reaches us under any name — `1468 П.pdf`, `izvestaj_scan_0043.pdf`,
`WhatsApp Image ....pdf` — and in either of two forms: the laboratory's digital
export (real text layer) or a scan (image only). The same report in those two
forms is ONE record, and must never be ingested twice.

So identity comes from the document body:

    Лаб. број: 1468/2026        -> lab number, the primary key
    Датум на земање: 14.05.2026 -> sampling date
    Мерно место: ... -RO-E84-014 -> sampling point code
    Страна 1 од 4               -> how many pages the report should have

For a scan there is no text layer, so the pages are rasterised and read by a
VISION MODEL, per `AGENT_MODEL_POLICY.md`:

    OCR / document vision -> kimi-k2.6 -> moonshot-v1-128k-vision-preview -> gpt-4o

Classical OCR is deliberately not used. These certificates are Macedonian
Cyrillic mixed with Latin chemical symbols, Greek letters and superscripts —
the case classical OCR handles worst — and the reasoning is recorded in
`pp_ocr_scanned_pdf.py`, which was verified against GG1024 to reproduce all 29
register rows exactly. The one normalisation carried over from it: a vision
model surrounded by Cyrillic returns homoglyphs for Latin chemical symbols
("ТНС" for "THC"), so the prompt pins chemical and unit symbols to Latin.
Identity and the completeness check therefore work identically for scanned and
digital copies.

Where both forms of one report exist, `better_of()` picks the one to keep:
more pages wins; on a tie the digital original beats the scan, because OCR
text is a lossy reading of it.
"""
import base64, json, os, re, subprocess, tempfile, urllib.request

# Per AGENT_MODEL_POLICY.md — OCR / document vision.
OCR_CHAIN = [
    ("kimi-k2.6", "https://api.moonshot.ai/v1", "MOONSHOT_API_KEY"),
    ("moonshot-v1-128k-vision-preview", "https://api.moonshot.ai/v1", "MOONSHOT_API_KEY"),
    ("gpt-4o", "https://api.openai.com/v1", "OPENAI_API_KEY"),
]

PROMPT = (
    "Transcribe this scanned laboratory certificate page verbatim for a "
    "pharmaceutical quality register.\n"
    "1. Copy exactly what is printed. Never correct, complete or improve anything.\n"
    "2. Preserve Macedonian Cyrillic exactly; do NOT transliterate.\n"
    "3. Chemical and unit symbols are printed in Latin: THC, CBD, CBN, Pb, Cd, As, "
    "Hg, CFU/g, mg/kg, %w/w. Render these in Latin even when surrounded by "
    "Cyrillic — never Cyrillic lookalikes such as ТНС for THC.\n"
    "4. Include every header and footer line, especially lines of the form "
    "'Лаб. број: NNNN/YYYY', 'Датум на земање: DD.MM.YYYY', 'Мерно место: ...' "
    "and the page footer 'Страна N од M'.\n"
    "Return the page text only, no commentary."
)

LAB = re.compile(r"(?:Лаб\.?\s*број|Број)\s*[:：]?\s*(\d{3,5})\s*/\s*(20\d{2})")
SAMPLED = re.compile(r"Датум на земање\s*[:：]?\s*(\d{2}\.\d{2}\.20\d{2})")
POINT = re.compile(r"[-–]\s*([A-ZА-Я]{1,3}[-_ ]?[A-ZА-Я]?\d{2,3}[-_ ]{1,2}\d{3})\s*$", re.M)
FOOTER = re.compile(r"Страна\s+(\d+)\s+од\s+(\d+)")


def pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else 0


def raw_text(pdf, first=None, last=None):
    cmd = ["pdftotext"]
    if first:
        cmd += ["-f", str(first), "-l", str(last or first)]
    return subprocess.run(cmd + [pdf, "-"], capture_output=True, text=True).stdout


def _page_pngs(pdf, max_pages=2, dpi=200):
    td = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", "1",
                    "-l", str(max_pages), pdf, os.path.join(td, "p")],
                   capture_output=True)
    return td, [os.path.join(td, f) for f in sorted(os.listdir(td)) if f.endswith(".png")]


def _vision(model, base, key, png):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," +
             base64.b64encode(open(png, "rb").read()).decode()}},
        ]}],
        "temperature": 0,
    }
    r = urllib.request.Request(base.rstrip("/") + "/chat/completions",
                               data=json.dumps(body).encode(),
                               headers={"Authorization": "Bearer " + key,
                                        "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=180) as f:
        d = json.loads(f.read().decode())
    return d["choices"][0]["message"]["content"]


def ocr_text(pdf, max_pages=2, dpi=200, verbose=False):
    """Read a scanned page with the policy vision chain. Never classical OCR."""
    td, pngs = _page_pngs(pdf, max_pages, dpi)
    out, used = [], None
    try:
        for png in pngs:
            for model, base, env in OCR_CHAIN:
                key = os.environ.get(env)
                if not key:
                    continue
                try:
                    out.append(_vision(model, base, key, png))
                    used = model
                    break
                except Exception as e:
                    if verbose:
                        print("   %s failed: %s" % (model, str(e)[:90]))
                    continue
    finally:
        for f in pngs:
            os.path.exists(f) and os.remove(f)
        os.path.isdir(td) and os.rmdir(td)
    ocr_text.last_model = used
    return "\n".join(out)


def text_of(pdf):
    """Text layer if the PDF has one, OCR if it does not. Returns (text, how)."""
    t = raw_text(pdf)
    if len(t.strip()) > 200:
        return t, "text-layer"
    t = ocr_text(pdf)
    return t, "vision:" + (getattr(ocr_text, "last_model", None) or "none")


def identity(pdf):
    """Everything needed to decide 'is this the same report we already hold?'"""
    t, how = text_of(pdf)
    lab = LAB.search(t)
    sampled = SAMPLED.search(t)
    point = POINT.search(t)
    foot = FOOTER.search(t)
    have = pages(pdf)
    declared = int(foot.group(2)) if foot else None
    return {
        "path": pdf,
        "source": how,
        "lab_no": ("%s/%s" % (lab.group(1), lab.group(2))) if lab else None,
        "sampled": sampled.group(1) if sampled else None,
        "point": (point.group(1).replace("_", "-").replace(" ", "-")
                  if point else None),
        "pages": have,
        "declared_pages": declared,
        "complete": (declared is not None and have >= declared),
        "readable": bool(lab),
    }


def key(ident):
    """The dedup key. Lab number is unique per laboratory-year on its own;
    the sampling date is carried as a cross-check, not as part of the key."""
    return ident.get("lab_no")


def better_of(a, b):
    """Which of two copies of the same report to keep."""
    if a["pages"] != b["pages"]:
        return a if a["pages"] > b["pages"] else b
    if a["source"] != b["source"]:
        return a if a["source"] == "text-layer" else b
    return a


if __name__ == "__main__":
    import json, sys
    for f in sys.argv[1:]:
        print(json.dumps(identity(f), ensure_ascii=False))
