#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which document certifies which parameter, batch by batch — the Head of QC's question of 16.09.2026.

    python3 deliverables/qc_gap_analysis/batch_parameter_sources.py [--src <compilation long CSV>] [--out <stem>]

**The question, verbatim:** *"make a list of what parameter from 1 to 12 from the product
specification is referenced from what external CoA code and the issuing date for every batch
that we have."*

So: one row per batch, one column per determination #1 … #12, and in the cell the document
that certifies it and the day that document was issued. The desk holds this per CERTIFICATE
(`CoQ References`, `CoQ Compilation`); this is the same record cut the other way — per
**batch**, which is what a person asks when they want to know what a lot rests on.

Three things the sheet says that a flat list would hide:

* **A batch has more than one certificate.** The release certificate and the 12-month
  reissue cite different documents for the parameters the retest campaign re-ran, and the
  same document for the ones it did not. Both are shown: the release citation, and the
  reissue's beneath it when it differs, so the cell says what changed and what did not.
* **Not every citation is external.** Determinations #1, #2 and #7 are performed in the
  Purely Plant laboratory and are carried on the internal certificate of analysis, which the
  certificate of quality then cites — those cells are marked `[internal]`, because the
  question asked for the EXTERNAL code and an internal one is a different kind of answer.
* **A blank is a statement.** Where the certificate prints no result the cell says why in
  the desk's own words — *not tested*, *upon request*, *to be performed* — rather than
  leaving the reader to guess whether the desk lost the document or the laboratory never
  ran the test.

Outputs, beside the workbook in `tracker/`:

  Batch_Parameter_Sources_v<N>.xlsx   two sheets — one row per batch, and the long form
  Batch_Parameter_Sources_v<N>.csv    the wide sheet as text
  Batch_Parameter_Sources_v<N>_long.csv   one row per batch, certificate and determination
"""
import argparse
import csv
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKER = os.path.join(HERE, "tracker")
sys.path.insert(0, TRACKER)

# the twelve of the product specification, in the order the certificate prints them
DETS = ["1", "2", "3", "4", "5", "6", "7", "8",
        "9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "9.7",
        "10.1", "10.2", "10.3", "11.1", "11.2", "11.3", "11.4", "12"]
# the determination a sub-determination belongs to, for the per-parameter columns
GROUP = OrderedDict((d, d.split(".")[0]) for d in DETS)
IN_HOUSE = re.compile(r"Purely Plant|in-house", re.I)


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def load(src):
    with open(src, encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)]


def cell(rows):
    """What certifies this determination for this batch, as one readable cell.

    `rows` are the certificate rows for one batch and one determination, release first.
    """
    seen, out = set(), []
    for r in rows:
        doc, dd = _norm(r["Document"]), _norm(r["Issued"])
        lab = _norm(r["Laboratory"])
        if not doc or doc == "—":
            why = _norm(r["Status"]) or _norm(r["Result"])
            key = ("-", why)
            if key not in seen:
                seen.add(key)
                out.append("%s — %s" % (r["Series"], why or "no document"))
            continue
        mark = " [internal]" if IN_HOUSE.search(lab) or doc.startswith("iCoA") else ""
        key = (doc, dd)
        if key in seen:
            continue
        seen.add(key)
        out.append("%s, %s%s" % (doc, dd or "—", mark))
    return "\n".join(out)


def build(src):
    rows = load(src)
    batches = OrderedDict()
    for r in rows:
        cb, pp = _norm(r["Batch (cultivation)"]), _norm(r["P lot"])
        key = (pp if pp.startswith("P") else cb, cb, _norm(r["Strain"]))
        batches.setdefault(key, {}).setdefault(_norm(r["#"]), []).append(r)
    # release before reissue, so a cell reads in the order the lot was tested
    order = {"release": 0}
    for b in batches.values():
        for det in b:
            b[det].sort(key=lambda r: order.get(_norm(r["Series"]), 1))
    return batches, rows


def wide(batches):
    head = ["Batch", "Cultivation batch", "Strain"] + ["#%s" % d for d in DETS]
    out = [head]
    for (lot, cb, strain), dets in batches.items():
        out.append([lot, cb, strain] + [cell(dets.get(d, [])) for d in DETS])
    return out


def long_rows(batches, src_rows):
    head = ["Batch", "Cultivation batch", "Strain", "Certificate", "Series", "Date of issue",
            "#", "Parameter", "Result", "Document", "Issued", "Laboratory", "Internal", "Status"]
    out = [head]
    for (lot, cb, strain), dets in batches.items():
        for d in DETS:
            for r in dets.get(d, []):
                lab = _norm(r["Laboratory"])
                out.append([lot, cb, strain, _norm(r["CoQ code"]), _norm(r["Series"]),
                            _norm(r["Date of issue"]), d, _norm(r["Parameter"]),
                            _norm(r["Result"]), _norm(r["Document"]), _norm(r["Issued"]),
                            lab, "yes" if IN_HOUSE.search(lab) or _norm(r["Document"]).startswith("iCoA") else "",
                            _norm(r["Status"])])
    return out


def write_xlsx(path, wide_rows, long_table, note):
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "By batch"
    ws.append([note])
    ws["A1"].font = Font(name="Calibri", size=9, italic=True, color="595959")
    ws.append([])
    for row in wide_rows:
        ws.append(row)
    hdr = 3
    for c in range(1, len(wide_rows[0]) + 1):
        cell_ = ws.cell(hdr, c)
        cell_.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        cell_.fill = PatternFill("solid", fgColor="44546A")
        cell_.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    widths = [14, 16, 20] + [26] * len(DETS)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    for r in range(hdr + 1, ws.max_row + 1):
        for c in range(1, len(wide_rows[0]) + 1):
            ws.cell(r, c).alignment = Alignment(vertical="top", wrap_text=True)
            ws.cell(r, c).font = Font(name="Calibri", size=8)
    ws.freeze_panes = "D%d" % (hdr + 1)
    ws.auto_filter.ref = "A%d:%s%d" % (hdr, openpyxl.utils.get_column_letter(len(wide_rows[0])), ws.max_row)

    ws2 = wb.create_sheet("Long")
    for row in long_table:
        ws2.append(row)
    for c in range(1, len(long_table[0]) + 1):
        ws2.cell(1, c).font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        ws2.cell(1, c).fill = PatternFill("solid", fgColor="44546A")
    for i, w in enumerate([13, 15, 18, 15, 22, 12, 6, 28, 22, 20, 12, 30, 8, 30], 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    ws2.freeze_panes = "A2"
    ws2.auto_filter.ref = "A1:%s%d" % (openpyxl.utils.get_column_letter(len(long_table[0])), ws2.max_row)
    wb.save(path)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, help="the CoQ compilation long CSV to cut")
    ap.add_argument("--out", default=None, help="output stem (default: tracker/Batch_Parameter_Sources_v<N>)")
    a = ap.parse_args(argv[1:])
    src = a.src
    if src is None:
        cands = sorted((f for f in os.listdir(TRACKER)
                        if re.match(r"^CoQ_compilation_v\d+_long\.csv$", f)),
                       key=lambda f: int(re.search(r"v(\d+)", f).group(1)))
        if not cands:
            raise SystemExit("no CoQ_compilation_v<N>_long.csv in " + TRACKER)
        src = os.path.join(TRACKER, cands[-1])
    ver = re.search(r"v(\d+)", os.path.basename(src)).group(1)
    stem = a.out or os.path.join(TRACKER, "Batch_Parameter_Sources_v%s" % ver)

    batches, rows = build(src)
    w, l = wide(batches), long_rows(batches, rows)
    note = ("Which document certifies which parameter, batch by batch — cut from "
            "CoQ_compilation_v%s. Each cell: the document code, its date of issue, and "
            "[internal] where the citation is Purely Plant's own certificate of analysis "
            "rather than an external laboratory's. Where a batch's reissue cites a "
            "different document from its release certificate, both are shown." % ver)
    with open(stem + ".csv", "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(w)
    with open(stem + "_long.csv", "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(l)
    write_xlsx(stem + ".xlsx", w, l, note)

    ext = sum(1 for r in l[1:] if r[9] and r[9] != "—" and not r[12])
    inh = sum(1 for r in l[1:] if r[12])
    none = sum(1 for r in l[1:] if not r[9] or r[9] == "—")
    print("%s: %d batches x %d determinations" % (os.path.basename(stem + ".xlsx"), len(w) - 1, len(DETS)))
    print("  %d citation(s) of an external laboratory certificate" % ext)
    print("  %d of an internal certificate of analysis (#1, #2, #7)" % inh)
    print("  %d determination row(s) with no document, each saying why" % none)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
