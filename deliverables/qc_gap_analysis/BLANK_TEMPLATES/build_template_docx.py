#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The three blank templates as Word, one text box per whole field.

    python3 deliverables/qc_gap_analysis/BLANK_TEMPLATES/build_template_docx.py

A template is a document somebody types into, which is what makes it different from a
certificate. `pdf_to_docx_exact.py` gives a certificate one positioned box per PDF text
span, and that is right for a record nobody edits — but a span is whatever the renderer
happened to draw, so `[MANUFACTURE DATE]` arrives as `[MANUFACTUR` and `E DATE]`, and
nobody can type a date into two boxes. The owner put it plainly:

    "is it possible that the individual text boxes follow some logical wholeness?
     not just with 3 or 5 words"

Merging boxes by their positions on the page was tried and measured, and it is not safe.
Taking neighbours that sit on one baseline joined two separate tick pills into
`HYBRIDINDICA`; tightening the rule until that stopped happening left the median box at
two words, which is the complaint again. Ink position does not say what belongs together.

The HTML does. Every field of these templates is already an element — `<span class="ph">`
for a placeholder, one element per cell — so this script reads the **DOM** for the
boundaries in the very pass that prints the page, and leaves the **PDF** to say where the
ink goes. The box is a field; the page is untouched. A box takes the element's own width,
so typing a longer value wraps inside the field instead of running off the page.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(GAP, "design_handoff", "toolchain"))
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, render          # noqa: E402
import house_fonts                                                       # noqa: E402
import pdf_to_docx_exact as X                                            # noqa: E402

PDF = os.path.join(HERE, "PDF")
OUT = os.path.join(HERE, "DOCX")

# Every field of the page, read off the laid-out document. A leaf is an element whose
# children are all inline — the smallest thing that is still a whole field — and a
# placeholder is always its own field so that typing into it cannot take the label with
# it. Coordinates come back relative to the page box and in its own units; the caller
# scales them by the printed page's width, which is the one measurement that ties the
# browser's pixels to the PDF's points without either being assumed.
PROBE = """() => {
  const page = document.querySelector('.page') || document.body;
  const pr = page.getBoundingClientRect();
  const INLINE = new Set(['SPAN','A','B','I','EM','STRONG','SUP','SUB','SMALL','BR','U',
                          'CODE','TT','LABEL','ABBR','WBR','S','MARK','FONT','BDI','Q']);
  const out = [];
  const take = (el, ph) => {
    const r = el.getBoundingClientRect();
    const t = (el.innerText || el.textContent || '').trim();
    if (!t || r.width <= 0 || r.height <= 0) return;
    // The computed face matters as much as the box. A placeholder is set in italic at a
    // weight Montserrat has no true italic for, so the renderer synthesises the slant and
    // embeds it as a Type3 font — which carries no family name at all. Forty-six of the
    // fifty-one placeholder spans came out that way, and every one of them would have been
    // left in the page image rather than made into a box anybody can type in. The DOM
    // knows what the face was meant to be; the PDF does not.
    const cs = getComputedStyle(el);
    out.push({x: r.x - pr.x, y: r.y - pr.y, w: r.width, h: r.height, text: t, ph: ph,
              ff: cs.fontFamily, fw: cs.fontWeight, fs: cs.fontStyle});
  };
  const walk = (el) => {
    if (el.classList && el.classList.contains('ph')) { take(el, true); return; }
    const kids = Array.from(el.children);
    const leaf = kids.every(k => INLINE.has(k.tagName));
    if (leaf) {
      take(el, false);
      // Every placeholder INSIDE this leaf, however deeply — not just its own children.
      // Looking only one level down found four of the certificate's forty-nine, and the
      // other forty-five were left to be boxed by whatever geometry happened to cover
      // them, which is how `[PRODUCTION BATCH]` stayed in two pieces.
      el.querySelectorAll('.ph').forEach(k => take(k, true));
      return;
    }
    kids.forEach(walk);
  };
  walk(page);
  return {pw: pr.width, ph: pr.height, fields: out};
}"""


def measure(sheets, css, chromium):
    """Print each template and collect its field map in the same pass."""
    got = {}

    def probe(src, page):
        page.emulate_media(media="print")     # measure the layout that will be PRINTED
        got[src] = page.evaluate(PROBE)

    made = render(sheets, PDF, chromium, css, probe=probe)
    return made, got


HOUSE = {"montserrat": "Montserrat", "roboto mono": "Roboto Mono", "orbitron": "Orbitron"}


def house_face(family, weight, style):
    """(family, weight, italic) for a computed CSS font, or None if it is not ours."""
    for part in (family or "").split(","):
        name = part.strip().strip("'\"").lower()
        if name in HOUSE:
            try:
                w = int(weight)
            except (TypeError, ValueError):
                w = 700 if str(weight).lower() == "bold" else 400
            return [HOUSE[name], w, str(style or "").lower().startswith("italic")]
    return None


def fields_for(raw, pdf_path):
    """The probe's pixels as points, ordered so the most specific field claims first."""
    import pymupdf
    d = pymupdf.open(pdf_path)
    w_pt = d[0].rect.width
    d.close()
    scale = w_pt / raw["pw"] if raw["pw"] else 0.75
    out = []
    for f in raw["fields"]:
        out.append({"x": f["x"] * scale, "y": f["y"] * scale,
                    "w": f["w"] * scale, "h": f["h"] * scale,
                    "text": f["text"], "ph": f["ph"],
                    "face": house_face(f.get("ff"), f.get("fw"), f.get("fs"))})
    # A placeholder first, then the smallest box: a field must be claimed by the element
    # that IS it, not by an ancestor that happens to contain it.
    out.sort(key=lambda f: (0 if f["ph"] else 1, f["w"] * f["h"]))
    return {0: out}


def words(docx):
    """(boxes, median words per box) of a built document, for the before/after."""
    import zipfile
    import re as _re
    from lxml import etree
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    root = etree.fromstring(zipfile.ZipFile(docx).read("word/document.xml"))
    counts = []
    for p in root.iter(W + "p"):
        if p.find(".//" + W + "framePr") is None:
            continue
        t = "".join(n.text or "" for n in p.iter(W + "t"))
        if t.strip():
            counts.append(len(t.split()))
    counts.sort()
    return len(counts), (counts[len(counts) // 2] if counts else 0)


def main():
    sheets = sorted(os.path.join(HERE, n) for n in os.listdir(HERE)
                    if n.endswith(".html"))
    if not sheets:
        raise SystemExit("no templates in %s" % HERE)
    os.makedirs(PDF, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    css, rawkb, subkb = house_fonts.font_face_css(page_text(sheets), FAMILIES, SUBSETS)
    print("fonts: %d faces, %.0f KB -> %.0f KB subset"
          % (css.count("@font-face"), rawkb / 1024.0, subkb / 1024.0))
    import glob
    chromium = (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    made, probed = measure(sheets, css, chromium)

    rows = []
    for src, pdf_path in zip(sheets, made):
        name = os.path.basename(pdf_path)[:-4]
        fields = fields_for(probed[src], pdf_path)
        docx = os.path.join(OUT, name + ".docx")

        plain = os.path.join(OUT, "." + name + ".span.docx")
        X.convert(pdf_path, plain, dpi=300, fonts=False, quiet=True)
        before = words(plain)
        os.remove(plain)

        X.convert(pdf_path, docx, dpi=300, fonts=True, quiet=True, fields=fields)
        after = words(docx)
        rows.append((name, before, after, os.path.getsize(docx) / 1e6, len(fields[0])))

    print("\n%-38s %14s %14s %8s" % ("", "one box/span", "one box/field", "size"))
    for name, b, a, mb, nf in rows:
        print("%-38s %6d / %-5s %6d / %-5s %6.2f MB   (%d DOM fields)"
              % (name[:38], b[0], "%d w" % b[1], a[0], "%d w" % a[1], mb, nf))
    return 0


if __name__ == "__main__":
    sys.exit(main())
