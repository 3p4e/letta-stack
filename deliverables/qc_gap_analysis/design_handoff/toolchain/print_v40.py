#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the Claude Design CoQ set to PDF — one A4 page per document, fonts embedded.

    python3 design_handoff/toolchain/print_v40.py                 # every document
    python3 design_handoff/toolchain/print_v40.py --only 26-013   # a substring filter
    python3 design_handoff/toolchain/print_v40.py --no-flatten    # vector merges only

Export settings are the package's own (docs/HANDOVER_to_ClaudeCode.md §1.7): A4,
margins 0, background graphics on, scale 100 %, no browser headers — Chromium with
prefer_css_page_size and print_background, the document's @page rule owning the frame.

Fonts: the package loads Montserrat, Roboto Mono and Orbitron from Google Fonts by
<link>. A renderer without a route to Google substitutes silently, and a substituted
mono breaks every column width measured against Roboto Mono's advance — so the faces
are fetched once, subset to the characters the set prints (latin + latin-ext +
cyrillic + greek), inlined as @font-face data URIs, and Google is blocked at the
network layer for the run. Same mechanism as live_instrument/print_coq_pdfs.py.

Outputs, under design_handoff/pdf/:
  pages/<document>.pdf                       one per document
  CoQ_<folder>.pdf                           one vector PDF per folder, bookmarked
  CoQ_<folder>_flat.pdf                      the same, each page a 300 dpi lossless raster
"""
import argparse, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); HANDOFF = os.path.dirname(HERE)
GAP = os.path.dirname(HANDOFF); ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, render   # noqa: E402
import house_fonts                                                  # noqa: E402
OUT = os.path.join(HANDOFF, "out"); PDF = os.path.join(HANDOFF, "pdf")
FOLDERS = ["ISSUE_COQ", "REISSUE/T1", "REISSUE/T2", "REISSUE/T3"]


def order_key(p):
    m = re.search(r"CoQ-PP_26-(\d{3})", os.path.basename(p))
    return (0, int(m.group(1))) if m else (1, os.path.basename(p))


def label(text):
    code = re.search(r"CoQ-PP[-_][\w\-]+", text or ""); lot = re.search(r"\b[PJ]\d{5,6}\b", text or "")
    return " · ".join([code.group(0) if code else "— assigned on issue —"] + ([lot.group(0)] if lot else []))


def merge(pages, dest, flatten, dpi):
    import pymupdf
    out = pymupdf.open(); toc = []
    for p in pages:
        d = pymupdf.open(p)
        for pg in d:
            name = label(pg.get_text())
            if flatten:
                pix = pg.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                n = out.new_page(width=pg.rect.width, height=pg.rect.height); n.insert_image(n.rect, pixmap=pix)
            else:
                out.insert_pdf(d, from_page=pg.number, to_page=pg.number)
            toc.append([1, name, out.page_count])
        d.close()
    out.set_toc(toc)
    out.set_metadata({"title": "Purely Plant — Certificates of Quality", "producer": "Purely Plant Quality Desk"})
    out.save(dest, garbage=4, deflate=True); out.close()
    return len(toc)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None); ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--no-flatten", action="store_true"); ap.add_argument("--chromium", default=None)
    a = ap.parse_args(argv[1:])
    chromium = a.chromium or (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    sets = {}
    for f in FOLDERS:
        ps = sorted(glob.glob(os.path.join(OUT, f, "*.html")), key=order_key)
        if a.only: ps = [p for p in ps if a.only in os.path.basename(p)]
        if ps: sets[f] = ps
    every = [p for ps in sets.values() for p in ps]
    if not every: raise SystemExit("nothing to print under " + OUT)
    css, raw, small = house_fonts.font_face_css(page_text(every), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB upstream -> %.0f KB subset" % (css.count("@font-face"), raw / 1024.0, small / 1024.0))
    pages_dir = os.path.join(PDF, "pages"); os.makedirs(pages_dir, exist_ok=True)
    for f, ps in sets.items():
        made = render(ps, pages_dir, chromium, css)
        stem = os.path.join(PDF, "CoQ_" + f.replace("/", "_"))
        n = merge(made, stem + ".pdf", False, a.dpi)
        line = "  %-12s %3d page(s)  %s (%.1f MiB)" % (f, n, os.path.basename(stem + ".pdf"), os.path.getsize(stem + ".pdf") / 1048576.0)
        if not a.no_flatten:
            merge(made, stem + "_flat.pdf", True, a.dpi)
            line += "  flat %.1f MiB" % (os.path.getsize(stem + "_flat.pdf") / 1048576.0)
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
