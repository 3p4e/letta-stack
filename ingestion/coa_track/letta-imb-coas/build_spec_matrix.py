#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wide-format spec matrix: one chronological row per batch, parameters as columns.

The transposition of exports/PP_Spec_Parameter_Listing.xlsx requested by the QC Manager:
the same fact-checked data, but spread across the columns to the right in row-per-batch
style. Every QCSP 001 parameter owns a dedicated column pair — Result | eCoA reference —
under frozen header rows that carry the parameter name (with unit) and its acceptance
criterion in dedicated cells. Each result's provenance is rendered compactly as
"code, date, lab" (e.g. ППК25105, 17.04.2025, CNP) and that text is hyperlinked to the
certificate scan on Drive.

Nothing is recomputed here: the rows come from build_spec_param_listing.build_rows(),
the exact dataset the four-layer fact check verified, and the build asserts that the
matrix holds the same totals (77 batches, 1 038 result lines, 729 missing cells' worth
of gaps). Where one parameter carries more than one certificate (the paired IPH
microbiology certificates, repeat assays), the lines stack inside the cell one per
certificate; a cell can hold only one hyperlink, so the reference cell links to the
first listed scan and the "eCoA index" sheet carries every certificate's own link.

Laboratory abbreviations follow the QC Manager's referencing convention:
CNP (UKIM Faculty of Pharmacy — Center for Natural Products), FARM (Farmahem),
IPH (Institute of Public Health), SPL (State Phytosanitary Laboratory), PP (in-house).
"""
import csv
import os
import sys
from collections import OrderedDict

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import build_spec_param_listing as bl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_XLSX = os.path.join(HERE, "exports", "PP_Spec_Parameter_Matrix.xlsx")
OUT_TSV = os.path.join(HERE, "exports", "PP_Spec_Parameter_Matrix.tsv")

# The reference convention writes UKIM's certificates under the Center's own initials.
REF_LAB = {"UKIM": "CNP"}

# (item №, short column title, unit shown in the header, acceptance criterion)
MATRIX_PANEL = [
    ("1",    "Macroscopic ID (Test A)",    "",      "Conforms to description"),
    ("2",    "Microscopic ID (Test B)",    "",      "Conforms to description"),
    ("3",    "HPTLC ID (Test C)",          "",      "Identity confirmed"),
    ("4",    "Total Δ⁹-THC",               "%",     "Per target grade (QCSP 001 §01)"),
    ("5",    "Total CBD",                  "%",     "≤ 1.0"),
    ("6",    "Total CBN",                  "%",     "≤ 1.0"),
    ("7",    "Foreign Matter",             "%",     "≤ 2.0"),
    ("8",    "Loss on Drying",             "%",     "≤ 12.0"),
    ("9.1",  "TAMC",                       "CFU/g", "≤ 10⁵"),
    ("9.2",  "TYMC",                       "CFU/g", "≤ 10⁴"),
    ("9.3",  "Bile-tol. gram-negative",    "CFU/g", "≤ 10⁴"),
    ("9.4",  "Salmonella",                 "",      "Absence /25 g"),
    ("9.5",  "Escherichia coli",           "",      "Absence /1 g"),
    ("10.1", "Aflatoxin B1",               "µg/kg", "≤ 2"),
    ("10.2", "Total Aflatoxins",           "µg/kg", "≤ 4"),
    ("10.3", "Ochratoxin A",               "µg/kg", "≤ 20"),
    ("11.1", "Lead (Pb)",                  "mg/kg", "≤ 0.5"),
    ("11.2", "Cadmium (Cd)",               "mg/kg", "≤ 0.3"),
    ("11.3", "Arsenic (As)",               "mg/kg", "≤ 0.2"),
    ("11.4", "Mercury (Hg)",               "mg/kg", "≤ 0.1"),
    ("12",   "Pesticide Residues",         "",      "≤ LOQ (Ph. Eur. 2.8.13)"),
]

IDENTITY = [("#", 4), ("Production", 9), ("Batch", 13), ("P-Number", 10),
            ("Strain", 17), ("Spec document", 16), ("Grade (v.02)", 14),
            ("Product code", 19)]
N_ID = len(IDENTITY)

RESULT_W = {"12": 26, "1": 11, "2": 11, "3": 11}
REF_W = 20

NAVY = "1B3A5C"
GOLD_TINT = "FBF6E9"
SUB_GREY = "E9EEF5"
BAND = "F4F7FB"
MISS = "9AA7B4"
INK = "16232B"
LINK = "0563C1"

TITLE_NOTE = (
    "Purely Plant — QCSP 001 specification matrix: one row per batch, chronological by "
    "the production date encoded in the batch number; one column pair (Result | eCoA "
    "reference) per specification parameter, acceptance criteria in the frozen header. "
    "Source: %s. Values as transcribed from the certificates; uncertainty excluded; "
    "units live in the header, not the cells. Repeat assays stack one line per "
    "certificate — the reference cell links to the first listed scan, and every "
    "certificate's own link is on the 'eCoA index' sheet. Grade is classification "
    "against the v.02 ladder, not a disposition. Labs: CNP = UKIM Faculty of Pharmacy "
    "(Center for Natural Products), FARM = Farmahem, IPH = Institute of Public Health, "
    "SPL = State Phytosanitary Laboratory, PP = Purely Plant in-house."
    % bl.SOURCE_NOTE)


def matrix_value(rec):
    """The result line for a matrix cell: bare value, unit stripped into the header."""
    v = (rec["value"] or "").strip()
    u = rec["unit"]
    if u not in ("—", "") and v.endswith(u):
        head = v[: -len(u)].strip()
        if head:
            v = head
    return v.replace(" — no analyte detected", "")


def ref_line(rec):
    lab = REF_LAB.get(rec["lab"], rec["lab"])
    return "%s, %s, %s" % (rec["cert"], rec["date"], lab)


def pivot(listing):
    """listing rows -> ordered batches, each with per-item stacked cells."""
    batches = OrderedDict()
    for rec in listing:
        b = batches.setdefault(rec["batch"], {
            "chrono": rec["chrono"], "prod": rec["prod"], "batch": rec["batch"],
            "p": rec["p"], "strain": rec["strain"], "spec_doc": rec["spec_doc"],
            "grade": rec["grade"], "code": rec["code"],
            "cells": {no: {"values": [], "refs": [], "links": []}
                      for no, _t, _u, _ac in MATRIX_PANEL},
        })
        cell = b["cells"][rec["no"]]
        if rec["value"].startswith("Missing"):
            continue
        cell["values"].append(matrix_value(rec))
        cell["refs"].append(ref_line(rec))
        cell["links"].append(rec["link"])
    return list(batches.values())


def cert_index(listing):
    """Unique certificates with the batches and spec items each one covers."""
    idx = OrderedDict()
    for rec in listing:
        if rec["cert"] == "—" or rec["value"].startswith("Missing"):
            continue
        key = (rec["cert"], rec["date"], rec["lab"], rec["link"])
        e = idx.setdefault(key, {"batches": [], "items": []})
        if rec["batch"] not in e["batches"]:
            e["batches"].append(rec["batch"])
        if rec["no"] not in e["items"]:
            e["items"].append(rec["no"])
    rows = []
    for (cert, date, lab, link), e in idx.items():
        rows.append({"cert": cert, "date": date,
                     "lab": REF_LAB.get(lab, lab), "link": link,
                     "batches": ", ".join(e["batches"]),
                     "items": ", ".join(e["items"])})
    rows.sort(key=lambda r: (r["date"] or "9999", r["cert"]))
    return rows


def write_xlsx(rows, index_rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spec matrix"
    thin = Side(style="thin", color="D6DEEA")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    n_cols = N_ID + 2 * len(MATRIX_PANEL)

    def put(r, c, v, **font):
        cell = ws.cell(r, c)
        cell.value = v
        cell.font = Font(name="Arial", size=8, **font)
        cell.border = border
        return cell

    # row 1 — provenance / reading note
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    c = put(1, 1, TITLE_NOTE, italic=True, color="555555")
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[1].height = 58

    # rows 2-4 — frozen headers: parameter (with №+unit), A.C., sub-labels
    for i, (title, _w) in enumerate(IDENTITY):
        col = i + 1
        ws.merge_cells(start_row=2, start_column=col, end_row=4, end_column=col)
        c = put(2, col, title, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", start_color=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for r in (3, 4):
            ws.cell(r, col).fill = PatternFill("solid", start_color=NAVY)
            ws.cell(r, col).border = border

    for j, (no, title, unit, ac) in enumerate(MATRIX_PANEL):
        col = N_ID + 1 + 2 * j
        head = "%s — %s" % (no, title) + (" (%s)" % unit if unit else "")
        ws.merge_cells(start_row=2, start_column=col, end_row=2, end_column=col + 1)
        c = put(2, col, head, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", start_color=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.cell(2, col + 1).fill = PatternFill("solid", start_color=NAVY)
        ws.cell(2, col + 1).border = border

        ws.merge_cells(start_row=3, start_column=col, end_row=3, end_column=col + 1)
        c = put(3, col, "A.C.  %s" % ac, bold=True, color=INK)
        c.fill = PatternFill("solid", start_color=GOLD_TINT)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.cell(3, col + 1).fill = PatternFill("solid", start_color=GOLD_TINT)
        ws.cell(3, col + 1).border = border

        for off, label in ((0, "Result"), (1, "eCoA (code, date, lab)")):
            c = put(4, col + off, label, bold=True, color="4A5B6C")
            c.fill = PatternFill("solid", start_color=SUB_GREY)
            c.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[2].height = 26
    ws.row_dimensions[3].height = 22
    ws.row_dimensions[4].height = 13

    # data — one row per batch
    for i, b in enumerate(rows):
        r = 5 + i
        band = (i % 2 == 1)
        fill = PatternFill("solid", start_color=BAND) if band else None
        ident = [b["chrono"], b["prod"], b["batch"], b["p"], b["strain"],
                 b["spec_doc"], b["grade"], b["code"]]
        max_lines = 1
        for cidx, v in enumerate(ident, start=1):
            c = put(r, cidx, v, bold=(cidx == 3), color=INK)
            c.alignment = Alignment(vertical="top", wrap_text=(cidx >= 5),
                                    horizontal="center" if cidx <= 2 else "left")
            if fill:
                c.fill = fill

        for j, (no, _t, _u, _ac) in enumerate(MATRIX_PANEL):
            col = N_ID + 1 + 2 * j
            cell = b["cells"][no]
            if not cell["values"]:
                c = put(r, col, "Missing / not tested", color=MISS)
                c.alignment = Alignment(vertical="top", wrap_text=True)
                c2 = put(r, col + 1, "—", color=MISS)
                c2.alignment = Alignment(vertical="top", horizontal="center")
                if fill:
                    c.fill = fill
                    c2.fill = fill
                continue
            max_lines = max(max_lines, len(cell["values"]))
            c = put(r, col, "\n".join(cell["values"]), color=INK)
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c2 = put(r, col + 1, "\n".join(cell["refs"]), color=LINK,
                     underline="single")
            c2.alignment = Alignment(vertical="top", wrap_text=True)
            first_link = next((l for l in cell["links"] if l), None)
            if first_link:
                c2.hyperlink = first_link
            if fill:
                c.fill = fill
                c2.fill = fill
        ws.row_dimensions[r].height = max(14, 11 * max_lines + 3)

    for i, (_t, w) in enumerate(IDENTITY):
        ws.column_dimensions[get_column_letter(i + 1)].width = w
    for j, (no, _t, _u, _ac) in enumerate(MATRIX_PANEL):
        col = N_ID + 1 + 2 * j
        ws.column_dimensions[get_column_letter(col)].width = RESULT_W.get(no, 11)
        ws.column_dimensions[get_column_letter(col + 1)].width = REF_W
    ws.freeze_panes = "F5"

    # sheet 2 — every certificate's own link
    wsx = wb.create_sheet("eCoA index")
    for cidx, (h, w) in enumerate([("eCoA code", 20), ("Issued", 11), ("Lab", 6),
                                   ("Batches", 34), ("Spec items", 22),
                                   ("Scan", 8)], start=1):
        c = wsx.cell(1, cidx, h)
        c.font = Font(name="Arial", size=8, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", start_color=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border
        wsx.column_dimensions[get_column_letter(cidx)].width = w
    for i, e in enumerate(index_rows, start=2):
        vals = [e["cert"], e["date"], e["lab"], e["batches"], e["items"]]
        for cidx, v in enumerate(vals, start=1):
            c = wsx.cell(i, cidx, v)
            c.font = Font(name="Arial", size=8, color=INK)
            c.alignment = Alignment(vertical="top",
                                    wrap_text=(cidx in (4, 5)),
                                    horizontal="center" if cidx in (2, 3) else "left")
            c.border = border
        c = wsx.cell(i, 6)
        if e["link"]:
            c.value = "open"
            c.hyperlink = e["link"]
            c.font = Font(name="Arial", size=8, color=LINK, underline="single")
        else:
            c.value = "—"
            c.font = Font(name="Arial", size=8, color=MISS)
        c.alignment = Alignment(horizontal="center", vertical="top")
        c.border = border
    wsx.freeze_panes = "A2"
    wsx.auto_filter.ref = "A1:F%d" % (len(index_rows) + 1)

    wb.save(OUT_XLSX)


def write_tsv(rows):
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        head1 = [t for t, _w in IDENTITY]
        head2 = [""] * N_ID
        for no, title, unit, ac in MATRIX_PANEL:
            head1 += ["%s — %s%s" % (no, title, " (%s)" % unit if unit else ""),
                      "eCoA reference"]
            head2 += ["A.C. %s" % ac, ""]
        w.writerow(head1)
        w.writerow(head2)
        for b in rows:
            line = [b["chrono"], b["prod"], b["batch"], b["p"], b["strain"],
                    b["spec_doc"], b["grade"], b["code"]]
            for no, _t, _u, _ac in MATRIX_PANEL:
                cell = b["cells"][no]
                if not cell["values"]:
                    line += ["Missing / not tested", "—"]
                else:
                    line += [" ; ".join(cell["values"]), " ; ".join(cell["refs"])]
            w.writerow(line)


def main():
    listing, stats, n_batches = bl.build_rows()
    rows = pivot(listing)
    index_rows = cert_index(listing)

    # the matrix must hold exactly the fact-checked totals — nothing lost, nothing added
    assert len(rows) == n_batches, (len(rows), n_batches)
    n_lines = sum(len(b["cells"][no]["values"])
                  for b in rows for no, _t, _u, _ac in MATRIX_PANEL)
    n_missing = sum(1 for b in rows for no, _t, _u, _ac in MATRIX_PANEL
                    if not b["cells"][no]["values"])
    assert n_lines == stats["results"], (n_lines, stats["results"])
    assert n_missing == stats["missing"], (n_missing, stats["missing"])

    write_xlsx(rows, index_rows)
    write_tsv(rows)

    print("batches (rows): %d   result lines: %d   missing cells: %d   certs: %d"
          % (len(rows), n_lines, n_missing, len(index_rows)))
    print("wrote %s (%d KB)" % (os.path.relpath(OUT_XLSX, HERE),
                                os.path.getsize(OUT_XLSX) // 1024))
    print("wrote %s (%d KB)" % (os.path.relpath(OUT_TSV, HERE),
                                os.path.getsize(OUT_TSV) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
