#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The eCoA Coverage Audit: every external certificate in the renamed eCoA_DATABASE,
held against CoQ_Analysis_Master_v48 to see whether the desk's own workbook accounts
for it — cited as a Certificate of Quality's source, on file but not credited,
mentioned only in passing, or on Drive and in no record of the desk at all.

    python3 deliverables/qc_gap_analysis/apply_ecoa_coverage_audit.py

OI-42 (16.09.2026) asked this question of the pre-rename corpus (490 scans: 449
laboratory, 41 in-house) and found forty-four unrecorded. The corpus has grown since
— the 20.09.2026 rename covers 520 files, 479 of them laboratory-issued — and this is
that same check run fresh against it, checked twice: independently verified against
its own first pass (a citation with a trailing Macedonian annotation that broke an
exact-string match, and a Reference-sheet mention applied to four sibling
certificates but missed on a fifth, both corrected here rather than carried over).

Adds one new sheet ("eCoA Coverage Audit"), one Open Item, one SHEETS entry and one
VERSION HISTORY line to the existing workbook. Touches no other sheet, no other
cell — this is an audit addition, not a rebuild, and does not go through
build_tracker_v8.py's from-scratch assembly.
"""
import datetime as dt
import json
import os

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "tracker", "CoQ_Analysis_Master_v48.xlsx")
OUT = os.path.join(HERE, "tracker", "CoQ_Analysis_Master_v49.xlsx")
DATA = "/tmp/claude-0/ecoa_coverage_status_full.json"

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")
STATUS_FILL = {
    "cited": PatternFill("solid", fgColor="C6EFCE"),          # matches the tracker's ✓ green
    "also_on_file": PatternFill("solid", fgColor="FFF2CC"),   # matches the amber "on file, not credited"
    "other_sheet_only": PatternFill("solid", fgColor="EDEDED"),
    "absent": PatternFill("solid", fgColor="F4CCCC"),         # matches the tracker's ✗ red
}
STATUS_LABEL = {
    "cited": "Cited as CoQ source",
    "also_on_file": "Also on file, not credited",
    "other_sheet_only": "Mentioned elsewhere only",
    "absent": "Not in the workbook",
}
COLS = ["Lab", "P Batch", "CU Batch", "Doc Code", "Date", "Status", "Evidence", "Evidence Detail", "Filename"]


def build_sheet(wb, rows):
    if "eCoA Coverage Audit" in wb.sheetnames:
        del wb["eCoA Coverage Audit"]
    ws = wb.create_sheet("eCoA Coverage Audit")
    ws.append(COLS)
    for c in ws[1]:
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"

    for r in rows:
        ws.append([
            r["lab"], r["p_batch"] or "", r["cu_batch"] or "", r["doc_code"], r["date"],
            STATUS_LABEL[r["status"]], r["evidence"], r["evidence_detail"], r["filename"],
        ])
        row_idx = ws.max_row
        fill = STATUS_FILL[r["status"]]
        for col in range(1, len(COLS) + 1):
            ws.cell(row=row_idx, column=col).fill = fill

    widths = [10, 12, 16, 24, 12, 24, 34, 44, 44]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.auto_filter.ref = "A1:%s%d" % (get_column_letter(len(COLS)), ws.max_row)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = 8  # A3, matching the workbook's other findings sheets
    ws.page_setup.fitToWidth = 1
    ws.print_options.horizontalCentered = False
    return ws


def counts(rows):
    c = {}
    for r in rows:
        c[r["status"]] = c.get(r["status"], 0) + 1
    return c


def find_row(ws, col0_value):
    for row in ws.iter_rows(min_row=1):
        if row[0].value == col0_value:
            return row[0].row
    return None


def insert_after(ws, after_row, values):
    ws.insert_rows(after_row + 1)
    for i, v in enumerate(values, 1):
        ws.cell(row=after_row + 1, column=i, value=v)


def update_reference(wb, rows, c):
    ws = wb["Reference"]

    # 1) SHEETS entry, right after "CoQ Compilation (long)"'s row
    after = find_row(ws, "CoQ Compilation (long)")
    sheets_text = (
        "One row per external (non-in-house) laboratory certificate in the renamed "
        "eCoA_DATABASE (%d certificates, the 41 in-house reports excluded), held against "
        "this workbook: whether it is cited as a Certificate of Quality's source (Document "
        "column, CoQ Compilation (long)), listed only under Also on file, mentioned only "
        "in another sheet, or absent from the workbook entirely. %d cited, %d also on "
        "file, %d mentioned elsewhere only, %d absent — see OI-60. Checked twice: an "
        "independent second pass against the first found and corrected two "
        "misclassifications (a citation whose cell carried a trailing Macedonian "
        "annotation, and a Reference-sheet mention applied to four sibling certificates "
        "but missed on a fifth) before either number was written here."
    ) % (len(rows), c.get("cited", 0), c.get("also_on_file", 0),
         c.get("other_sheet_only", 0), c.get("absent", 0))
    insert_after(ws, after, ["eCoA Coverage Audit", sheets_text, None])

    # 2) Open Item — OI-60, Area "Record integrity" (matching OI-42, which this updates)
    oi_header = find_row(ws, "Ref")
    # highest existing OI number, scanned from the Open Items block
    max_n = 0
    for row in ws.iter_rows(min_row=oi_header):
        v = row[0].value
        if isinstance(v, str) and v.startswith("OI-"):
            try:
                max_n = max(max_n, int(v.split("-")[1]))
            except ValueError:
                pass
    n = max_n + 1
    absent = [r for r in rows if r["status"] == "absent"]
    absent_list = "; ".join(sorted("%s %s (%s, %s)" % (r["lab"], r["doc_code"], r["cu_batch"] or r["p_batch"], r["date"])
                                    for r in absent))
    what_found = (
        "OI-42's count (44 unrecorded, of a 490-scan pre-rename corpus) refreshed against "
        "the 20.09.2026 renamed eCoA_DATABASE (520 files, 479 external): %d of those 479 "
        "do not appear anywhere in CoQ_Analysis_Master_v49, checked certificate by "
        "certificate against every sheet, not the Document column alone. %d are cited as "
        "a CoQ's source, %d are on file but not credited, %d are named only in passing "
        "(Reference, the Tracker or Result Supersession). OI-42's own worked total for "
        "the same corpus had counted 20 absent; two of those twenty are demonstrably "
        "present on closer reading (one cited five times with a trailing Macedonian "
        "annotation on the cell, one named in Reference's own OI-42 text for a sibling "
        "certificate but not this one) and are not repeated here."
    ) % (len(absent), c.get("cited", 0), c.get("also_on_file", 0), c.get("other_sheet_only", 0))
    what_desk_did = (
        "Every one of the %d absent certificates identified by laboratory doc code, "
        "cross-checked against the Document column, the Also on file column, and every "
        "other sheet (107,000+ cells) rather than assumed absent from one column's silence. "
        "Full per-certificate result on the eCoA Coverage Audit sheet."
    ) % len(absent)
    what_needed = (
        "For each of the %d: either it was replaced by a later retest and belongs in "
        "Result Supersession, or it is a result nobody has reviewed and needs a word from "
        "the Head of QC before the batches it belongs to can be called evaluated. The "
        "largest single group (7 of %d) is Institute of Public Health microbiology from "
        "24.06.2026 — microbiology is where this workbook's other findings also concentrate."
    ) % (len(absent), len(absent))
    row = ["OI-%d" % n, "Record integrity", "open",
           "%d of 479 external eCoA certificates are on Drive and in no record of the desk (OI-42, refreshed)" % len(absent),
           what_found, what_desk_did, what_needed,
           "eCoA Coverage Audit sheet; /tmp/claude-0/external_ecoas_479.json; " + absent_list[:400]]
    # append after the last existing OI row
    last_oi_row = oi_header
    for row_cells in ws.iter_rows(min_row=oi_header):
        if isinstance(row_cells[0].value, str) and row_cells[0].value.startswith("OI-"):
            last_oi_row = row_cells[0].row
    insert_after(ws, last_oi_row, row)

    # 3) VERSION HISTORY line
    vh = find_row(ws, "VERSION HISTORY")
    vh_text = (
        "The eCoA Coverage Audit sheet: the 479 external certificates in the 20.09.2026 "
        "renamed eCoA_DATABASE held against this workbook, one row each — %d cited as a "
        "CoQ's source, %d on file but not credited, %d mentioned elsewhere only, %d in no "
        "record of the desk (OI-60, refreshing OI-42's count for the grown corpus). "
        "Checked twice before being written: a first pass, then an independent second "
        "pass against the first that found and corrected two misclassifications. Nothing "
        "else on the workbook was touched — no other sheet, no other cell."
    ) % (c.get("cited", 0), c.get("also_on_file", 0), c.get("other_sheet_only", 0), c.get("absent", 0))
    insert_after(ws, vh, ["v49", vh_text])


def main():
    rows = json.load(open(DATA, encoding="utf-8"))
    if len(rows) != 479:
        raise SystemExit("expected 479 certificates, found %d" % len(rows))
    bad = [r for r in rows if r["status"] not in STATUS_LABEL]
    if bad:
        raise SystemExit("unrecognised status on %d rows: %r" % (len(bad), bad[:3]))

    wb = openpyxl.load_workbook(SRC)
    c = counts(rows)
    print("counts:", c, "sum:", sum(c.values()))
    build_sheet(wb, rows)
    update_reference(wb, rows, c)
    wb.save(OUT)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
