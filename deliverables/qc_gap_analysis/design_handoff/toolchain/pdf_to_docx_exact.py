#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A Word file that is the PDF page, not a reconstruction of it.

    python3 pdf_to_docx_exact.py IN.pdf OUT.docx [--dpi 300] [--no-fonts]
    python3 pdf_to_docx_exact.py --batch IN_DIR OUT_DIR [--dpi 300] [--jobs 4]

Why this exists
---------------
The desk first exported Word from the HTML the certificate is built from. The owner
looked at the result and said what any inspector would say: *"a totally different file,
different design, different structure, different everything — that will not do in a GMP
environment."* He is right. An HTML-to-Word writer re-flows the document: it decides
where lines break and how tall a row is, and the page that comes out is a page nobody
approved.

`pdf2docx` was the next attempt and is better, but it is still a re-flow — it reads the
PDF, guesses at paragraphs, columns and tables, and rebuilds them. On CoQ-PP_26-013 it
clipped the RESULT column off the right edge, overlapped the section bars with their
labels, and spilled one A4 page onto two.

This converter does not reconstruct anything. It takes the printed page as given:

* **the page stays the page.** Every rule, bar, panel, logo and signature the PDF draws
  is kept — vector art and images are not touched — and rendered as the page's
  background at print resolution.
* **the text becomes text, where it already is.** Each text span is removed from that
  background and re-emitted as a real Word run inside a positioned frame
  (``w:framePr``, anchored to the page, in twips) at the coordinates the PDF gives it.
  Nothing re-flows, because nothing flows: there is no paragraph stream to break.
* **the faces travel with the file.** `embed_fonts.py` embeds Montserrat, Roboto Mono
  and Orbitron, so a run is as wide in Word as it is in the PDF on a machine that has
  never heard of them.

The result opens in Word as an ordinary document with selectable, editable, searchable
text, and looks like the certificate because it *is* the certificate's own page.

What stays in the background
----------------------------
A handful of spans are glyph-level fallbacks the browser reached for — ``☒ ☐ ≤ ∑ Δ``
and the superscripts — carried by DejaVu and Liberation rather than a house face. Those
are left in the page layer: they print exactly as the PDF prints them, and they are not
text anybody edits. Everything else — all of the Latin and Cyrillic content — is a run.

Calibration
-----------
Word places a framed line by its own rules, not by the PDF's baseline, so the frame
origin needs an offset. It is not guessed: ``--calibrate`` converts the output back to
PDF through LibreOffice, matches the spans by their text, and reports the median
displacement. The constants below are what that measurement returned.
"""
import argparse
import copy
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pymupdf
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

EMU_PER_PT = 12700
TWIP_PER_PT = 20

# TEXT_INHIBIT_SPACES matters more than it sounds. Left to itself PyMuPDF puts a space
# wherever it sees a gap between glyphs, so the letter-spaced subtitle comes back as
# "С Е Р Т И Ф И К А Т З А К В А Л И Т Е Т" — forty-one characters where the page draws
# twenty-one. Set plainly that is the wrong text to copy out of the document, and it is
# also too wide, so the correction squeezes it until the real word spaces close up.
TEXT_FLAGS = (pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE
              | pymupdf.TEXT_INHIBIT_SPACES)

# Where a framed run lands relative to the span's own bbox, in points, as measured by
# --calibrate against LibreOffice's render of the output. See the module docstring.
FRAME_DX = -0.100
FRAME_DY_A = 0.014
# Per family, because Word seats a line inside a box it sizes from the face's own ascent:
# the same type size drops Orbitron and Roboto Mono differently from Montserrat.
FRAME_DY_B = {"Montserrat": 0.3058, "Orbitron": 0.2083, "Roboto Mono": 0.2439}
FRAME_DY_B_DEFAULT = 0.2165

# The PDF names a face per weight; Word knows four styles per family name, so
# embed_fonts.face_name() gives each weight its own family. Map one to the other.
_FACE = re.compile(r"^(Montserrat|RobotoMono|Orbitron)"
                   r"(Thin|ExtraLight|Light|Regular|Medium|SemiBold|Bold|ExtraBold|Black|\d{3})?"
                   r"(Italic)?$")
_FAMILY = {"Montserrat": "Montserrat", "RobotoMono": "Roboto Mono", "Orbitron": "Orbitron"}
_WEIGHT = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500,
           "SemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900, None: 400, "": 400}


def face_of(pdf_font):
    """(family, weight, italic) for a PDF font name, or None if it is not a house face.

    >>> face_of("MontserratMediumItalic")
    ('Montserrat', 500, True)
    >>> face_of("RobotoMonoSemiBold")
    ('Roboto Mono', 600, False)
    >>> face_of("Orbitron900")
    ('Orbitron', 900, False)
    >>> face_of("DejaVuSansMono") is None
    True
    """
    name = pdf_font.split("+")[-1].replace("-", "").replace(" ", "")
    m = _FACE.match(name)
    if not m:
        return None
    fam, w, it = m.group(1), m.group(2), m.group(3)
    weight = int(w) if (w or "").isdigit() else _WEIGHT.get(w, 400)
    return _FAMILY[fam], weight, bool(it)


def _el(tag, **attrs):
    e = OxmlElement(tag if ":" in tag else "w:" + tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e


def _sub(parent, tag, **attrs):
    e = _el(tag, **attrs)
    parent.append(e)
    return e


# CT_RPr is a sequence, not a bag: Word reads `w:spacing` only where the schema puts it,
# between `w:color` and `w:w`, and a file that appends it after `w:sz` is one Word calls
# unreadable. python-docx has no accessor for it, so insert by the schema's own order.
_RPR_ORDER = ("rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike",
              "dstrike", "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid",
              "vanish", "webHidden", "color", "spacing", "w", "kern", "position", "sz",
              "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign",
              "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath")
_RPR_INDEX = {qn("w:" + t): i for i, t in enumerate(_RPR_ORDER)}


def rpr_set(rPr, tag, **attrs):
    """Put `tag` into `rPr` at the position CT_RPr's sequence requires."""
    name = qn("w:" + tag)
    for existing in rPr.findall(name):
        rPr.remove(existing)
    e = _el(tag, **attrs)
    rank = _RPR_INDEX.get(name, len(_RPR_ORDER))
    for i, child in enumerate(rPr):
        if _RPR_INDEX.get(child.tag, len(_RPR_ORDER)) > rank:
            rPr.insert(i, e)
            return e
    rPr.append(e)
    return e


def page_setup(section, width_pt, height_pt):
    """A4 (or whatever the PDF is), no margins: the frames carry every position."""
    section.page_width = Emu(int(round(width_pt * EMU_PER_PT)))
    section.page_height = Emu(int(round(height_pt * EMU_PER_PT)))
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin",
                 "header_distance", "footer_distance", "gutter"):
        setattr(section, side, Emu(0))


def float_behind(run_picture, width_pt, height_pt, z):
    """Turn python-docx's inline picture into an anchor pinned to the page corner.

    python-docx only writes `wp:inline`, which sits in the text flow and pushes the
    first line down a page's worth. The background has to be behind the text and out of
    the flow, which is `wp:anchor` with behindDoc and an absolute position.
    """
    ns = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    drawing = run_picture._inline.getparent()
    inline = run_picture._inline
    anchor = OxmlElement("wp:anchor")
    for k, v in (("distT", "0"), ("distB", "0"), ("distL", "0"), ("distR", "0"),
                 ("simplePos", "0"), ("relativeHeight", str(z)), ("behindDoc", "1"),
                 ("locked", "0"), ("layoutInCell", "1"), ("allowOverlap", "1")):
        anchor.set(k, v)
    sp = OxmlElement("wp:simplePos"); sp.set("x", "0"); sp.set("y", "0")
    anchor.append(sp)
    for tag, rel in (("wp:positionH", "page"), ("wp:positionV", "page")):
        pos = OxmlElement(tag)
        pos.set("relativeFrom", rel)
        off = OxmlElement("wp:posOffset")
        off.text = "0"
        pos.append(off)
        anchor.append(pos)
    ext = OxmlElement("wp:extent")
    ext.set("cx", str(int(round(width_pt * EMU_PER_PT))))
    ext.set("cy", str(int(round(height_pt * EMU_PER_PT))))
    anchor.append(ext)
    ee = OxmlElement("wp:effectExtent")
    for k in ("l", "t", "r", "b"):
        ee.set(k, "0")
    anchor.append(ee)
    anchor.append(OxmlElement("wp:wrapNone"))
    for child in inline:
        if child.tag.startswith("{%s}" % ns) and child.tag.endswith(("}extent", "}effectExtent")):
            continue
        anchor.append(copy.deepcopy(child))
    drawing.remove(inline)
    drawing.append(anchor)


_METRIC = {}


def metric_font(family, weight, italic):
    """The very TTF that will be embedded, opened for measuring."""
    key = (family, weight, italic)
    if key not in _METRIC:
        try:
            from embed_fonts import instance
            path = instance(family, weight, italic)
            _METRIC[key] = pymupdf.Font(fontfile=path) if path else None
        except Exception:
            _METRIC[key] = None
    return _METRIC[key]


def tracking(text, size, want_pt, family, weight, italic):
    """How much wider the run has to be made, in twips, to fill the PDF's own box.

    Two things need this. The certificate letter-spaces its titles and its section bars
    in CSS, which a PDF stores as ordinary text drawn at chosen positions — set plainly,
    `СЕРТИФИКАТ ЗА КВАЛИТЕТ` is two thirds of the width the page gives it. And Word holds
    a type size only to the nearest half-point, so a table set at 15.975 pt is set at
    16 pt and every run in it is a shade wide or narrow, which walks a right-aligned
    column off its own edge.

    Both are the same measurement: the width the page gives the run, less the width the
    embedded face renders it at, at the size Word will actually use. `split_tracking`
    turns that into the per-character spacing to carry it.
    """
    font = metric_font(family, weight, italic)
    if font is None or not text:
        return 0
    try:
        have = font.text_length(text, fontsize=size)
    except Exception:
        return 0
    if have <= 0:
        return 0
    return int(round((want_pt - have) * TWIP_PER_PT))


def split_tracking(total_twips, n):
    """Per-character spacing for two runs that together widen the text by `total_twips`.

    Two things are going on. `w:spacing` is one whole twip per character, so a
    sixty-character line could only be corrected in steps of three points; giving the
    first `r` characters one twip more than the rest brings that down to a twentieth of
    a point. And spacing after the LAST character moves nothing visible — the glyphs
    still end where they ended — so the correction is spread over the n-1 gaps between
    characters, not over the characters. That last point was worth 1.6 pt on the title.

    Returns (spacing for the first `r` characters, r); the rest take one twip less.

    >>> split_tracking(7, 4)
    (3, 1)
    >>> split_tracking(-7, 4)
    (-2, 2)
    >>> split_tracking(6, 4)
    (2, 0)
    >>> split_tracking(5, 1)
    (0, 0)
    """
    gaps = n - 1
    if gaps <= 0:
        return 0, 0
    k = total_twips // gaps                    # floors towards minus infinity, as wanted
    r = total_twips - k * gaps
    return k + (1 if r else 0), r


def add_span(doc, span, page_w_pt):
    """One PDF text span as a Word paragraph frozen at the PDF's own coordinates."""
    face = face_of(span["font"])
    if face is None:
        return False
    family, weight, italic = face
    try:
        from embed_fonts import face_name
        fam, bold, ital = face_name(family, weight, italic)
    except Exception:                                     # the mapping is the same shape
        fam, bold, ital = family, weight >= 700, italic

    x0, y0, x1, y1 = span["bbox"]
    # Word measures type in HALF-points and nothing finer, so the PDF's 15.975 pt is a
    # size Word cannot hold. python-docx truncated it to 15.5 and every run came out
    # three per cent narrow — the right-hand column ended 9 pt short of its own edge.
    # Round to the nearest half-point and then measure against THAT, so the width the
    # tracking corrects to is the width Word will actually set.
    size = max(0.5, round(span["size"] * 2) / 2.0)
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()

    # The frame: anchored to the page, positioned in twips, taking part in no flow.
    # Width is the span's own, with a point of slack; clamped so Word never pulls a
    # frame back inside the page and takes the right-hand column with it.
    w = min(max(x1 - x0 + 2.0, 4.0), max(page_w_pt - x0 - 0.5, 4.0))
    track = tracking(span["text"], size, x1 - x0, family, weight, italic)
    pPr.append(_el("framePr", w=int(round(w * TWIP_PER_PT)),
                   hRule="auto", wrap="none", vAnchor="page", hAnchor="page",
                   x=int(round((x0 + FRAME_DX) * TWIP_PER_PT)),
                   y=int(round((y0 + FRAME_DY_A
                                 + FRAME_DY_B.get(family, FRAME_DY_B_DEFAULT) * size)
                                * TWIP_PER_PT))))
    # CT_PPr is a sequence too, and its order is framePr, spacing, ind, jc — not the
    # order they were written in. Word refuses a document whose pPr children are out of
    # order outright, with nothing more helpful than "unreadable content".
    _sub(pPr, "spacing", before=0, after=0,
         line=int(round(size * TWIP_PER_PT)), lineRule="exact")
    _sub(pPr, "ind", left=0, right=0, firstLine=0)
    _sub(pPr, "jc", val="left")

    text = span["text"]
    hi, r = split_tracking(track, len(text)) if abs(track) >= 3 else (0, 0)
    lo = hi - 1 if r else hi
    parts = [(text[:r], hi), (text[r:], lo)] if 0 < r < len(text) else [(text, hi)]

    c = int(span.get("color", 0))
    colour = RGBColor((c >> 16) & 255, (c >> 8) & 255, c & 255)
    for chunk, sp in parts:
        if not chunk:
            continue
        run = p.add_run(chunk)
        run.font.name = fam
        run.font.bold = bold
        run.font.italic = ital
        run.font.color.rgb = colour
        rPr = run._r.get_or_add_rPr()
        rf = rPr.find(qn("w:rFonts"))
        if rf is None:
            rf = _el("rFonts")
            rPr.insert(0, rf)
        for a in ("ascii", "hAnsi", "cs", "eastAsia"):
            rf.set(qn("w:" + a), fam)
        rpr_set(rPr, "sz", val=int(round(size * 2)))
        rpr_set(rPr, "szCs", val=int(round(size * 2)))
        if sp:
            rpr_set(rPr, "spacing", val=sp)
        # Kerning off: the width was measured from the face's plain advances, and Word's
        # kerning would pull the run in again under the correction just applied.
        rpr_set(rPr, "kern", val=0)
    return True


def convert_page(page, doc, dpi, first):
    """Redact the house-font text out of the page, print what is left, replace the text."""
    spans, keep = [], []
    for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for s in line["spans"]:
                if not s["text"].strip():
                    continue
                (spans if face_of(s["font"]) else keep).append(s)

    # Take only the spans that will come back as runs. A redaction removes any glyph
    # whose box meets the rectangle, and the symbol fallbacks sit flush against their
    # neighbours in the same line, so the rectangle is pulled in a third of a point.
    for s in spans:
        x0, y0, x1, y1 = s["bbox"]
        page.add_redact_annot(pymupdf.Rect(x0 + 0.3, y0 + 0.2, x1 - 0.3, y1 - 0.2), fill=False)
    if spans:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)

    rect = page.rect
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    png = pix.tobytes("png")

    section = doc.sections[-1] if first else doc.add_section()
    page_setup(section, rect.width, rect.height)

    bg = doc.add_paragraph()
    bgPr = bg._p.get_or_add_pPr()
    _sub(bgPr, "spacing", before=0, after=0, line=20, lineRule="exact")
    run = bg.add_run()
    pic = run.add_picture(io.BytesIO(png), width=Emu(int(round(rect.width * EMU_PER_PT))))
    float_behind(pic, rect.width, rect.height, 1 + page.number)

    n = sum(1 for s in spans if add_span(doc, s, rect.width))
    return n, len(keep)


def convert(src, out, dpi=300, fonts=True, quiet=False):
    doc = Document()
    pdf = pymupdf.open(src)
    placed = kept = 0
    for i, page in enumerate(pdf):
        a, b = convert_page(page, doc, dpi, i == 0)
        placed += a
        kept += b
    # The redactions are made on the in-memory page and the document is closed without
    # being saved, so the controlled PDF on disk is never written to. A certificate is a
    # record; converting it must not touch it.
    pdf.close()
    doc.save(out)
    if fonts:
        subprocess.run([sys.executable, os.path.join(HERE, "embed_fonts.py"), out],
                       check=True, stdout=subprocess.DEVNULL)
    bad = check_order(out)
    if bad:
        raise SystemExit("%s is malformed and Word would refuse it:\n  %s"
                         % (out, "\n  ".join(bad)))
    if not quiet:
        print("%s  %d runs placed, %d symbol spans left on the page, %.2f MB"
              % (os.path.basename(out), placed, kept, os.path.getsize(out) / 1e6))
    return placed, kept


# ----------------------------------------------------------------------------- calibrate
def calibrate(src, dpi=300):
    """Convert, render the result back to PDF, and report the median span displacement."""
    tmp = tempfile.mkdtemp(prefix="cal")
    try:
        out = os.path.join(tmp, "cal.docx")
        convert(src, out, dpi=dpi, fonts=True, quiet=True)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, out],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        got = os.path.join(tmp, "cal.pdf")
        want = {}
        for s in _spans(src):
            want.setdefault(s["text"].strip(), []).append(s)
        dxs, pairs = [], []
        fam_pairs = {}
        for s in _spans(got):
            key = s["text"].strip()
            if key in want and len(want[key]) == 1:
                w = want[key][0]
                dxs.append(s["bbox"][0] - w["bbox"][0])
                pairs.append((w["size"], s["bbox"][1] - w["bbox"][1]))
                f = face_of(w["font"])
                if f:
                    fam_pairs.setdefault(f[0], []).append(pairs[-1])
        if not dxs:
            print("nothing matched"); return
        dxs.sort()
        mx = dxs[len(dxs) // 2]
        # dy grows with the type size, because Word seats the line inside a box it sizes
        # from the face, not from the baseline the PDF gives. Fit dy = a + b * size and
        # take the slope out of the frame origin instead of averaging it away.
        n = len(pairs)
        sx = sum(a for a, _ in pairs); sy = sum(b for _, b in pairs)
        sxx = sum(a * a for a, _ in pairs); sxy = sum(a * b for a, b in pairs)
        den = n * sxx - sx * sx
        b = (n * sxy - sx * sy) / den if den else 0.0
        a = (sy - b * sx) / n
        res = sorted(dy - (a + b * sz) for sz, dy in pairs)
        print("matched %d spans   median dx %+.3f pt  (%.3f..%.3f)"
              % (n, mx, dxs[n // 20], dxs[-max(1, n // 20)]))
        print("dy = %+.3f %+.4f * size    residual %+.3f..%+.3f pt"
              % (a, b, res[n // 20], res[-max(1, n // 20)]))
        print("set FRAME_DX = %.3f ; FRAME_DY_A = %.3f" % (FRAME_DX - mx, FRAME_DY_A - a))
        for fam in sorted(fam_pairs):
            v = sorted(fam_pairs[fam])
            slope = sorted(d / sz for sz, d in v)[len(v) // 2]
            cur = FRAME_DY_B.get(fam, FRAME_DY_B_DEFAULT)
            worst = max(abs(d) for _, d in v)
            print("   %-12s n=%3d  worst %+.3f pt   set FRAME_DY_B[%r] = %.4f"
                  % (fam, len(v), worst, fam, cur - slope))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


_PPR_ORDER = ("pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
              "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
              "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
              "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
              "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
              "suppressOverlap", "jc", "textDirection", "textAlignment",
              "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr",
              "pPrChange")


def check_order(path):
    """Every w:pPr and w:rPr in the file, against the sequence the schema fixes.

    Word does not repair a document whose property children are out of order; it
    declines to open it and says only "unreadable content", which is how an earlier
    Word export was lost. This asserts the two sequences this converter writes, so a
    malformed file is caught here rather than on the reviewer's desk.
    """
    import zipfile
    from lxml import etree
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    orders = {W + "pPr": _PPR_ORDER, W + "rPr": _RPR_ORDER}
    bad = []
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    for tag, order in orders.items():
        rank = {W + t: i for i, t in enumerate(order)}
        for el in root.iter(tag):
            seen = [rank.get(c.tag, -1) for c in el]
            named = [c.tag.split("}")[-1] for c in el]
            if any(r < 0 for r in seen):
                bad.append("%s: unknown child %s" % (tag.split("}")[-1],
                           [n for n, r in zip(named, seen) if r < 0]))
            elif seen != sorted(seen):
                bad.append("%s out of order: %s" % (tag.split("}")[-1], named))
    return sorted(set(bad))


def verify(src, dpi=150, worst=6):
    """Convert, render the result back to PDF, and report where every run landed.

    This is the evidence, not a sanity check: a converted certificate is only the
    certificate if each run starts, sits and ends where the approved page puts it. The
    numbers are in points — a point is a third of a millimetre.
    """
    tmp = tempfile.mkdtemp(prefix="ver")
    try:
        out = os.path.join(tmp, "v.docx")
        convert(src, out, dpi=dpi, fonts=True, quiet=True)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, out],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        want = {}
        for s in _spans(src):
            want.setdefault(s["text"].strip(), []).append(s)
        rows = []
        for s in _spans(os.path.join(tmp, "v.pdf")):
            k = s["text"].strip()
            if k in want and len(want[k]) == 1:
                w = want[k][0]
                rows.append((s["bbox"][0] - w["bbox"][0], s["bbox"][1] - w["bbox"][1],
                             s["bbox"][2] - w["bbox"][2], k, w["font"]))
        if not rows:
            print("%s: nothing matched" % os.path.basename(src))
            return None
        n = len(rows)
        stats = {}
        for lbl, i in (("left", 0), ("top", 1), ("right", 2)):
            v = sorted(abs(r[i]) for r in rows)
            stats[lbl] = (v[n // 2], v[int(n * 0.95)], v[-1])
        print("%s  %d runs matched" % (os.path.basename(src), n))
        for lbl in ("left", "top", "right"):
            print("   %-5s edge  median %.3f  p95 %.3f  max %.3f pt"
                  % ((lbl,) + stats[lbl]))
        if worst:
            print("   furthest off:")
            for r in sorted(rows, key=lambda r: -max(abs(r[0]), abs(r[1]), abs(r[2])))[:worst]:
                print("     %+6.2f %+6.2f %+6.2f  %-40s %s"
                      % (r[0], r[1], r[2], r[3][:40], r[4]))
        return stats
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _spans(path):
    d = pymupdf.open(path)
    out = [s for p in d for b in p.get_text("dict", flags=TEXT_FLAGS)["blocks"] if b["type"] == 0
           for l in b["lines"] for s in l["spans"] if s["text"].strip()]
    d.close()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--no-fonts", action="store_true")
    ap.add_argument("--batch", action="store_true", help="src and out are directories")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="convert, render back to PDF and report where each run landed")
    ap.add_argument("--force", action="store_true", help="batch: rewrite existing outputs")
    a = ap.parse_args(argv)
    if a.calibrate:
        return calibrate(a.src, a.dpi)
    if a.verify:
        return verify(a.src)
    if a.batch:
        os.makedirs(a.out, exist_ok=True)
        names = sorted(n for n in os.listdir(a.src) if n.lower().endswith(".pdf"))
        for i, n in enumerate(names, 1):
            dst = os.path.join(a.out, n[:-4] + ".docx")
            if os.path.exists(dst) and not a.force:
                continue
            convert(os.path.join(a.src, n), dst, a.dpi, not a.no_fonts, quiet=True)
            print("[%d/%d] %s" % (i, len(names), n), flush=True)
        return
    convert(a.src, a.out, a.dpi, not a.no_fonts)


if __name__ == "__main__":
    main()
