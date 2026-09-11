#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Tranche 1 and Tranche 2 drafts as two merged PDFs, fonts and logo embedded.

    python3 deliverables/qc_gap_analysis/live_instrument/print_coq_pdfs.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv \
        --chromium /opt/pw-browsers/chromium-1194/chrome-linux/chrome

One PDF per tranche, one page per certificate, in P-lot order. The pages are
printed by the same headless Chromium that compiles the drafts, from the same
files, so what a person reads in the PDF is what the Quality Desk renders.

## Why the fonts are embedded rather than linked

The compiled drafts pull Montserrat, Roboto Mono and Orbitron from
`fonts.googleapis.com`. In a browser that is fine. In a printer it is not: a
headless renderer that cannot reach Google silently substitutes Liberation Sans,
and a controlled document that changes appearance depending on whether a third
party is reachable is not one to hand a regulator. So the faces are fetched once,
**subset to the characters these 22 documents actually print**, and inlined as
data URIs — `house_fonts.py`, which the QCSP 001 specifications already use for
the same reason. Google is then blocked at the network layer for the whole run,
so the PDF is byte-identical whether or not the container has a route to it.

The certificate needs two things the specifications do not: **Orbitron**, which
sets the banner, and the **Greek** subset, because every sheet prints
"Total Δ⁹-THC" and a Δ outside the embedded subset is a Δ the renderer replaces.

The brand mark is already a data URI in the master, so it needs nothing.

## What is printed

`@page{size:A4;margin:0}` and a `.page` fixed at 210 × 297 mm, so
`prefer_css_page_size` gives exactly one A4 page per certificate with no printer
margin of its own. Backgrounds are printed — the DRAFT watermark, the section
rules, the selection pills and the red of every marked field are the document,
not decoration.
"""
import argparse
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
DRAFTS = os.path.join(GAP, "drafts")
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))

# The two the specifications use, plus the banner face. Orbitron carries no
# italic and only the weights the banner sets.
#
# EVERY italic weight the stylesheet sets must be listed here, or the browser
# emboldens a neighbouring italic and the synthesised face — having no outlines of
# its own — is rasterised into Type 3 glyph procedures. `.ap-cred` sets
# font-weight:600 in italic and italic 600 was missing: 39 faces in the Tranche 1
# PDF and 27 in Tranche 2 came out Type 3 while the same family embedded as
# TrueType on other pages of the same document. Pinning the variable axes, which
# removed Type 3 the first time, fixes the faces the page asks for by name; it
# cannot fix one the page never asked for.
FAMILIES = (
    ("Montserrat", "Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,500;1,600;1,700"),
    ("Roboto Mono", "Roboto+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500"),
    ("Orbitron", "Orbitron:wght@500;600;700;800;900"),
)
# latin and cyrillic carry the two languages; greek carries Δ; latin-ext the
# few accented characters a strain name can hold.
SUBSETS = ("latin", "latin-ext", "cyrillic", "greek")
BLOCK = ("**fonts.googleapis.com/**", "**fonts.gstatic.com/**")


def scope(path):
    """Draftable lots by tranche, in P-lot order."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("draftable") != "yes":
                continue
            lot = (r.get("p_lot") or "").strip()
            if not lot or lot == "—":
                continue
            out.setdefault(r["tranche"].strip(), []).append(lot)
    return {t: sorted(v) for t, v in sorted(out.items())}


def page_text(paths):
    """Every character these documents print, for the subsetter."""
    import re
    chars = set()
    for p in paths:
        html = open(p, encoding="utf-8").read()
        # attribute values and data URIs are not printed text; the tags come out
        # first so a base64 blob never reaches the character set
        html = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html)
        chars |= set(re.sub(r"<[^>]+>", " ", html))
    return "".join(sorted(chars))


def render(paths, outdir, chromium=None, css=""):
    """One A4 PDF per document, returned in the order given."""
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium) if chromium \
            else pw.chromium.launch()
        page = browser.new_page()
        for pat in BLOCK:
            page.route(pat, lambda route: route.abort())
        for src in paths:
            page.goto("file://" + os.path.abspath(src))
            if css:
                page.add_style_tag(content=css)
            page.evaluate("() => document.fonts.ready")
            dst = os.path.join(outdir, os.path.basename(src)[:-5] + ".pdf")
            page.pdf(path=dst, prefer_css_page_size=True, print_background=True)
            made.append(dst)
        browser.close()
    return made


def merge(parts, out):
    subprocess.run(["pdfunite"] + parts + [out], check=True)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", default=os.path.join(GAP, "tracker",
                                                    "coq_draft_scope_2026-09-10.csv"))
    ap.add_argument("--drafts", default=DRAFTS)
    ap.add_argument("--out", default=DRAFTS)
    ap.add_argument("--chromium", default=os.environ.get("CHROMIUM_PATH"))
    a = ap.parse_args(argv)

    import house_fonts
    tranches = scope(a.scope)
    files = {t: [os.path.join(a.drafts, "DRAFT_CoQ_%s.html" % lot) for lot in lots]
             for t, lots in tranches.items()}
    missing = [p for ps in files.values() for p in ps if not os.path.exists(p)]
    if missing:
        raise SystemExit("no compiled draft for: " + ", ".join(map(os.path.basename, missing)))

    every = [p for ps in files.values() for p in ps]
    css, raw, small = house_fonts.font_face_css(page_text(every), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB upstream -> %.0f KB subset"
          % (css.count("@font-face"), raw / 1024.0, small / 1024.0))

    tmp = os.path.join(a.out, ".pages")
    os.makedirs(tmp, exist_ok=True)
    for t, ps in files.items():
        parts = render(ps, tmp, a.chromium, css)
        out = os.path.join(a.out, "Tranche_%s_CoQ_Drafts.pdf" % t)
        merge(parts, out)
        print("Tranche %s: %d certificate(s) -> %s (%d KiB)"
              % (t, len(parts), out, os.path.getsize(out) // 1024))
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
