#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One HTML file per certificate that needs nothing else to render.

    python3 deliverables/qc_gap_analysis/build_selfcontained.py \
        SIGNED_2026-09-21/iCoA/Retest/HTML  --out SELFCONTAINED/iCoA_Retest

Head of QC, 23.09.2026: the HTML must open in Word on the desktop with no runtime error.

The issued HTML does not, and the reason is not scripts — there are none in any of them. It is
that each file **links four things it is not shipped with**: `../_icoa.css`, `../_coq-rules.css`,
`../_icoa3-print.css` and `../_logo.svg`, none of which sit beside the documents in the signed
set, plus a stylesheet on `fonts.googleapis.com`. Opened on its own the document therefore
arrives unstyled and the reader goes out to the network for the rest — which is where the
complaint comes from, and which no controlled document should ever do.

So this script folds all of it in:

* the three stylesheets, in the order the document links them, as one `<style>` block;
* the logo, as a `data:image/svg+xml;base64` URI;
* the three house families, **subset to the characters these documents actually print** and
  inlined as `data:font/woff2` — the same `house_fonts.font_face_css()` the printer uses, so the
  faces are the ones the PDF was made with, not whatever the machine happens to have;
* and the `fonts.googleapis.com` link removed, because a document whose appearance depends on a
  third party being reachable is not one to hand an inspector.

The signatures are already `data:` URIs in the issued files and need nothing.

Nothing about the page changes. No rule is edited, no element moves: the same CSS in the same
order, the same markup, the same glyphs. The only difference is that it is all in the one file.
"""
import argparse
import base64
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
sys.path.insert(0, os.path.join(HERE, "live_instrument"))

ASSETS = os.path.join(HERE, "icoa_handoff", "v3", "ISSUE_iCOA")
GOOGLE = re.compile(r'<link[^>]+fonts\.googleapis\.com[^>]*>\s*', re.I)
SHEET = re.compile(r'<link[^>]+rel="stylesheet"[^>]+href="(\.\./[^"]+\.css)"[^>]*>\s*', re.I)


def asset(name):
    p = os.path.join(ASSETS, os.path.basename(name))
    if not os.path.exists(p):
        raise SystemExit("asset not found, so the page could not render: %s" % p)
    return p


def inline_one(html, font_css):
    """The document with every external dependency folded in, in the order it linked them."""
    sheets = SHEET.findall(html)
    css = []
    for href in sheets:
        with open(asset(href), encoding="utf-8") as fh:
            css.append("/* %s */\n%s" % (os.path.basename(href), fh.read()))
    html = SHEET.sub("", html)
    html = GOOGLE.sub("", html)

    block = "<style>\n%s\n%s\n</style>\n" % (font_css, "\n".join(css))
    # the block goes where the links were: still inside <head>, still before the document's own
    # trailing <style> overrides, so the cascade is the one the page was built against
    i = html.lower().find("</head>")
    if i < 0:
        raise SystemExit("no </head> — not a document this script understands")
    html = html[:i] + block + html[i:]

    # the logo, and any other relative asset the page still points at
    for rel in sorted(set(re.findall(r'(?:src|href)="(\.\./[^"]+)"', html))):
        p = asset(rel)
        kind = ("image/svg+xml" if p.endswith(".svg") else
                "image/png" if p.endswith(".png") else "application/octet-stream")
        with open(p, "rb") as fh:
            uri = "data:%s;base64,%s" % (kind, base64.b64encode(fh.read()).decode("ascii"))
        html = html.replace('"%s"' % rel, '"%s"' % uri)
    return html


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", help="a directory of issued HTML, or one file")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    src = os.path.join(HERE, a.src) if not os.path.isabs(a.src) else a.src
    files = sorted(glob.glob(os.path.join(src, "*.html"))) if os.path.isdir(src) else [src]
    if not files:
        raise SystemExit("no HTML in %s" % src)
    out = os.path.join(HERE, a.out) if not os.path.isabs(a.out) else a.out
    os.makedirs(out, exist_ok=True)

    # one subset across the whole set, so every file carries the same faces and the archive
    # compresses instead of holding 83 different copies
    import house_fonts
    from print_coq_pdfs import FAMILIES, SUBSETS, page_text
    font_css, raw, small = house_fonts.font_face_css(page_text(files), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB upstream -> %.0f KB subset"
          % (font_css.count("@font-face"), raw / 1024.0, small / 1024.0))

    total = 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            html = fh.read()
        done = inline_one(html, font_css)
        left = re.findall(r'(?:src|href)="(?:https?:|\.\./)[^"]*"', done)
        if left:
            raise SystemExit("%s still points outside itself: %s" % (os.path.basename(f), left[:3]))
        if re.search(r"<script", done, re.I):
            raise SystemExit("%s carries a script — Word would complain" % os.path.basename(f))
        dst = os.path.join(out, os.path.basename(f))
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(done)
        total += os.path.getsize(dst)
    print("%d file(s) -> %s  (%.1f MB)" % (len(files), out, total / 1e6))
    print("every file: no external reference, no relative asset, no script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
