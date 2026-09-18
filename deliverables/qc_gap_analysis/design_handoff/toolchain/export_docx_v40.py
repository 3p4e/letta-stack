#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every certificate of quality as a Word document — a real one.

    python3 design_handoff/toolchain/export_docx_v40.py

The Head of QC, 18.09.2026: a Word document is for pinpoint edits and formatting in a word
processor. The earlier export placed the printed page as a picture on an A4 sheet, which
is a PDF wearing the wrong extension, and it is withdrawn. Each .docx is now built from the
certificate's own HTML — the same file the PDF is printed from — by html_to_docx.py: the
header bar, the section bars, the identity grids, the results and cross-reference tables,
the conformity row, the approval block with the signatures as inline pictures, and the
footer, every one of them as editable Word text and tables.

The controlled record is still the PDF; the Word copy is the same content in a form a
person can edit. Both come from one HTML, so they cannot disagree.

Output: design_handoff/docx/<same folders as out/>/<same stem>.docx, and one merged
document per tranche beside the merged PDFs: pdf/CoQ_Tranche_<N>.docx (release round,
then retest, as the PDF orders them).
"""
import glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); HANDOFF = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import html_to_docx as H                                                # noqa: E402
import merge_tranches_v40 as M                                          # noqa: E402
OUT = os.path.join(HANDOFF, "out"); DOCX = os.path.join(HANDOFF, "docx"); PDF = os.path.join(HANDOFF, "pdf")


def build():
    rows = M.collect()
    n = 0
    for _t, _series, stem, html in sorted(rows, key=lambda r: r[2]):
        folder = os.path.relpath(os.path.dirname(html), OUT)
        dest = os.path.join(DOCX, folder); os.makedirs(dest, exist_ok=True)
        H.convert(html, os.path.join(dest, stem + ".docx")); n += 1
    print("docx written: %d  -> %s" % (n, os.path.relpath(DOCX)))
    order = {"release": 0, "reissue": 1}
    for t in ("1", "2", "3"):
        group = sorted((r for r in rows if str(r[0]) == t), key=lambda r: (order[r[1]], M.order_key(r[2])))
        if not group:
            continue
        out = os.path.join(PDF, "CoQ_Tranche_%s.docx" % t)
        k = H.convert_many([r[3] for r in group], out, "Tranche %s — certificates of quality" % t)
        print("  Tranche %s  %3d certificate(s)  %s (%.1f MiB)" % (t, k, os.path.basename(out), os.path.getsize(out) / 1048576))
    return n


if __name__ == "__main__":
    sys.exit(0 if build() == 172 else 1)
