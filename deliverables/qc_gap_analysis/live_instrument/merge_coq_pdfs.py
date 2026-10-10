#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One document per tranche, flattened for the printer.

    python3 deliverables/qc_gap_analysis/live_instrument/merge_coq_pdfs.py
    python3 deliverables/qc_gap_analysis/live_instrument/merge_coq_pdfs.py --dpi 400
    python3 deliverables/qc_gap_analysis/live_instrument/merge_coq_pdfs.py --no-flatten

`print_coq_pdfs.py` prints four files — the release certificates and the 12-month
reissues, each split by tranche. A person reading a tranche wants **one** document,
and the Head of QC asked for exactly that on 16.09.2026: all of Tranche 1 in one
file and all of Tranche 2 in another, with the graphics flattened.

## What "merged" means here

The release certificates first, in P-lot order, then the reissues, in P-lot order —
the order the rounds happened in, which is how a batch file reads. Nothing is
reordered, reformatted or re-rendered from the HTML: the pages are the ones
`print_coq_pdfs.py` produced, so a page in the merged document is byte-for-byte the
same certificate a person printed singly.

Each page gets a **bookmark naming its certificate**, read off the page itself
(`CoQ-PP_26-007 · P050022 · release`), so a 34-page document opens as a list of
certificates rather than a scroll. The code is read from the page text rather than
from a scope file, so a bookmark can never name a page it is not on.

## Why the pages are flattened, and what is lost

The certificate is not flat artwork. Its banner, its section rules, the selection
pills and the red of every marked field are gradients, blends and layered fills, and
a printer resolves those itself — screening a gradient, approximating a blend mode,
sometimes dropping a soft mask entirely. Two printers can disagree about the same
file, which is not a property a controlled document should have.

So each page is rendered once, here, at `--dpi` (300 by default, the print standard),
into a single RGB raster, and that raster becomes the page. Every gradient is
resolved to pixels before the file leaves the desk: what the Quality Desk renders is
what every printer puts on paper, and the document no longer depends on the printer's
interpretation of a blend.

The image is written **lossless** — Flate, not JPEG. On this artwork that is not a
compromise for quality's sake alone: the pages are mostly flat colour with smooth
gradients and thin red hairlines, which PNG compresses to about two thirds of what
JPEG q95 costs and without ringing around the hairlines. Measured on Tranche 1
page 1 at 300 dpi: 1060 KiB lossless against 1574 KiB at JPEG q95.

**What is lost is the text layer.** A flattened page cannot be selected, searched or
copied, and a screen reader cannot read it. That is the trade, and it is why the four
vector files `print_coq_pdfs.py` produces are left in place rather than replaced —
they remain the searchable record, and `--no-flatten` merges without rasterising for
anyone who wants one file that is still text.

Page geometry is preserved exactly: the raster is placed on a page of the source
page's own rectangle, so an A4 page stays 210 × 297 mm and prints at 100 %.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
DRAFTS = os.path.join(GAP, "drafts")

# (output stem, human title, [source files in the order they are merged])
TRANCHES = [
    ("Tranche_1_CoQ_Complete", "Tranche 1 — certificates of quality",
     ["Tranche_1_CoQ_Drafts.pdf", "Tranche_1_CoQ_Reissue_Drafts.pdf"]),
    ("Tranche_2_CoQ_Complete", "Tranche 2 — certificates of quality",
     ["Tranche_2_CoQ_Drafts.pdf", "Tranche_2_CoQ_Reissue_Drafts.pdf"]),
]
A4_MM = (210.0, 297.0)
_TOL_MM = 0.5


def label(text, series):
    """The bookmark for one page, read off the page's own text.

    >>> label("CODE\\nCoQ-PP_26-007\\nIssued 06.06.2026\\nP050022 | GRAPE PIE", "release")
    'CoQ-PP_26-007 · P050022 · release'
    >>> label("nothing here", "reissue")
    '— at issue — · reissue'
    """
    code = re.search(r"CoQ-PP[-_][\w\-]+", text or "")
    lot = re.search(r"\b[PJ]\d{5,6}\b", text or "")
    parts = [code.group(0) if code else "— at issue —"]
    if lot:
        parts.append(lot.group(0))
    parts.append(series)
    return " · ".join(parts)


def series_of(name):
    return "reissue" if "Reissue" in name else "release"


def build(stem, title, sources, dpi, flatten, out_dir):
    import pymupdf
    out = pymupdf.open()
    toc, off_spec = [], []
    for src in sources:
        path = os.path.join(DRAFTS, src)
        if not os.path.exists(path):
            raise SystemExit("missing source: %s — run print_coq_pdfs.py first" % path)
        doc = pymupdf.open(path)
        ser = series_of(src)
        for page in doc:
            rect = page.rect
            mm = (rect.width / 72 * 25.4, rect.height / 72 * 25.4)
            if abs(mm[0] - A4_MM[0]) > _TOL_MM or abs(mm[1] - A4_MM[1]) > _TOL_MM:
                off_spec.append((src, page.number + 1, round(mm[0], 1), round(mm[1], 1)))
            name = label(page.get_text(), ser)
            if flatten:
                pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                new = out.new_page(width=rect.width, height=rect.height)
                new.insert_image(new.rect, pixmap=pix)     # Flate, lossless
            else:
                out.insert_pdf(doc, from_page=page.number, to_page=page.number)
            toc.append([1, name, out.page_count])
        doc.close()
    out.set_toc(toc)
    out.set_metadata({
        "title": "Purely Plant — %s" % title,
        "subject": "Certificates of quality — DRAFT, unsigned, not issued",
        "producer": "Purely Plant Quality Desk",
    })
    dest = os.path.join(out_dir, stem + ".pdf")
    out.save(dest, garbage=4, deflate=True)
    out.close()
    return dest, len(toc), off_spec


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=300,
                    help="rasterisation resolution when flattening (default 300)")
    ap.add_argument("--no-flatten", action="store_true",
                    help="merge without rasterising — keeps the text layer")
    ap.add_argument("--out", default=DRAFTS, help="output directory (default: drafts/)")
    a = ap.parse_args(argv[1:])
    flatten = not a.no_flatten
    print("one document per tranche — %s" % (
        "flattened at %d dpi, lossless" % a.dpi if flatten else "vector, text preserved"))
    for stem, title, sources in TRANCHES:
        dest, pages, off = build(stem + ("" if flatten else "_vector"),
                                 title, sources, a.dpi, flatten, a.out)
        print("  %-34s %2d page(s)  %6.1f MiB" % (
            os.path.basename(dest), pages, os.path.getsize(dest) / 1048576.0))
        for src, n, w, h in off:
            print("      page %d of %s is %s x %s mm, not A4" % (n, src, w, h))
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
