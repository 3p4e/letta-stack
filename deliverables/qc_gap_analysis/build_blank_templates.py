#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One blank template per document type — every value a blue bracketed descriptor.

    python3 deliverables/qc_gap_analysis/build_blank_templates.py

The owner, 21.09.2026: a template for the intermediate-bulk product specification, the
certificate of quality and the internal certificate of analysis, "with placeholders
descriptors in brackets and maybe colored in blue to indicate that the value needs to be
replaced", as HTML.

WHICH FIELDS ARE PLACEHOLDERS IS NOT GUESSED. Every document of a fleet is parsed and each
text node addressed by its position in the tree. A node whose text is the SAME on all 172
documents is fixed wording and is left exactly as it is; a node whose text DIFFERS between
any two is a value somebody fills, and only those become descriptors. That is the whole
rule, and it means the templates cannot quietly blank a caption or keep a batch number.

The blue is a style block APPENDED to the document. Delete that one block and the file is
the design exactly as it was, which is the same rule the certificates follow: a settled
visual layer is added to, never edited.
"""
import collections
import base64
import glob
import html as H
import os
import re
import sys

from lxml import html as LH
from lxml import etree

# These documents are UTF-8 and say so, but lxml guesses from the bytes and
# had been reading the Macedonian half as latin-1. Parse with the encoding stated.
PARSER = LH.HTMLParser(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "BLANK_TEMPLATES")

STYLE = """
<style id="__placeholders">
  /* Appended by build_blank_templates.py — delete this block and the document is the
     design exactly as delivered. */
  .ph { color:#1565C0 !important; font-style:italic !important; font-weight:600 !important;
        -webkit-print-color-adjust:exact; print-color-adjust:exact; }
</style>
"""

# A readable name for each field, by the class the design gives it. Anything not named
# here falls back to the class itself, so a new field appears as a descriptor rather than
# silently keeping the specimen's value.
NAMES = {
    "hb-code": "DOCUMENT CODE", "hb-issue": "ISSUE DATE", "hb-sup": "SUPERSEDES",
    "pb-name": "CULTIVATION BATCH", "pbp-val": "TOTAL THC RESULT",
    "pot-nom": "GRADE NOMINAL", "pot-tol": "GRADE TOLERANCE", "pot-win": "GRADE WINDOW",
    "p-spec": "SPECIFICATION REFERENCE", "disp-batch": "BATCH", "ratio": "PHENOTYPE",
    "cert": "DOCUMENT CITED", "cd": "DOCUMENT DATE", "lk-val": "VALUE",
    "lr-lab": "LABORATORY", "lr-mono": "PARAMETERS COVERED", "lr-ac": "ACCREDITATION",
    "ap-date-val": "APPROVAL DATE", "mk": "MACEDONIAN", "r-val": "RESULT",
    "pp-v": "VALUE", "lk-lbl": "LABEL", "sec-label": "SECTION",
    # The observation record: a box that is ticked and the finding beside it. `fc` and
    # `ck-t` are deliberately NOT named here — their group already names them Colour,
    # Odour, Texture & resin, and a descriptor reading OBSERVATION 12 tells the analyst
    # nothing about what belongs in the chip.
    "bx": "TICK", "ck": "TICK", "title": "DOCUMENT TITLE",
    "chip-un": "UNIT", "pb-potency": "POTENCY", "pcr-val": "VALUE",
}

# Named by what they are, never by the group they sit in: these carry no value of their
# own, so a caption above them describes their neighbours rather than them.
STRUCTURAL = {"bx", "ck", "title"}

# The tick itself, and the empty box the certificate says a blank one prints.
TICKS = {"bx"}
UNTICKED = "\u2610"


# The headline and the conformity line are set in display type; a descriptor as long as
# "CULTIVATION BATCH 2" runs off the page there, so those few are named short.
SHORT = {
    "CULTIVATION BATCH": "BATCH", "CULTIVATION BATCH 2": "STRAIN",
    "TOTAL THC RESULT": "THC %", "PRODUCTION BATCH \u2116": "PRODUCTION BATCH",
    "CULTIVATION BATCH \u2116": "CULTIVATION BATCH",
    "SPECIFICATION REFERENCE": "SPEC REF", "PRODUCT SPECIFICATION \u2116": "SPEC \u2116",
    "FINAL QC TESTING FOR BATCH": "BATCH", "DOCUMENT ID": "DOC ID", "DOCUMENT ID 2": "ISSUE DATE",
}


def clip_words(label, n):
    """`label` cut to at most `n` characters, on a word boundary.

    Cutting at the character left `CYSTOLITHS \u00b7 HCL R TES` and
    `COVERING TRICHOMES \u2014 D` on the page — a descriptor that ends mid-word reads as a
    mistake rather than as a name. A whole word short is better than a broken one.

    >>> clip_words("CYSTOLITHS \u00b7 HCL R TEST", 22)
    'CYSTOLITHS \u00b7 HCL R'
    >>> clip_words("FOREIGN TISSUE OR MOULD", 22)
    'FOREIGN TISSUE OR'
    >>> clip_words("COLOUR", 22)
    'COLOUR'
    >>> clip_words("SUPERCALIFRAGILISTICEXPIALIDOCIOUS", 22)
    'SUPERCALIFRAGILISTICEX'
    """
    label = label.strip()
    if len(label) <= n:
        return label
    cut = label[:n + 1]
    space = cut.rfind(" ")
    out = (cut[:space] if space > 0 else label[:n]).rstrip(" \u00b7|\u2014-")
    return out or label[:n]


def shorten(label):
    """A descriptor short enough for the box it has to sit in.

    The lookup is forgiving about the tail of a caption, because a caption's tail is
    decoration: `FINAL QC TESTING FOR BATCH \u2116` is the same field as
    `FINAL QC TESTING FOR BATCH`, and matching only the exact string let it through at
    full length, where it ran out of its pill and across the conformity chip.

    >>> shorten("FINAL QC TESTING FOR BATCH \u2116")
    'BATCH'
    >>> shorten("SPECIFICATION REFERENCE")
    'SPEC REF'
    >>> shorten("SOMETHING NOBODY HAS SHORTENED AT ALL")   # cut on a word boundary
    'SOMETHING NOBODY HAS'
    """
    for key in (label, re.sub(r"[\s\u2116.:·—-]+$", "", label)):
        if key in SHORT:
            return SHORT[key][:22]
    return clip_words(label, 22)


def addr(el):
    chain, n = [], el
    while n is not None and n.tag != "html":
        p = n.getparent()
        idx = list(p).index(n) if p is not None else 0
        chain.append("%s.%s[%d]" % (n.tag, (n.get("class") or "").split(" ")[0], idx))
        n = p
    return "/".join(reversed(chain))


def texts(path):
    t = LH.parse(path, PARSER).getroot()
    out = {}
    for el in t.iter():
        if el.tag in ("script", "style"):
            continue
        s = (el.text or "").strip()
        if s:
            out[addr(el)] = s
    return out


def leaf_class(a):
    seg = a.split("/")[-1]
    c = seg.split(".", 1)[1].split("[")[0] if "." in seg else ""
    if c:
        return c
    for seg in reversed(a.split("/")[:-1]):
        c = seg.split(".", 1)[1].split("[")[0] if "." in seg else ""
        if c:
            return c
    return ""


def nearest_label(el):
    """The label the design already prints beside this value.

    Every panel in these documents pairs a caption with its value — lk-lbl with lk-val,
    ig-label with ig-val, pcr-lbl with pcr-val, ptk-lbl with the tick options. Taking the
    caption's own words names the placeholder the way the page already names the field, so
    the template reads in the document's language rather than in the stylesheet's.
    """
    def cap(node):
        for sib in node.itersiblings(preceding=True):
            c = (sib.get("class") or "")
            if re.search(r"(^|[\s-])(lbl|label|attr)($|[\s-])", c) and "sec" not in c:
                t = " ".join(x.strip() for x in sib.itertext() if x.strip())
                # the caption is bilingual; the English half is enough for a descriptor
                t = re.split(r"[\u0400-\u04FF]", t)[0].strip(" ·|—-")
                if t:
                    return t
        return ""
    n = el
    # Three, not two. The observation chip sits in `.ck` inside `.fc-opts`, and the group
    # caption — `<div class="fc-attr">Colour</div>` — is the sibling of that third one. A
    # shorter climb named all twenty-three of them OBSERVATION after their class instead.
    # The `sec` exclusion is what keeps the climb off the section bars, which is the fault
    # that made this two in the first place.
    for _ in range(3):            # the field, the panel it sits in, and that panel's group
        if n is None:
            break
        t = cap(n)
        if t:
            return t
        n = n.getparent()
    return ""


def row_number(el):
    """For a cell inside a results row, the determination number that row carries."""
    tr = el
    while tr is not None and tr.tag != "tr":
        tr = tr.getparent()
    if tr is None:
        return ""
    first = tr.find(".//td")
    if first is None:
        return ""
    s = "".join(first.itertext()).strip()
    return s if re.match(r"^\d+(\.\d+)?$", s) else ""


def self_contained(html, base):
    """Fold every relative stylesheet and image into the document.

    A template is a file somebody opens on its own, and the internal certificate carried
    three stylesheets and its logo by relative path — `../_icoa.css` and its companions,
    `../_logo.svg` — which resolve beside the fleet and nowhere else. Moved into
    `BLANK_TEMPLATES/` the page lost every rule it had and printed over three A4 pages
    with a broken image where the mark belongs. The certificate of quality never showed
    it, because its own design carries both inline already.
    """
    def css(m):
        href = m.group(1)
        if "//" in href:                       # Google Fonts and the like stay as they are
            return m.group(0)
        return "<style data-from=\"%s\">\n%s\n</style>" % (
            os.path.basename(href), read_asset(base, href).decode("utf-8"))

    def img(m):
        src = m.group(1)
        if "//" in src or src.startswith("data:"):
            return m.group(0)
        kind = MEDIA.get(os.path.splitext(src)[1].lower())
        if not kind:
            raise SystemExit("template image of unknown type: %s" % src)
        data = base64.b64encode(read_asset(base, src)).decode("ascii")
        return m.group(0).replace(src, "data:%s;base64,%s" % (kind, data))

    html = re.sub(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>', css, html)
    return re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', img, html)


MEDIA = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}


def read_asset(base, href):
    path = os.path.normpath(os.path.join(base, href))
    if not os.path.isfile(path):
        raise SystemExit("template asset not found: %s" % path)
    return open(path, "rb").read()


def build(name, specimen, fleet):
    files = sorted(sum([glob.glob(g) for g in fleet], []))
    if not files:
        raise SystemExit("%s: no documents to compare" % name)
    vals = collections.defaultdict(set)
    for f in files:
        for k, v in texts(f).items():
            vals[k].add(v)
    variable = {k for k, v in vals.items() if len(v) > 1}

    tree = LH.parse(specimen, PARSER)
    root = tree.getroot()
    used = collections.Counter()
    n = 0
    for el in root.iter():
        if el.tag in ("script", "style"):
            continue
        if not (el.text or "").strip():
            continue
        a = addr(el)
        if a not in variable:
            continue
        cls = leaf_class(a)
        if cls in TICKS:
            # A tick is a state, not a value, and the certificate says how a blank one
            # prints: the menus are "printed unticked and marked and initialled by hand
            # at the time of analysis". So the box is drawn empty rather than given a
            # descriptor. Twenty-five of the internal certificate's sixty placeholders
            # were [TICK n] standing where one glyph belongs, and they were wide enough
            # to push the descriptor beside them out of its own chip.
            el.text = UNTICKED
            continue
        # The caption the page prints beside a value names it best, except where the
        # element is not a value at all. A tick box is a tick whatever group it sits in,
        # and letting the caption reach it made every box in the observation record read
        # [COLOUR] or [ODOUR]. Those few classes are named by what they ARE.
        label = (NAMES[cls] if cls in STRUCTURAL
                 else nearest_label(el)
                 or NAMES.get(cls, (cls or "VALUE").replace("-", " ").upper()))
        label = re.sub(r"\s+", " ", label).strip().upper()
        label = shorten(label)
        num = row_number(el)
        if num:
            label = "%s #%s" % (label, num)
        else:
            used[label] += 1
            if used[label] > 1:
                label = "%s %d" % (label, used[label])
        if el.tag in ("title", "style", "script"):
            continue                           # not a field; a span here is markup, not text
        span = etree.Element("span")
        span.set("class", "ph")
        span.text = "[%s]" % label
        span.tail = el.tail
        el.text = None
        el.insert(0, span)
        n += 1

    out = LH.tostring(root, encoding="unicode", doctype="<!DOCTYPE html>")
    out = out.replace("</body>", STYLE + "</body>", 1)
    out = self_contained(out, os.path.dirname(specimen))
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, name)
    open(dest, "w", encoding="utf-8").write(out)
    print("%-44s %4d documents compared, %3d fixed, %3d placeholder(s)"
          % (name, len(files), len(vals) - len(variable), n))
    return n


LADDER_SPLIT = re.compile(r"[\s\u00b7\u2014/&-]+")
PH_TEXT = re.compile(r"^\[(.*?)(?:\s+(#?\d+))?\]$")


def ladder(text):
    """Progressively shorter forms of a placeholder, each still naming its field.

    The number is the field's identity — `[COLOUR 3]` is not `[COLOUR 2]` — so it is
    never dropped; only the words give way, and only as far as the box demands.

    >>> list(ladder("[COLOUR 3]"))
    ['[COLOUR 3]', '[COL 3]', '[C 3]', '[3]']
    >>> list(ladder("[BRACTS & STIGMAS]"))
    ['[BRACTS & STIGMAS]', '[BRA STI]', '[BS]', '[\u00b7]']
    >>> list(ladder("[nn]"))               # no number to keep, so the word itself gives way
    ['[nn]', '[n]', '[\u00b7]']
    >>> next(ladder("plain text"))         # not a placeholder: left alone
    'plain text'
    """
    m = PH_TEXT.match(text.strip())
    if not m:
        yield text
        return
    label, num = (m.group(1) or "").strip(), m.group(2)
    words = [w for w in LADDER_SPLIT.split(label) if w]
    forms = [label, " ".join(w[:3] for w in words), "".join(w[:1] for w in words), ""]
    seen = set()
    for f in forms:
        if f in seen:
            continue
        seen.add(f)
        if f and num:
            out = "[%s %s]" % (f, num)
        elif f:
            out = "[%s]" % f
        elif num:
            out = "[%s]" % num
        else:
            out = "[\u00b7]"                     # a field with nowhere to put its name
        yield out


def fit_placeholders(paths, css, chromium):
    """Shorten any placeholder the page would cut off, until it fits its own box.

    The chips of the observation record are `overflow:hidden; text-overflow:ellipsis`,
    and they are not all the same width — the widest held `[OBSERVATION` and the
    narrowest only `[OBS`, so fifteen of the internal certificate's sixty placeholders
    printed with their number cut off and could not be told apart. No abbreviation chosen
    in advance fits them all, so each one is measured in the layout that will be printed
    and shortened only as far as its own box demands.
    """
    import sys as _sys
    _sys.path.insert(0, os.path.join(HERE, "live_instrument"))
    from print_coq_pdfs import render
    from playwright.sync_api import sync_playwright

    # A placeholder is an inline <span>, and scrollWidth on an inline element measures
    # nothing — the first attempt reported every template clean while the chips were
    # visibly cut off. What clips is the BOX around it: the nearest ancestor that hides
    # its horizontal overflow. Ask that one whether its content is wider than itself.
    OVERFLOW = """() => Array.from(document.querySelectorAll('.ph')).map(e => {
        for (let n = e; n && n !== document.body; n = n.parentElement) {
          const o = getComputedStyle(n).overflowX;
          if ((o === 'hidden' || o === 'clip') && n.scrollWidth > n.clientWidth + 0.5)
            return {i: +e.dataset.phi, t: e.textContent};
        }
        return null;
      }).filter(Boolean)"""
    changed = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium) if chromium \
            else pw.chromium.launch()
        page = browser.new_page()
        for src in paths:
            tree = LH.parse(src, parser=PARSER).getroot()
            phs = [e for e in tree.iter() if "ph" in (e.get("class") or "").split()]
            for i, e in enumerate(phs):
                e.set("data-phi", str(i))
            tmp = src + ".fit.html"
            open(tmp, "w", encoding="utf-8").write(
                LH.tostring(tree, encoding="unicode", doctype="<!DOCTYPE html>"))
            try:
                page.goto("file://" + os.path.abspath(tmp))
                if css:
                    page.add_style_tag(content=css)
                page.evaluate("() => document.fonts.ready")
                page.emulate_media(media="print")
                rungs = {}
                for _ in range(6):
                    over = page.evaluate(OVERFLOW)
                    if not over:
                        break
                    moved = False
                    for o in over:
                        i = o["i"]
                        if i not in rungs:
                            rungs[i] = list(ladder(o["t"]))[1:]
                        if not rungs[i]:
                            continue
                        nxt = rungs[i].pop(0)
                        page.evaluate(
                            "([i, t]) => { document.querySelector('[data-phi=\"'+i+'\"]')"
                            ".textContent = t; }", [i, nxt])
                        changed[(src, i)] = nxt
                        moved = True
                    if not moved:
                        break
                left = page.evaluate(OVERFLOW)
            finally:
                os.remove(tmp)
            for i, e in enumerate(phs):
                if (src, i) in changed:
                    e.text = changed[(src, i)]
                e.attrib.pop("data-phi", None)
            open(src, "w", encoding="utf-8").write(
                LH.tostring(tree, encoding="unicode", doctype="<!DOCTYPE html>"))
            n = sum(1 for k in changed if k[0] == src)
            print("%-44s %3d shortened to fit, %d still cut off"
                  % (os.path.basename(src), n, len(left)))
            if left:
                raise SystemExit("a placeholder is still cut off: %s"
                                 % [x["t"] for x in left][:4])
        browser.close()


def main():
    build("CoQ_BLANK_TEMPLATE.html",
          os.path.join(HERE, "design_handoff/out/ISSUE_COQ/CoQ-PP_26-013_P050072_GP_Grape_Pie_Grade_II.html"),
          [os.path.join(HERE, "design_handoff/out/ISSUE_COQ/*.html"),
           os.path.join(HERE, "design_handoff/out/REISSUE/*/*.html")])
    build("iCoA_BLANK_TEMPLATE.html",
          os.path.join(HERE, "icoa_handoff/v3/ISSUE_iCOA/INITIAL/iCoA-PP_26-001_CJ1024_CJ_Cap_Junky_Initial.html"),
          [os.path.join(HERE, "icoa_handoff/v3/ISSUE_iCOA/*/*.html")])
    # The specification's template is not derived: the owner supplied a blank of it, and
    # specs/build_spec_template.py names its twelve fields by hand. Copying that one keeps
    # a single source for the specification rather than two that can drift apart.
    import shutil
    src = os.path.join(HERE, "specs", "TEMPLATE", "QCSP_001_ImB_TEMPLATE.html")
    dst = os.path.join(OUT, "ImB_Specification_BLANK_TEMPLATE.html")
    shutil.copyfile(src, dst)
    n = open(dst, encoding="utf-8").read().count('class="ph"')
    print("%-44s %4s %s %3d placeholder(s)"
          % ("ImB_Specification_BLANK_TEMPLATE.html", "—", "from the owner's own blank,",  n))

    # Last, and on all three: a descriptor nobody can read is worse than none. Measured
    # in the layout that will be printed, never guessed.
    import glob as _glob
    import sys as _sys
    _sys.path.insert(0, os.path.join(HERE, "live_instrument"))
    from print_coq_pdfs import FAMILIES, SUBSETS, page_text                  # noqa: E402
    import house_fonts                                                       # noqa: E402
    sheets = sorted(_glob.glob(os.path.join(OUT, "*.html")))
    css, _, _ = house_fonts.font_face_css(page_text(sheets), FAMILIES, SUBSETS)
    chromium = (_glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    fit_placeholders(sheets, css, chromium)
    return 0


if __name__ == "__main__":
    sys.exit(main())
