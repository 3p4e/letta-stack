# -*- coding: utf-8 -*-
"""
pp_math — LaTeX formulas as native, editable Word equations (OMML). The ONE converter of the engine.

Why (Head of QC, 04.11.2026: "a LaTeX formula rendering solution that will always be available for the engine, users
and AI"): until then formulas went through latex2mathml + Office's MML2OMML.XSL, or pandoc when installed. The engine
image had neither, so a formula was silently printed as raw LaTeX text. Now:

  * one backend: pandoc (LaTeX -> OMML), installed in every image and in CI; no Office file, no network, no font;
  * no silent fallback: a formula that cannot be converted raises MathError, so a document is never built with
    "\\frac{a}{b}" printed on the page. (PP_MATH_FALLBACK=text restores the old text fallback on a developer machine.)
  * the same grammar for people and for AI authors:  $x_i$  inline,  $$ … $$  display, \\$ a literal dollar sign;
  * `python pp_math.py --selftest` is run when an image is built and by the service health check.

PDF: the renderer must carry LibreOffice Math (Gotenberg does; the local fallback image installs libreoffice-math);
without it LibreOffice drops the equations from the PDF, silently.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from lxml import etree

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class MathError(ValueError):
    """A formula the engine cannot turn into a Word equation (unavailable converter, or invalid LaTeX)."""


def _pandoc():
    """The pandoc executable (PP_PANDOC overrides), or None when it is not there / not runnable."""
    exe = os.environ.get("PP_PANDOC") or shutil.which("pandoc")
    return exe if exe and os.path.isfile(exe) and os.access(exe, os.X_OK) else None


def available():
    return bool(_pandoc())


def fallback_text_allowed():
    return os.environ.get("PP_MATH_FALLBACK", "").strip().lower() == "text"


# ---- conversion -------------------------------------------------------------------------------------------------
_CACHE = {}
# Decimal comma (house rule: a comma in Macedonian, 0,877). Written 0{,}877 in LaTeX; a renderer treats the comma as
# punctuation and prints "0 , 877", so a number written that way is set upright and tight: \mathrm{0,877}.
_DECIMAL = re.compile(r"(?<![\w.])(\d+)\{,\}(\d+)(?!\d)")
# Backslash commands pandoc did not understand come back as literal text in an m:t; that is a failed formula.
_LEAK = re.compile(r"\\[A-Za-z]+")


# Names in a formula print upright (Head of QC, 04.11.2026: "Total THC", "Содржина", "M-однос" came out as spaced italic
# letters, T o t a l T H C, because a formula was written without \\text). Two or more Latin letters in a row, or any Cyrillic run,
# are a name; a single letter is a variable and stays italic. Commands (\\frac), and what is already inside \\text{} / \\mathrm{}
# / \\operatorname{}, are left alone. Write a product of variables with a space or \\cdot (a b, a\\cdot b), not ab.
_KEEP = re.compile(r"\\(?:text|mathrm|mathit|mathbf|textbf|mbox|operatorname)\s*\{[^{}]*\}|\\[A-Za-z]+\*?|\\.")
_NAME = re.compile(r"[A-Za-z]{2,}|[Ѐ-ӿ]+")
# A decimal point inside a formula is the same number as everywhere else in the document: it prints with the decimal comma.
_POINT = re.compile(r"(?<![\w.])(\d+)\.(\d+)(?!\d)")


def _upright_names(latex):
    out, pos = [], 0
    for m in _KEEP.finditer(latex):
        out.append(_NAME.sub(lambda w: "\\text{" + w.group(0) + "}", latex[pos:m.start()])); out.append(m.group(0)); pos = m.end()
    out.append(_NAME.sub(lambda w: "\\text{" + w.group(0) + "}", latex[pos:]))
    return "".join(out)


def prepare(latex):
    """The LaTeX as it is sent to pandoc: decimal separators set tight, names upright."""
    latex = re.sub(r"(?<!\\)%", r"\\%", latex)     # % is a comment in TeX and silently dropped the rest of the formula: a percent sign is literal
    latex = _POINT.sub(r"\1{,}\2", latex)
    latex = _DECIMAL.sub(r"\\text{\1,\2}", latex)
    return _upright_names(latex)


def to_omml_xml(latex, display=False):
    """OMML (bytes: an m:oMath, or an m:oMathPara when display) for one LaTeX formula."""
    key = (latex, bool(display))
    if key in _CACHE:
        return _CACHE[key]
    exe = _pandoc()
    if not exe:
        raise MathError("equation engine unavailable: pandoc is not installed (formula: %s)" % latex[:60])
    latex_src = prepare(latex)
    src = ("$$" + latex_src + "$$") if display else ("$" + latex_src + "$")
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "m.docx")
        r = subprocess.run([exe, "-f", "markdown+tex_math_dollars", "-o", out], input=src.encode("utf-8"),
                           capture_output=True)
        if r.returncode != 0:
            raise MathError("formula does not parse: %s — %s" % (latex[:60], r.stderr.decode("utf-8", "ignore")[:120]))
        root = etree.fromstring(zipfile.ZipFile(out).read("word/document.xml"))
    para = root.find(".//{%s}oMathPara" % M_NS)
    omath = root.find(".//{%s}oMath" % M_NS)
    if omath is None:
        raise MathError("formula does not parse: %s" % latex[:60])
    text = "".join(x.text or "" for x in omath.iter("{%s}t" % M_NS))
    if _LEAK.search(text):
        raise MathError("formula uses a command the engine does not know: %s" % _LEAK.search(text).group(0))
    node = para if (display and para is not None) else omath
    xml = etree.tostring(node)
    _CACHE[key] = xml
    return xml


def to_omml(latex, display=False):
    return etree.fromstring(to_omml_xml(latex, display))


def format_omml(root, color_hex=None, bold=False, size_pt=None):
    """Colour / bold / size on every math run (m:r), so a formula matches the text round it."""
    for r in list(root.iter("{%s}r" % M_NS)):
        wrpr = etree.SubElement(r, "{%s}rPr" % W_NS)
        r.remove(wrpr)
        if bold:
            etree.SubElement(wrpr, "{%s}b" % W_NS)
        if color_hex:
            etree.SubElement(wrpr, "{%s}color" % W_NS).set("{%s}val" % W_NS, color_hex)
        if size_pt:
            etree.SubElement(wrpr, "{%s}sz" % W_NS).set("{%s}val" % W_NS, str(int(round(size_pt * 2))))
        mrpr = r.find("{%s}rPr" % M_NS)
        r.insert((list(r).index(mrpr) + 1) if mrpr is not None else 0, wrpr)
    return root


# ---- the $…$ grammar --------------------------------------------------------------------------------------------
# $$…$$ display; $…$ inline: the opening $ is not followed by a space, the closing $ is not preceded by one and is not
# followed by a digit (so "5 $ and 6 $" is money, not maths). \$ is a literal dollar sign.
_MATH = re.compile(r"(?<!\\)\$\$(.+?)(?<!\\)\$\$|(?<![\\$])\$(?=\S)((?:[^$\\\n]|\\.)+?)(?<=\S)\$(?![0-9$])", re.S)


def has_math(text):
    return bool(text) and "$" in text and bool(_MATH.search(text))


def pieces(text):
    """[(kind, value)]: kind 'text' | 'math' | 'display'. A literal \\$ becomes $ in the text pieces."""
    out, pos = [], 0
    for m in _MATH.finditer(text or ""):
        if m.start() > pos:
            out.append(("text", text[pos:m.start()].replace("\\$", "$")))
        if m.group(1) is not None:
            out.append(("display", m.group(1).strip()))
        else:
            out.append(("math", m.group(2).strip()))
        pos = m.end()
    if pos < len(text or ""):
        out.append(("text", text[pos:].replace("\\$", "$")))
    return out


def whole_formula(text):
    """(latex, display) when the text is exactly one formula, else None."""
    ps = pieces((text or "").strip())
    if len(ps) == 1 and ps[0][0] in ("math", "display"):
        return ps[0][1], ps[0][0] == "display"
    return None


def formulas(text):
    """Every LaTeX formula in the text."""
    return [v for k, v in pieces(text) if k in ("math", "display")]


def strip_formulas(text):
    """The text with its formulas removed (what a fidelity count should see)."""
    return "".join(v for k, v in pieces(text) if k == "text")


def check(text):
    """Problems in the formulas of a text, as strings an author can act on ([] = all convert)."""
    problems = []
    for f in formulas(text):
        try:
            to_omml_xml(f)
        except MathError as e:
            problems.append(str(e))
    return problems


# ---- self-test --------------------------------------------------------------------------------------------------
SELFTEST = r"\text{Total THC}=\text{THC}+\left(\text{THCA}\times 0{,}877\right)\;;\;u_c=\sqrt{\sum_i u_i^2}\;;\;\frac{a}{b}"


def status():
    """{'ok': bool, 'backend': str} — cheap enough for a health endpoint (result cached after the first call)."""
    exe = _pandoc()
    if not exe:
        return {"ok": False, "backend": "none (pandoc not installed)"}
    try:
        ver = subprocess.run([exe, "--version"], capture_output=True, timeout=10).stdout.decode().splitlines()[0]
        to_omml_xml(SELFTEST)
        to_omml_xml(r"\frac{a}{b}", display=True)
        return {"ok": True, "backend": ver}
    except Exception as e:  # noqa: BLE001 — a health probe reports, never raises
        return {"ok": False, "backend": "pandoc fails its self-test: %s" % str(e)[:100]}


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        s = status()
        print("pp_math:", "OK" if s["ok"] else "FAIL", "-", s["backend"])
        sys.exit(0 if s["ok"] else 1)
    print(__doc__)
