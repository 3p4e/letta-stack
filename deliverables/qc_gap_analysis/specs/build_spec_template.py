#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One blank specification to fill by hand — every value a blue bracketed descriptor.

    python3 deliverables/qc_gap_analysis/specs/build_spec_template.py

The owner, 21.09.2026: one template document with the placeholders in brackets and
coloured blue, so a reader can see at a glance which values are theirs to replace.

It is the owner's own template with its values swapped for descriptors — nothing about the
layout, the columns or Section 02 is touched. The blue comes from a style block APPENDED
to the document, never by editing the settled one, so removing that one block returns the
file to the design exactly as delivered.

Section 02 carries no placeholder. Its twenty-eight rows are the same on every sheet of the
set — they are the specification, not a value to fill — and they are left as they are.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "base", "Product_Specification_ImB.html")
OUT = os.path.join(HERE, "TEMPLATE", "QCSP_001_ImB_TEMPLATE.html")

# The placeholder ink: a blue that belongs to no printed value on the page, so nothing
# filled in can be mistaken for something still to fill in.
STYLE = """
<style id="__placeholders">
  /* Appended, never merged into the design's own stylesheet. Delete this block and the
     document is the template exactly as it was delivered. */
  .ph {
    color: #1565C0 !important;
    font-style: italic !important;
    font-weight: 600 !important;
    letter-spacing: .2px !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .ph-box { color: #1565C0 !important; }
</style>
"""


def ph(text):
    return '<span class="ph">[%s]</span>' % text


def one(hay, needle, repl, what):
    n = hay.count(needle)
    if n != 1:
        raise SystemExit("template anchor %s appears %d times, expected 1" % (what, n))
    return hay.replace(needle, repl, 1)


def main():
    h = open(TEMPLATE, encoding="utf-8").read()

    h = one(h, "<title>Purely Plant — Product Specification — Intermediate Bulk (blank template)</title>",
            "<title>Purely Plant — Product Specification — Intermediate Bulk — TEMPLATE</title>",
            "<title>")
    h = one(h, '<div class="hb-code">QCSP 001_XX-I_v.03</div>',
            '<div class="hb-code">%s</div>' % ph("SPEC DOC CODE"), ".hb-code")
    h = one(h, '<div class="pb-name">Cultivar name</div>',
            '<div class="pb-name">%s</div>' % ph("CULTIVAR NAME"), ".pb-name")
    h = one(h, '<span class="pbp-val">00.00%</span><span class="pbp-tol">± 0.00%</span>',
            '<span class="pbp-val">%s</span><span class="pbp-tol">± %s</span>'
            % (ph("NOMINAL %"), ph("TOLERANCE %")), ".pbp-val/.pbp-tol")

    # the three tick pills — the box stays, the ratio becomes two descriptors
    h = one(h, 'INDICA<span class="pn">00</span> : SATIVA<span class="pn">00</span>',
            'INDICA<span class="pn">%s</span> : SATIVA<span class="pn">%s</span>'
            % (ph("INDICA %"), ph("SATIVA %")), "phenotype ratio")

    h = one(h, '<span class="pcr-val">XX_THC00 : CBD1</span>',
            '<span class="pcr-val">%s</span>' % ph("PRODUCT CODE"), "Product Code")
    h = one(h, '<span class="pcr-val">00.00 &ndash; 00.00 %</span>',
            '<span class="pcr-val">%s &ndash; %s %%</span>' % (ph("LOW"), ph("HIGH")), "Potency")
    h = one(h, '<span class="pcr-val">QCSP_001_XX-I_v.03</span>',
            '<span class="pcr-val">%s</span>' % ph("SPEC DOC CODE"), "Spec. doc. code")

    # The two approval dates are not interchangeable — the first is the QC Manager's and
    # the second the QA Manager's — so they are named apart. Calling both DD.MM.YYYY left
    # two fields in the template that nobody could tell from each other.
    DATE = '<span class="ap-date-val tpl">DD.MM.YYYY</span>'
    n = h.count(DATE)
    if n != 2:
        raise SystemExit("template has %d approval dates, expected 2" % n)
    first, second = h.find(DATE), h.rfind(DATE)
    if not (h.rfind("QC Manager", 0, first) > h.rfind("QA Manager", 0, first)
            and h.rfind("QA Manager", 0, second) > h.rfind("QC Manager", 0, second)):
        raise SystemExit("the approval grid is not QC then QA; the date labels would lie")
    for who in ("QC DATE", "QA DATE"):
        h = h.replace(DATE, '<span class="ap-date-val">%s</span>' % ph(who), 1)

    # the owner, 21.09.2026: no document code in the bottom right corner
    h = one(h, '<div class="foot-right">QCSP 001 v.03</div>',
            '<div class="foot-right"></div>', ".foot-right")

    # tick boxes stay empty and carry the placeholder ink, so it reads as "choose one"
    h = h.replace('<span class="var-opt">&#9744;', '<span class="var-opt ph-box">&#9744;')

    h = one(h, "</body>", STYLE + "</body>", "</body>")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(h)
    print("template written: %s" % os.path.relpath(OUT, os.path.dirname(HERE)))
    print("placeholders: %d bracketed descriptor(s), %d tick box(es)"
          % (h.count('class="ph"'), h.count('ph-box')))
    return 0


if __name__ == "__main__":
    sys.exit(main())
