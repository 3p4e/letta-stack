#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A fleet of certificates as Word that a person can actually type into.

    python3 design_handoff/toolchain/build_editable_docx.py SRC_DIR --docx OUT_DIR
        [--pdf PDF_DIR] [--sample 2]

`pdf_to_docx_exact.py` on its own gives one positioned box per **PDF text span**, which is
right for a record nobody edits: the page is exact and every run sits where the approved
page puts it. It is wrong for a document somebody has to correct, because a span is
whatever the renderer happened to draw — a lot code arrives in three pieces and nobody can
retype a date that is split across two boxes. The owner, on the blank templates:

    "is it possible that the individual text boxes follow some logical wholeness?
     not just with 3 or 5 words"

Merging boxes by their positions was tried on those templates and measured, and it is not
safe: ink position does not say what belongs together. The **DOM** does. So this takes the
same route `BLANK_TEMPLATES/build_template_docx.py` established for the blank set and
applies it to a populated fleet — read the element boundaries off the laid-out page in the
very pass that prints it, and leave the PDF to say where the ink goes. The page is
untouched; only the boxes change, from one per span to one per field.

The source is expected to be the **self-contained** HTML — fonts already inlined — so
nothing is injected and nothing is fetched. `--sample N` converts N of the documents twice,
once per span and once per field, so the report can state the improvement instead of
claiming it.
"""
import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, HERE)

from print_coq_pdfs import render                                        # noqa: E402
import pdf_to_docx_exact as X                                            # noqa: E402
from build_template_fields import PROBE, fields_for, words               # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", help="a directory of self-contained HTML")
    ap.add_argument("--docx", required=True)
    ap.add_argument("--pdf")
    ap.add_argument("--sample", type=int, default=2,
                    help="how many documents to also convert per-span, for the comparison")
    ap.add_argument("--dpi", type=int, default=300)
    a = ap.parse_args(argv)

    sheets = sorted(glob.glob(os.path.join(a.src, "*.html")))
    if not sheets:
        raise SystemExit("no HTML in %s" % a.src)
    pdfdir = a.pdf or os.path.join(a.docx, "_pdf")
    os.makedirs(pdfdir, exist_ok=True)
    os.makedirs(a.docx, exist_ok=True)

    chromium = (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    probed = {}

    def probe(src, page):
        page.emulate_media(media="print")      # measure the layout that will be PRINTED
        probed[src] = page.evaluate(PROBE)

    made = render(sheets, pdfdir, chromium, "", probe=probe)
    print("printed %d page(s)" % len(made))

    cmp_rows = []
    for i, (src, pdf_path) in enumerate(zip(sheets, made)):
        name = os.path.basename(pdf_path)[:-4]
        fields = fields_for(probed[src], pdf_path)
        docx = os.path.join(a.docx, name + ".docx")
        before = None
        if i < a.sample:
            plain = os.path.join(a.docx, "." + name + ".span.docx")
            X.convert(pdf_path, plain, dpi=a.dpi, fonts=False, quiet=True)
            before = words(plain)
            os.remove(plain)
        X.convert(pdf_path, docx, dpi=a.dpi, fonts=True, quiet=True, fields=fields)
        if before:
            cmp_rows.append((name, before, words(docx), len(fields[0])))

    if cmp_rows:
        print("\n%-46s %14s %14s" % ("", "one box/span", "one box/field"))
        for name, b, af, nf in cmp_rows:
            print("%-46s %5d / %-6s %5d / %-6s  (%d DOM fields)"
                  % (name[:46], b[0], "%d w" % b[1], af[0], "%d w" % af[1], nf))
    print("\n%d Word file(s) -> %s" % (len(made), a.docx))
    return 0


if __name__ == "__main__":
    sys.exit(main())
