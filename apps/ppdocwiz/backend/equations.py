"""LaTeX formulas in the Doc Wiz: check and preview (04.11.2026).

pp_math (pandoc -> native Word equation) is the ONE converter. The UI asks this module two things:
  check_text   every $…$ / $$…$$ of a text: does it convert? (the same call the build makes, so the check and the
               document can never disagree)
  preview_png  how one formula prints: the real equation, through the same renderer as the PDF (Gotenberg, or local
               LibreOffice with Math), cropped to the formula. A browser-side maths library would be a second engine
               that accepts or draws things pandoc does not, so none is used.
"""
import base64
import hashlib
import os
import re
import subprocess
import tempfile
from collections import OrderedDict

import pp_math
import pp_report

MAX_FORMULA = 1500
MAX_TEXT = 200_000
MAX_FORMULAS = 300
_DPI = 200
_CACHE: "OrderedDict[str, bytes]" = OrderedDict()


def check_text(text: str) -> dict:
    """{'ok': bool, 'engine': {...}, 'formulas': [{'latex', 'display', 'ok', 'error'}]} for every formula in text."""
    rows = []
    for kind, latex in pp_math.pieces(text[:MAX_TEXT]):
        if kind not in ("math", "display"):
            continue
        if len(rows) >= MAX_FORMULAS:
            break
        err = ""
        if len(latex) > MAX_FORMULA:
            err = "formula is longer than %d characters" % MAX_FORMULA
        else:
            try:
                pp_math.to_omml_xml(latex, display=(kind == "display"))
            except pp_math.MathError as e:
                err = str(e)
        rows.append({"latex": latex, "display": kind == "display", "ok": not err, "error": err})
    return {"ok": all(r["ok"] for r in rows), "engine": pp_math.status(), "formulas": rows}


def _crop_box(pdf: str):
    """(x, y, w, h) in pixels at _DPI round all text on page 1 (the equation's glyphs), or None."""
    out = subprocess.run(["pdftotext", "-bbox", "-f", "1", "-l", "1", pdf, "-"], capture_output=True, timeout=30).stdout.decode("utf-8", "ignore")
    xs = [(float(a), float(b), float(c), float(d)) for a, b, c, d in
          re.findall(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"', out)]
    if not xs:
        return None
    k, pad = _DPI / 72.0, 8
    x0, y0 = min(a for a, _, _, _ in xs), min(b for _, b, _, _ in xs)
    x1, y1 = max(c for _, _, c, _ in xs), max(d for _, _, _, d in xs)
    return max(0, int(x0 * k) - pad), max(0, int(y0 * k) - pad), int((x1 - x0) * k) + 2 * pad, int((y1 - y0) * k) + 2 * pad


def preview_png(latex: str, display: bool, render_pdf) -> bytes:
    """PNG of one formula as it prints. render_pdf(docx, pdf) is the app's renderer (it serialises local LibreOffice)."""
    key = hashlib.sha1(("%d|%s" % (display, latex)).encode("utf-8")).hexdigest()
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    from docx import Document
    from docx.shared import Cm
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Cm(24), Cm(6)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(1)
    p = d.add_paragraph()
    pp_report._math_or_text(p, latex, display, "000000", False, 16)
    with tempfile.TemporaryDirectory() as t:
        docx, pdf, png = os.path.join(t, "f.docx"), os.path.join(t, "f.pdf"), os.path.join(t, "f")
        d.save(docx)
        render_pdf(docx, pdf)
        cmd = ["pdftoppm", "-r", str(_DPI), "-png", "-singlefile", "-f", "1", "-l", "1"]
        box = _crop_box(pdf)
        if box:
            cmd += ["-x", str(box[0]), "-y", str(box[1]), "-W", str(box[2]), "-H", str(box[3])]
        subprocess.run(cmd + [pdf, png], check=True, capture_output=True, timeout=60)
        data = open(png + ".png", "rb").read()
    _CACHE[key] = data
    while len(_CACHE) > 64:
        _CACHE.popitem(last=False)
    return data


def preview_b64(latex: str, display: bool, render_pdf) -> str:
    return base64.b64encode(preview_png(latex, display, render_pdf)).decode("ascii")
