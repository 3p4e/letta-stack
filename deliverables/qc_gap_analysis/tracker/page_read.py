#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read a certificate page: its own text layer, or the policy vision chain.

Classical OCR is not used here, and this is not a preference. These certificates are
Macedonian Cyrillic mixed with Latin chemical symbols, Greek letters and superscripts —
exactly what Tesseract handles worst, and the distinction it loses (10² read as 102,
< 10² и > 10 read as a single number) is the distinction this verification exists to
test. The standing rule is in AGENT_MODEL_POLICY.md and is enforced by
scripts/policy_check.py:

    OCR / document vision -> kimi-k2.6 -> moonshot-v1-128k-vision-preview -> gpt-4o

The chain itself has one definition, in ingestion/ragflow/doc_identity.py; this module
adds only what the tracker needs on top of it — a reading instruction written for a
certificate rather than a water report, whole-document rather than first-two-pages, and
a cache, because a vision read costs real money and the same pages are re-read on every
verification run.
"""
import os, re, subprocess, sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", ".."))
sys.path.insert(0, os.path.join(_ROOT, "ingestion", "ragflow"))
import doc_identity

# The tracker's own reading instruction. Rule 1 is the governing rule of the whole
# register: transcribe the paper, never improve it. Rules 4 and 5 exist because the
# values under test are precisely the ones a careless reader flattens.
PROMPT = (
    "Transcribe this laboratory certificate page verbatim for a pharmaceutical "
    "quality register.\n"
    "1. Copy exactly what is printed. Never correct, complete or improve anything.\n"
    "2. Preserve Macedonian Cyrillic exactly; do NOT transliterate.\n"
    "3. Chemical and unit symbols are printed in Latin: THC, CBD, CBN, Pb, Cd, As, "
    "Hg, CFU/g, mg/kg, %w/w. Render these in Latin even when surrounded by Cyrillic — "
    "never Cyrillic lookalikes such as ТНС for THC.\n"
    "4. Keep every exponent as printed: write 10^2 for a superscript two, and keep a "
    "counted range whole, e.g. '< 10^2 и > 10'. Never flatten 10^2 to 102 or drop the "
    "second half of a range.\n"
    "5. Keep the decimal separator as printed — a comma stays a comma.\n"
    "6. Copy each result row as 'parameter | result | unit | method', one per line.\n"
    "Return the page text only, no commentary."
)


def cache_dir(base=None):
    d = base or os.environ.get("QC_PAGE_CACHE") or os.path.join(
        os.environ.get("QC_WORK_DIR", "/tmp/qc_page_check"), "pagetext")
    os.makedirs(d, exist_ok=True)
    return d


def page_text(path, cache=None, dpi=200):
    """The page's own words: its text layer when it has one, else the vision chain.

    A vision read is marked '[vision]' in the first line so a caller can tell the two
    apart — a read text layer is the document, a vision read is a reading of it."""
    cd = cache_dir(cache)
    key = os.path.join(cd, re.sub(r"[^0-9A-Za-zА-Яа-я.\-]", "_",
                                  os.path.basename(path)) + ".txt")
    if os.path.exists(key):
        return open(key, encoding="utf-8").read()
    t = doc_identity.raw_text(path)
    if len(t.strip()) < 200:
        n = doc_identity.pages(path) or 1
        t = doc_identity.ocr_text(path, max_pages=n, dpi=dpi, prompt=PROMPT)
        if t.strip():
            t = "[vision:%s]\n%s" % (getattr(doc_identity.ocr_text, "last_model",
                                             None) or "none", t)
        else:
            t = ""
    open(key, "w", encoding="utf-8").write(t)
    return t


if __name__ == "__main__":
    print(page_text(sys.argv[1])[:2500])
