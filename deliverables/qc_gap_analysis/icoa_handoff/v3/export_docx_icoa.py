#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every internal certificate of analysis as a Word document — a real one.

    python3 export_docx_icoa.py

The same rule as design_handoff/toolchain/export_docx_v40.py, and the same converter
(html_to_docx.py): each certificate's own HTML — the file the PDF is printed from — becomes
editable Word text and tables: header bar, section bars, identity grids, the method cards,
the observation record with its ☒/☐ checklist, the results table, the disposition, the
three-signatory approval block with the signatures as inline pictures, and the footer.
The page-as-a-picture export of 18.09.2026 is withdrawn (Head of QC, the same day).

Output: docx/<INITIAL|RETEST>/<stem>.docx, and the merged retest sets the Head of QC asked
for on 18.09.2026 — pdf/iCoA_Retest_Tranche_<n>.docx — in the order of the merged PDF.
"""
import glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); GAP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(GAP, "design_handoff", "toolchain"))
import html_to_docx as H                                                # noqa: E402
ISSUE = os.path.join(HERE, "ISSUE_iCOA"); DOCX = os.path.join(HERE, "docx"); PDF = os.path.join(HERE, "pdf")


def build():
    import measure_page as MP
    n = 0
    stems = {}
    htmls = [h for rnd in ("INITIAL", "RETEST") for h in sorted(glob.glob(os.path.join(ISSUE, rnd, "*.html")))]
    measured = MP.measure_many(htmls)
    for html in htmls:
        rnd = os.path.basename(os.path.dirname(html))
        stem = os.path.splitext(os.path.basename(html))[0]
        stems[stem] = html
        dest = os.path.join(DOCX, rnd); os.makedirs(dest, exist_ok=True)
        H.convert(html, os.path.join(dest, stem + ".docx"), measured=measured[html]); n += 1
    print("docx written: %d  -> %s" % (n, os.path.relpath(DOCX, HERE)))
    # the merged retest sets follow merge_tranche_retests.py's own membership and order
    sys.path.insert(0, HERE)
    import merge_tranche_retests as MT
    lots = MT.tranche_lots()
    retests = sorted((s for s in stems if "_Retest_" in s), key=MT.seq)
    for t, name in (("T1", "1"), ("T2", "2")):
        htmls = [stems[s] for s in retests if MT.lot_of(s) in lots[t]]
        if not htmls:
            continue
        out = os.path.join(PDF, "iCoA_Retest_Tranche_%s.docx" % name)
        k = H.convert_many(htmls, out, "Tranche %s — internal certificates of analysis, retest round" % name, measured=measured)
        print("  Tranche %s  %3d certificate(s)  %s (%.1f MiB)" % (name, k, os.path.basename(out), os.path.getsize(out) / 1048576))
    return n


if __name__ == "__main__":
    sys.exit(0 if build() == 172 else 1)
