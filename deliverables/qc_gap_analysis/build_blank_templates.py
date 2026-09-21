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
    "pp-v": "VALUE", "lk-lbl": "LABEL", "sec-label": "SECTION", "fc": "OBSERVATION",
    # the observation record: a box that is ticked and the finding beside it
    "bx": "TICK", "ck-t": "OBSERVATION", "ck": "TICK", "title": "DOCUMENT TITLE",
    "chip-un": "UNIT", "pb-potency": "POTENCY", "pcr-val": "VALUE",
}


# The headline and the conformity line are set in display type; a descriptor as long as
# "CULTIVATION BATCH 2" runs off the page there, so those few are named short.
SHORT = {
    "CULTIVATION BATCH": "BATCH", "CULTIVATION BATCH 2": "STRAIN",
    "TOTAL THC RESULT": "THC %", "PRODUCTION BATCH \u2116": "PRODUCTION BATCH",
    "CULTIVATION BATCH \u2116": "CULTIVATION BATCH",
    "SPECIFICATION REFERENCE": "SPEC REF", "PRODUCT SPECIFICATION \u2116": "SPEC \u2116",
    "FINAL QC TESTING FOR BATCH": "BATCH", "DOCUMENT ID": "DOC ID", "DOCUMENT ID 2": "ISSUE DATE",
}


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
            if re.search(r"(^|[\s-])(lbl|label)", c) and "sec" not in c:
                t = " ".join(x.strip() for x in sib.itertext() if x.strip())
                # the caption is bilingual; the English half is enough for a descriptor
                t = re.split(r"[\u0400-\u04FF]", t)[0].strip(" ·|—-")
                if t:
                    return t
        return ""
    n = el
    for _ in range(2):            # the field itself, then the little panel it sits in
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
        label = nearest_label(el) or NAMES.get(cls, (cls or "VALUE").replace("-", " ").upper())
        label = re.sub(r"\s+", " ", label).strip().upper()
        label = SHORT.get(label, label)[:22]
        num = row_number(el)
        if num:
            label = "%s #%s" % (label, num)
        else:
            used[label] += 1
            if used[label] > 1:
                label = "%s %d" % (label, used[label])
        span = etree.Element("span")
        span.set("class", "ph")
        span.text = "[%s]" % label
        span.tail = el.tail
        el.text = None
        el.insert(0, span)
        n += 1

    out = LH.tostring(root, encoding="unicode", doctype="<!DOCTYPE html>")
    out = out.replace("</body>", STYLE + "</body>", 1)
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, name)
    open(dest, "w", encoding="utf-8").write(out)
    print("%-44s %4d documents compared, %3d fixed, %3d placeholder(s)"
          % (name, len(files), len(vals) - len(variable), n))
    return n


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
