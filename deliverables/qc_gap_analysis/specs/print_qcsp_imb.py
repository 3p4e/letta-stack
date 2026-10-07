#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the specification sheets to PDF — one A4 page each, fonts embedded.

    python3 deliverables/qc_gap_analysis/specs/print_qcsp_imb.py

The same pipeline the certificates use. The page loads Montserrat, Roboto Mono and Orbitron
from Google Fonts by <link>; a renderer with no route to Google substitutes silently, which
moves every column measured against Roboto Mono's advance. The faces are fetched once,
subset to the characters the set prints, inlined as @font-face data URIs, and Google is
blocked at the network layer for the run.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, render, merge   # noqa: E402
import house_fonts                                                        # noqa: E402

OUT = os.path.join(HERE, "QCSP_001_ImB")
SHEETS = os.path.join(OUT, "SHEETS")
PAGES = os.path.join(OUT, "PDF")


def pages_of(pdf):
    try:
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
    except Exception:
        pass
    return 0


def main(argv=()):
    """Print every sheet, or only the sheets named (file names under SHEETS/): a rebuild that changes a few
    sheets reprints those and leaves every other PDF as it is. The font subset is always cut from the whole set."""
    sheets = sorted(glob.glob(os.path.join(SHEETS, "*.html")))
    if not sheets:
        raise SystemExit("no sheets — run build_qcsp_imb.py first")
    want = [os.path.basename(a) for a in argv]
    chosen = [s for s in sheets if not want or os.path.basename(s) in want]
    if len(chosen) != (len(want) or len(sheets)):
        raise SystemExit("not every named sheet exists: %s" % sorted(set(want) - {os.path.basename(s) for s in sheets}))
    os.makedirs(PAGES, exist_ok=True)
    css, raw, small = house_fonts.font_face_css(page_text(sheets), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB upstream -> %.0f KB subset"
          % (css.count("@font-face"), raw / 1024.0, small / 1024.0))
    # Playwright's own browser, as the certificate printer uses; a fixed /opt/pw-browsers build can be one the
    # installed Playwright no longer drives (chromium-1194 exits on launch under Playwright 1.56)
    chromium = None
    made = render(chosen, PAGES, chromium, css)
    book = os.path.join(OUT, "QCSP_001_ImB.pdf")
    merge(sorted(glob.glob(os.path.join(PAGES, "*.pdf"))), book)
    bad = [(os.path.basename(f), pages_of(f)) for f in made if pages_of(f) != 1]
    print("printed %d sheet(s) -> %s" % (len(made), os.path.relpath(PAGES)))
    print("  merged: %s (%.1f MiB)" % (os.path.basename(book),
                                       os.path.getsize(book) / 1048576.0))
    for name, n in bad:
        print("   NOT ONE PAGE: %s (%d)" % (name, n))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
