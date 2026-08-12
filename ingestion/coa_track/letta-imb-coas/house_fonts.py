#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed the QCSP 001 typefaces in the document rather than linking them.

The house documents pull Montserrat and Roboto Mono from fonts.googleapis.com. That is
fine in a browser and useless everywhere else: the headless renderer that produces the
PDFs cannot reach it and silently substitutes Liberation Sans, so the PDF and the HTML
of the same specification come out looking like different documents. A controlled
document that changes appearance depending on whether Google is reachable is not one
you want to hand a regulator.

So the faces are fetched once, subset to the characters these specifications actually
use, and inlined as data URIs. Whole-family woff2 for the weights in play runs to about
940 KB — 1.25 MB once base64-encoded, per document, which is absurd for twenty pages of
text. Subsetting cuts it by roughly two orders of magnitude because the documents use a
few hundred glyphs: Latin, Cyrillic, and a handful of typographic and scientific marks
(≤ × ± · – — ° µ № Δ, superscript digits for CFU/g exponents, subscripts for aflatoxin
B₁ and the G₂ homologues).

The cache directory holds the unmodified upstream woff2 so a rebuild does not re-fetch,
and is not committed — the subset output is deterministic from it.
"""
import base64
import io
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".fontcache")

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")
# latin-ext is dropped: nothing in these documents needs it. Cyrillic carries the
# Macedonian, latin the rest.
SUBSETS = ("latin", "cyrillic")
# The Macedonian gloss that runs beside every English string is set in italic, and so
# is the "Cultivar:" label — a large share of the words on the page. The house documents
# request no italic axis, so a browser fakes it by slanting the upright face and the
# headless renderer gives up and reaches for Liberation Sans Italic instead. Requesting
# the real italics costs six more faces and removes both problems. Only the weights that
# are actually set in italic are asked for.
FAMILIES = (
    ("Montserrat", "Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500;1,700"),
    ("Roboto Mono", "Roboto+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500"),
)

# Marks that never appear in the HTML source as text — CSS ::after content, and the
# glyphs the renderer needs for the badges.
ALWAYS = "TARGETNEW0123456789.,:;()[]/|-–—·%°±×≤≥<>&#@№µΔ⁹⁴⁵₁₂ "


def _fetch(family_spec):
    """Upstream woff2 for one family: [(weight, style, subset, path)], cached on disk."""
    os.makedirs(CACHE, exist_ok=True)
    url = "https://fonts.googleapis.com/css2?family=%s&display=swap" % family_spec
    css = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read().decode()
    out = []
    for subset, block in re.findall(r"/\*\s*([a-z-]+)\s*\*/\s*(@font-face\s*\{.*?\})",
                                    css, re.S):
        if subset not in SUBSETS:
            continue
        src = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        weight = re.search(r"font-weight:\s*(\d+)", block)
        if not src:
            continue
        w = weight.group(1) if weight else "400"
        style = "italic" if "font-style: italic" in block else "normal"
        path = os.path.join(CACHE, "%s-%s-%s-%s.woff2"
                            % (family_spec.split(":")[0].replace("+", ""), w, style,
                               subset))
        if not os.path.exists(path):
            open(path, "wb").write(urllib.request.urlopen(
                urllib.request.Request(src.group(1), headers={"User-Agent": UA}),
                timeout=30).read())
        out.append((w, style, subset, path))
    return out


WEIGHT_NAME = {"400": "Regular", "500": "Medium", "600": "SemiBold",
               "700": "Bold", "800": "ExtraBold"}


def _rename(font, family, weight, slant="normal"):
    """Google's slices all carry the Thin name table whatever their weight."""
    style = WEIGHT_NAME.get(weight, weight)
    if slant == "italic":
        style = "Regular Italic" if style == "Regular" else style + " Italic"
    full = "%s %s" % (family, style)
    ps = full.replace(" ", "")
    for nid, value in ((1, family), (2, style), (4, full), (6, ps),
                       (16, family), (17, style)):
        font["name"].setName(value, nid, 3, 1, 0x409)
        font["name"].setName(value, nid, 1, 0, 0)


def _subset(path, text, family="", weight="400", slant="normal"):
    """One face cut down to `text`, returned as woff2 bytes, or None if no glyph matches."""
    from fontTools import subset as fts
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    cmap = set()
    for table in font["cmap"].tables:
        cmap |= set(table.cmap)
    wanted = {ord(c) for c in text} & cmap
    if not wanted:
        font.close()
        return None

    options = fts.Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = ["kern", "liga", "locl"]
    options.notdef_outline = False
    options.drop_tables += ["GSUB", "GPOS"]
    subsetter = fts.Subsetter(options=options)
    subsetter.populate(unicodes=wanted)
    subsetter.subset(font)

    if family:
        _rename(font, family, weight, slant)

    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    font.close()
    return buf.getvalue()


def font_face_css(text):
    """An @font-face block covering `text`, with every face inlined as a data URI."""
    chars = set(text) | set(ALWAYS)
    blocks, raw, embedded = [], 0, 0
    for family, spec in FAMILIES:
        for weight, style, subset, path in _fetch(spec):
            data = _subset(path, "".join(chars), family, weight, style)
            if not data:
                continue
            raw += os.path.getsize(path)
            embedded += len(data)
            blocks.append(
                "@font-face{font-family:'%s';font-style:%s;font-weight:%s;"
                "font-display:block;src:url(data:font/woff2;base64,%s) format('woff2');}"
                % (family, style, weight, base64.b64encode(data).decode()))
    return "\n".join(blocks), raw, embedded


if __name__ == "__main__":
    css, raw, small = font_face_css("Purely Plant Спецификација Δ⁹-THC ≤ 12.0%")
    print("faces: %d   upstream %.1f KB -> subset %.1f KB (%.1f%%)"
          % (css.count("@font-face"), raw / 1024.0, small / 1024.0,
             100.0 * small / raw if raw else 0))
