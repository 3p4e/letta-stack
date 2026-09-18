#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the QCSP 001 v.04 sheets to PDF, one A4 page each, fonts embedded.

    python3 deliverables/qc_gap_analysis/specs/print_qcsp004.py

The same pipeline the certificates use (live_instrument/print_coq_pdfs.py): the faces are
fetched once, subset to the characters these sheets print, inlined as data URIs, and Google
is blocked at the network layer for the run — a renderer with no route to Google substitutes
silently, and a controlled document that changes appearance depending on whether Google is
reachable is not one to hand a regulator.
"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
import house_fonts                                                       # noqa: E402
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, render, merge   # noqa: E402

OUT = os.path.join(HERE, "QCSP_001_v04")
PAGES = os.path.join(OUT, "pdf", "pages")


def bookmarks(book, made):
    """Name every sheet in the bound specification, so 57 pages can be navigated.

    The whole specification travels with the bundles as its own document, and a reader
    looking for one strain's window should not have to page through the rest of them.
    """
    import pymupdf
    ix = {s["code"]: s for s in
          json.load(open(os.path.join(OUT, "INDEX.json"), encoding="utf-8"))["sheets"]}
    doc = pymupdf.open(book)
    toc = []
    for i, f in enumerate(made):
        stem = os.path.basename(f).rsplit(".", 1)[0]
        hit = next((c for c in ix if stem.startswith(c)), None)
        s = ix.get(hit) or {}
        label = "%s — %s, Grade %s  (%s)" % (hit or stem, s.get("strain", ""),
                                             s.get("grade", ""), s.get("window", ""))
        toc.append([1, label if hit else stem, i + 1])
    doc.set_toc(toc)
    doc.saveIncr() if doc.can_save_incrementally() else doc.save(book + ".tmp")
    doc.close()
    if os.path.exists(book + ".tmp"):
        os.replace(book + ".tmp", book)
    return toc


def main():
    pages = sorted(glob.glob(os.path.join(OUT, "SHEETS", "*.html")))
    if not pages:
        raise SystemExit("no sheets — run build_qcsp004.py first")
    os.makedirs(PAGES, exist_ok=True)
    css, raw, small = house_fonts.font_face_css(page_text(pages), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB upstream -> %.0f KB subset"
          % (css.count("@font-face"), raw / 1024.0, small / 1024.0))
    chromium = (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    made = render(pages, PAGES, chromium, css)
    book = os.path.join(OUT, "pdf", "QCSP_001_v04.pdf")
    merge(made, book)
    bookmarks(book, made)
    print("  %d sheet(s)  %s (%.1f MiB)" % (len(made), os.path.basename(book),
                                            os.path.getsize(book) / 1048576.0))


if __name__ == "__main__":
    main()
