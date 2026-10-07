#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the specification sheets to PDF — one A4 page each, fonts embedded.

    python3 deliverables/qc_gap_analysis/specs/print_qcsp_imb.py

The same pipeline the certificates use. The page loads Montserrat, Roboto Mono and Orbitron
from Google Fonts by <link>; a renderer with no route to Google substitutes silently, which
moves every column measured against Roboto Mono's advance. The faces are fetched once,
subset to the characters the set prints, inlined as @font-face data URIs, and Google is
blocked at the network layer for the run.

**Print-safe, by default** (Head of QC, 07.10.2026: *"The printer is printing white pages when printing the
specifications"*). The sheet's design fades its bands, rows and footer rim with CSS masks and opacities, and
Chromium writes those as transparency: every sheet carried 58 page-sized images, 29 soft masks and 78 transparency
groups (the certificates carry none). A printer that runs out of memory flattening that much transparency prints
a white page. So each sheet is printed in two passes over the same layout and joined:

1. **background** — the page with every glyph made transparent (text shadows stay), rendered by MuPDF to one
   opaque 300 dpi image: the bands, rules, fades, logo and shadows exactly as drawn, with no transparency left;
2. **text** — the page with every background, border, shadow, mask, filter, image and opacity switched off, so
   only the glyphs print, as vector text in the house faces at the same positions. A text colour with alpha is
   blended onto its backdrop first, so no glyph carries transparency either.

The joined page holds one opaque image under vector text: no soft mask, no group, no alpha, no blend mode. Each
sheet is refused unless it is one page, carries none of those, reads as the plain print does (bar the duplicate
glyphs text shadows add), and matches it to the eye (mean pixel difference at 100 dpi). `--vector` prints the plain,
transparent sheets instead.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

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


# a selector no stylesheet of the sheet out-ranks: the design's own rules carry !important at class specificity
HI = '*' + ':not(#_)' * 6
ALL = '%s,%s::before,%s::after,%s::marker' % (HI, HI, HI, HI)
NO_TEXT = ALL + '{color:transparent!important;-webkit-text-fill-color:transparent!important;' \
                'text-decoration-color:transparent!important}'
TEXT_ONLY = ALL + '{background:none!important;background-color:transparent!important;background-image:none!important;' \
                  'border-color:transparent!important;outline-color:transparent!important;box-shadow:none!important;' \
                  'text-shadow:none!important;-webkit-mask-image:none!important;mask-image:none!important;' \
                  '-webkit-mask:none!important;mask:none!important;filter:none!important;backdrop-filter:none!important;' \
                  'opacity:1!important;mix-blend-mode:normal!important}' + \
            ','.join(t + ':not(#_)' * 7 for t in ('img', 'svg', 'canvas')) + '{visibility:hidden!important}'
# a text colour with alpha, blended onto the nearest opaque background behind it (white if none)
OPAQUE_TEXT = """() => { let n = 0;
  const parse = c => { const m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
    const v = m[1].split(',').map(x => parseFloat(x)); return [v[0], v[1], v[2], v.length > 3 ? v[3] : 1]; };
  const backdrop = el => { for (let e = el; e; e = e.parentElement) { const b = parse(getComputedStyle(e).backgroundColor);
      if (b && b[3] >= 0.99) return b; } return [255, 255, 255, 1]; };
  for (const el of document.querySelectorAll('*')) { const c = parse(getComputedStyle(el).color);
    if (c && c[3] < 1 && c[3] > 0) { const b = backdrop(el), m = i => Math.round(c[i] * c[3] + b[i] * (1 - c[3]));
      el.style.setProperty('color', `rgb(${m(0)},${m(1)},${m(2)})`, 'important'); n++; } }
  return n; }"""
DPI = 300


def transparency(doc):
    """What in a PDF asks the printer to flatten: soft-masked images, transparency groups, alpha, blend modes."""
    found = []
    for x in range(1, doc.xref_length()):
        get = lambda k: doc.xref_get_key(x, k)
        if get('Subtype')[1] == '/Image' and get('SMask')[0] != 'null':
            found.append('soft mask')
        if get('Group')[0] != 'null':
            found.append('group')
        if get('Type')[1] == '/ExtGState':
            sm, ca, CA, bm = get('SMask'), get('ca'), get('CA'), get('BM')
            if sm[0] != 'null' and sm[1] != '/None':
                found.append('soft mask')
            if any(v[0] != 'null' and float(v[1]) < 1 for v in (ca, CA)):
                found.append('alpha')
            if bm[0] != 'null' and bm[1] not in ('/Normal', '/Compatible'):
                found.append('blend')
    return sorted(set(found))


def print_safe(chosen, css, chromium):
    """Each sheet as one opaque 300 dpi background under its vector text; see the module note."""
    import pymupdf
    tmp = tempfile.mkdtemp(prefix='qcsp_print_')
    dirs = {k: os.path.join(tmp, k) for k in ('vector', 'background', 'text')}
    for d in dirs.values():
        os.makedirs(d)
    blended = []
    render(chosen, dirs['vector'], chromium, css)
    render(chosen, dirs['background'], chromium, css + NO_TEXT)
    render(chosen, dirs['text'], chromium, css + TEXT_ONLY,
           probe=lambda src, page: blended.append(page.evaluate(OPAQUE_TEXT)))
    made, bad = [], []
    for src in chosen:
        name = os.path.basename(src)[:-5] + '.pdf'
        vec, bg, tx = (pymupdf.open(os.path.join(dirs[k], name)) for k in ('vector', 'background', 'text'))
        if not (vec.page_count == bg.page_count == tx.page_count == 1):
            bad.append('%s: %d/%d/%d pages' % (name, vec.page_count, bg.page_count, tx.page_count))
            continue
        r = vec[0].rect
        out = pymupdf.open()
        page = out.new_page(width=r.width, height=r.height)
        page.insert_image(r, pixmap=bg[0].get_pixmap(dpi=DPI, alpha=False, colorspace=pymupdf.csRGB))
        page.show_pdf_page(r, tx, 0)
        out.set_metadata(vec.metadata)
        dst = os.path.join(PAGES, name)
        out.save(dst, garbage=4, deflate=True)
        out.close()
        got = pymupdf.open(dst)
        left = transparency(got)
        words = lambda t: sorted(t.split())
        want_text = ''.join(tx[0].get_text().split())
        a = vec[0].get_pixmap(dpi=100, alpha=False).samples
        b = got[0].get_pixmap(dpi=100, alpha=False).samples
        mean = sum(abs(x - y) for x, y in zip(a, b)) / float(len(a))
        if left:
            bad.append('%s still carries %s' % (name, ', '.join(left)))
        if ''.join(got[0].get_text().split()) != want_text:
            bad.append('%s: the text layer did not survive the join' % name)
        # a text shadow prints its glyphs twice, and the plain print's extraction can split the copy off as a word
        # of its own ("SATIVA60" and "60") or run it into the word ("☒☒HYBRID"); so runs of one character are
        # collapsed on both sides, and a word found inside another is not missing
        once = lambda w: re.sub(r'(.)\1+', r'\1', w)
        have = {once(w) for w in words(got[0].get_text())}
        missing = {w for w in {once(w) for w in words(vec[0].get_text())} - have if not any(w in h for h in have)}
        if missing:
            bad.append('%s: words of the plain print missing: %s' % (name, ' '.join(sorted(missing))[:200]))
        if mean > 2.0:
            bad.append('%s differs from the plain print (mean %.2f / 255)' % (name, mean))
        got.close()
        for d in (vec, bg, tx):
            d.close()
        made.append(dst)
    shutil.rmtree(tmp, ignore_errors=True)
    if bad:
        raise SystemExit('print-safe sheets refused:\n  ' + '\n  '.join(bad))
    print('print-safe: %d sheets, one opaque %d dpi background under vector text; %d text colours with alpha blended'
          % (len(made), DPI, sum(blended)))
    return made


def main(argv=()):
    """Print every sheet, or only the sheets named (file names under SHEETS/): a rebuild that changes a few
    sheets reprints those and leaves every other PDF as it is. The font subset is always cut from the whole set."""
    sheets = sorted(glob.glob(os.path.join(SHEETS, "*.html")))
    if not sheets:
        raise SystemExit("no sheets — run build_qcsp_imb.py first")
    vector = '--vector' in argv
    argv = [a for a in argv if a != '--vector']
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
    made = render(chosen, PAGES, chromium, css) if vector else print_safe(chosen, css, chromium)
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
