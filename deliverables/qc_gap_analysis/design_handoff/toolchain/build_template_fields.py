#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The DOM field probe, shared by the blank-template builder and the fleet builder.

Lifted verbatim from `BLANK_TEMPLATES/build_template_docx.py`, which established it, so
that the populated fleets box their fields by exactly the rule the blank templates do.
Nothing here is new; the comments are that script's own.
"""
import os

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


