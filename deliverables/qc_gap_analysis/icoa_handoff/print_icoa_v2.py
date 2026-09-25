#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the internal certificates of analysis to PDF — one A4 page each, fonts embedded.

    python3 icoa_handoff/print_icoa_v2.py                 # both folders
    python3 icoa_handoff/print_icoa_v2.py --only 26-013   # a substring filter
    python3 icoa_handoff/print_icoa_v2.py --preview       # out/_preview, plus a PNG

The same pipeline as the certificate of quality (`design_handoff/toolchain/print_v40.py`)
and for the same reason: the page loads Montserrat, Roboto Mono and Orbitron from Google
Fonts by `<link>`, and a renderer with no route to Google substitutes silently — which
breaks every column measured against Roboto Mono's advance. The faces are fetched once,
subset to the characters the set prints, inlined as `@font-face` data URIs, and Google is
blocked at the network layer for the run.

Outputs under `icoa_handoff/pdf/`: `pages/<document>.pdf`, one merged bookmarked PDF per
folder, and in preview mode a 150 dpi PNG of the first page to look at.
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, render    # noqa: E402
import house_fonts                                                  # noqa: E402

OUT = os.path.join(HERE, "out")
PDF = os.path.join(HERE, "pdf")


def order_key(p):
    m = re.search(r"iCoA-PP_26-(\d{3})", os.path.basename(p))
    return (0, int(m.group(1))) if m else (1, os.path.basename(p))


def label(text):
    code = re.search(r"iCoA-PP[-_][\w\-]+", text or "")
    lot = re.search(r"\b[PJ]\d{5,6}\b", text or "")
    return " · ".join([code.group(0) if code else "—"] + ([lot.group(0)] if lot else []))


def merge(pages, dest):
    import pymupdf
    out, toc = pymupdf.open(), []
    for p in pages:
        d = pymupdf.open(p)
        for pg in d:
            out.insert_pdf(d, from_page=pg.number, to_page=pg.number)
            toc.append([1, label(pg.get_text()), out.page_count])
        d.close()
    out.set_toc(toc)
    out.set_metadata({"title": "Purely Plant — Internal Certificates of Analysis",
                      "producer": "Purely Plant Quality Desk"})
    out.save(dest, garbage=4, deflate=True)
    out.close()
    return len(toc)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--chromium", default=None)
    a = ap.parse_args(argv[1:])
    chromium = a.chromium or (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome")
                              or [None])[0]
    root = os.path.join(OUT, "_preview") if a.preview else OUT
    sets = {}
    for f in ("INITIAL", "RETEST"):
        ps = sorted(glob.glob(os.path.join(root, f, "*.html")), key=order_key)
        if a.only:
            ps = [p for p in ps if a.only in os.path.basename(p)]
        if ps:
            sets[f] = ps
    every = [p for ps in sets.values() for p in ps]
    if not every:
        raise SystemExit("nothing to print under " + root)
    css, raw, small = house_fonts.font_face_css(page_text(every), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB upstream -> %.0f KB subset"
          % (css.count("@font-face"), raw / 1024.0, small / 1024.0))
    pages_dir = os.path.join(PDF, "preview" if a.preview else "pages")
    os.makedirs(pages_dir, exist_ok=True)
    for f, ps in sets.items():
        made = render(ps, pages_dir, chromium, css)
        if a.preview:
            import pymupdf
            for m in made:
                d = pymupdf.open(m)
                d[0].get_pixmap(dpi=150).save(m[:-4] + ".png")
                d.close()
            print("  %-8s %3d page(s) -> %s" % (f, len(made), os.path.relpath(pages_dir, GAP)))
            continue
        stem = os.path.join(PDF, "iCoA_" + f)
        n = merge(made, stem + ".pdf")
        print("  %-8s %3d page(s)  %s (%.1f MiB)"
              % (f, n, os.path.basename(stem + ".pdf"),
                 os.path.getsize(stem + ".pdf") / 1048576.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
