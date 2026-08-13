#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wide-format spec matrix: one chronological row-block per batch, parameters as columns.

The transposition of exports/PP_Spec_Parameter_Listing.xlsx requested by the QC Manager:
the same fact-checked data spread across the columns to the right, row-per-batch style.
Every QCSP 001 parameter owns a dedicated column pair — Result | eCoA reference — under
frozen header rows that carry the parameter name (with unit) and its acceptance criterion
in dedicated cells. Each result's provenance is rendered compactly as "code, date, lab"
(e.g. ППК25105, 17.04.2025, CNP) and that text is hyperlinked to the certificate scan.

Where one batch was tested in more than one campaign — release testing in one season, a
re-test a year later — the batch row splits into testing-round sub-rows, one per campaign,
so results from different dates never share a cell. Rounds are clustered on certificate
issue dates (a gap of more than 90 days opens a new round); the batch identity cells span
the sub-rows. A parameter never tested for the batch reads "Missing / not tested" once,
spanning the sub-rows; a parameter tested in one round but not another reads "—" in the
round that lacks it.

The specification-document and grade identity columns are gone: the grade now sits in its
own cell immediately right of each THC assay, as classification of that assay against the
cultivar's QCSP 001 v.02 ladder — "Grade III, 15.00 – 20.00" — never a disposition.

Column C carries the CoQ document code each batch would need. QCSOP 012 v.03 §6.4.2 sets
the convention — CoQ-PP-[YYYY]-[NNNN], the next sequential number for the certificate
type within the calendar year, drawn from the Certificate Issuance Register (QCLB 020) —
so the codes here are proposed sequential assignments in chronological batch order,
pending the register entries the QC Manager makes at final approval.

Nothing is recomputed from the certificates: the rows come from
build_spec_param_listing.build_rows(), the dataset the four-layer fact check verified,
and the build asserts the matrix holds the same totals (77 batches, 1 038 result lines,
729 missing parameter cells). A cell holds one hyperlink, so a reference cell stacking
the paired same-day certificates links to the first scan; the "eCoA index" sheet carries
every certificate's own link.

Laboratory abbreviations follow the QC Manager's referencing convention:
CNP (UKIM Faculty of Pharmacy — Center for Natural Products), FARM (Farmahem),
IPH (Institute of Public Health), SPL (State Phytosanitary Laboratory), PP (in-house).
"""
import csv
import datetime
import os
import re
import sys
from collections import OrderedDict

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import build_house_specs as hs
import build_spec_param_listing as bl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_XLSX = os.path.join(HERE, "exports", "PP_Spec_Parameter_Matrix.xlsx")
OUT_TSV = os.path.join(HERE, "exports", "PP_Spec_Parameter_Matrix.tsv")

# The reference convention writes UKIM's certificates under the Center's own initials.
REF_LAB = {"UKIM": "CNP"}

COQ_YEAR = 2026          # calendar year the CoQs would be created in
ROUND_GAP_DAYS = 90      # a longer gap between certificate dates opens a new round

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
THC_ITEM = "4"           # the one parameter that carries the extra Grade column

IDENTITY = [("#", 4), ("Production", 9), ("CoQ doc. code\n(proposed)", 16),
            ("Batch", 13), ("P-Number", 10), ("Strain", 17), ("Product code", 19)]
N_ID = len(IDENTITY)

RESULT_W = {"12": 26, "1": 11, "2": 11, "3": 11}
GRADE_W = 18
REF_W = 20

NAVY = "1B3A5C"
GOLD_TINT = "FBF6E9"
SUB_GREY = "E9EEF5"
BAND = "F4F7FB"
MISS = "9AA7B4"
INK = "16232B"
LINK = "0563C1"

TITLE_NOTE = (
    "Purely Plant — QCSP 001 specification matrix: one row-block per batch, "
    "chronological by the production date encoded in the batch number; batches tested "
    "in more than one campaign split into testing-round sub-rows (certificate issue "
    "dates more than %d days apart), so results from different dates never share a "
    "cell. One column pair (Result | eCoA reference) per specification parameter, "
    "acceptance criteria in the frozen header; the THC assay carries an extra Grade "
    "cell — classification of that assay against the cultivar's QCSP 001 v.02 ladder, "
    "not a disposition. Column C proposes the CoQ document code each batch would need "
    "per QCSOP 012 v.03 §6.4.2 (CoQ-PP-[YYYY]-[NNNN], sequential per calendar year); "
    "final numbers are assigned from the Certificate Issuance Register (QCLB 020) at "
    "approval. Source: %s. Values as transcribed from the certificates; uncertainty "
    "excluded; units live in the header, not the cells. Same-day paired certificates "
    "stack one line each within a sub-row — the reference cell links to the first "
    "listed scan, and every certificate's own link is on the 'eCoA index' sheet. "
    "Labs: CNP = UKIM Faculty of Pharmacy (Center for Natural Products), "
    "FARM = Farmahem, IPH = Institute of Public Health, SPL = State Phytosanitary "
    "Laboratory, PP = Purely Plant in-house."
    % (ROUND_GAP_DAYS, bl.SOURCE_NOTE))

DATE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")


def parse_date(s):
    m = DATE_RE.match((s or "").strip())
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


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


_LADDERS = {}


def ladder_for(strain):
    if strain not in _LADDERS:
        pub = hs.PUBLISHED.get(strain)
        _LADDERS[strain] = hs.extend(pub[3])[0] if pub else None
    return _LADDERS[strain]


def grade_line(strain, value):
    """'Grade III, 15.00 – 20.00' for a numeric assay; '—' for qualifiers/no ladder."""
    ladder = ladder_for(strain)
    if ladder is None:
        return "—"
    v = value.strip()
    if v.startswith(("<", "≤")) or not v:
        return "—"
    m = re.match(r"^\d+(?:\.\d+)?$", v)
    if not m:
        return "—"
    g = hs.grade_of(ladder, float(v))
    if g is None:
        return "outside every grade"
    for label, _nominal, floor, cap in ladder:
        if label == g:
            return "Grade %s, %.2f – %.2f" % (g, floor, cap)
    return "Grade %s" % g


def pivot(listing):
    """listing rows -> ordered batches, each with testing rounds of per-item cells."""
    batches = OrderedDict()
    for rec in listing:
        b = batches.setdefault(rec["batch"], {
            "chrono": rec["chrono"], "prod": rec["prod"], "batch": rec["batch"],
            "p": rec["p"], "strain": rec["strain"], "code": rec["code"],
            "entries": [],
        })
        if not rec["value"].startswith("Missing"):
            b["entries"].append(rec)

    for b in batches.values():
        # cluster certificate issue dates into testing rounds
        dates = sorted({d for d in (parse_date(r["date"]) for r in b["entries"]) if d})
        cluster_of = {}
        start = None
        for d in dates:
            if start is None or (d - prev).days > ROUND_GAP_DAYS:
                start = d
            cluster_of[d] = start
            prev = d
        starts = sorted(set(cluster_of.values()))
        idx_of = {s: i for i, s in enumerate(starts)}
        n_rounds = max(1, len(starts))

        rounds = [
            {no: {"values": [], "grades": [], "refs": [], "links": []}
             for no, _t, _u, _ac in MATRIX_PANEL}
            for _ in range(n_rounds)
        ]
        for rec in b["entries"]:
            d = parse_date(rec["date"])
            ri = idx_of[cluster_of[d]] if d else 0
            cell = rounds[ri][rec["no"]]
            val = matrix_value(rec)
            cell["values"].append(val)
            cell["refs"].append(ref_line(rec))
            cell["links"].append(rec["link"])
            if rec["no"] == THC_ITEM:
                cell["grades"].append(grade_line(b["strain"], val))
        b["rounds"] = rounds
        b["coq"] = "CoQ-PP-%d-%04d" % (COQ_YEAR, b["chrono"])
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


def group_cols():
    """(item no -> (first column, width in columns)) for the parameter groups."""
    out, col = {}, N_ID + 1
    for no, _t, _u, _ac in MATRIX_PANEL:
        w = 3 if no == THC_ITEM else 2
        out[no] = (col, w)
        col += w
    return out, col - 1


def write_xlsx(rows, index_rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spec matrix"
    thin = Side(style="thin", color="D6DEEA")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    groups, n_cols = group_cols()

    def put(r, c, v, **font):
        cell = ws.cell(r, c)
        cell.value = v
        cell.font = Font(name="Arial", size=8, **font)
        cell.border = border
        return cell

    def fill_range(r1, c1, r2, c2, color):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                ws.cell(r, c).fill = PatternFill("solid", start_color=color)
                ws.cell(r, c).border = border

    # row 1 — provenance / reading note
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    c = put(1, 1, TITLE_NOTE, italic=True, color="555555")
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[1].height = 76

    # rows 2-4 — frozen headers: parameter (with №+unit), A.C., sub-labels
    for i, (title, _w) in enumerate(IDENTITY):
        col = i + 1
        ws.merge_cells(start_row=2, start_column=col, end_row=4, end_column=col)
        c = put(2, col, title, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        fill_range(2, col, 4, col, NAVY)

    for no, title, unit, ac in MATRIX_PANEL:
        col, w = groups[no]
        head = "%s — %s" % (no, title) + (" (%s)" % unit if unit else "")
        ws.merge_cells(start_row=2, start_column=col, end_row=2, end_column=col + w - 1)
        c = put(2, col, head, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        fill_range(2, col, 2, col + w - 1, NAVY)

        ws.merge_cells(start_row=3, start_column=col, end_row=3, end_column=col + w - 1)
        c = put(3, col, "A.C.  %s" % ac, bold=True, color=INK)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        fill_range(3, col, 3, col + w - 1, GOLD_TINT)

        labels = (["Result", "Grade (v.02)", "eCoA (code, date, lab)"] if w == 3
                  else ["Result", "eCoA (code, date, lab)"])
        for off, label in enumerate(labels):
            c = put(4, col + off, label, bold=True, color="4A5B6C")
            c.fill = PatternFill("solid", start_color=SUB_GREY)
            c.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[2].height = 26
    ws.row_dimensions[3].height = 22
    ws.row_dimensions[4].height = 13

    # data — one row-block per batch, one sub-row per testing round
    r = 5
    for bi, b in enumerate(rows):
        n_r = len(b["rounds"])
        band = (bi % 2 == 1)
        fill = BAND if band else None
        r_top, r_bot = r, r + n_r - 1

        ident = [b["chrono"], b["prod"], b["coq"], b["batch"], b["p"], b["strain"],
                 b["code"]]
        for cidx, v in enumerate(ident, start=1):
            if n_r > 1:
                ws.merge_cells(start_row=r_top, start_column=cidx,
                               end_row=r_bot, end_column=cidx)
            c = put(r_top, cidx, v, bold=(cidx == 4), color=INK)
            c.alignment = Alignment(vertical="top", wrap_text=(cidx >= 6),
                                    horizontal="center" if cidx <= 2 else "left")
            if fill:
                fill_range(r_top, cidx, r_bot, cidx, fill)
            else:
                for rr in range(r_top, r_bot + 1):
                    ws.cell(rr, cidx).border = border

        line_counts = [1] * n_r
        for no, _t, _u, _ac in MATRIX_PANEL:
            col, w = groups[no]
            tested_rounds = [ri for ri in range(n_r)
                             if b["rounds"][ri][no]["values"]]
            if not tested_rounds:
                # never tested for this batch — one statement spanning the sub-rows
                for off in range(w):
                    if n_r > 1:
                        ws.merge_cells(start_row=r_top, start_column=col + off,
                                       end_row=r_bot, end_column=col + off)
                    txt = "Missing / not tested" if off == 0 else "—"
                    c = put(r_top, col + off, txt, color=MISS)
                    c.alignment = Alignment(vertical="top", wrap_text=(off == 0),
                                            horizontal="left" if off == 0 else "center")
                    if fill:
                        fill_range(r_top, col + off, r_bot, col + off, fill)
                    else:
                        for rr in range(r_top, r_bot + 1):
                            ws.cell(rr, col + off).border = border
                continue

            for ri in range(n_r):
                cell = b["rounds"][ri][no]
                rr = r_top + ri
                if not cell["values"]:
                    # tested in another round, not this one
                    for off in range(w):
                        c = put(rr, col + off, "—", color=MISS)
                        c.alignment = Alignment(vertical="top", horizontal="center")
                        if fill:
                            c.fill = PatternFill("solid", start_color=fill)
                    continue
                line_counts[ri] = max(line_counts[ri], len(cell["values"]))
                parts = [("\n".join(cell["values"]), INK, False)]
                if w == 3:
                    parts.append(("\n".join(cell["grades"]), INK, False))
                parts.append(("\n".join(cell["refs"]), LINK, True))
                for off, (txt, color, is_ref) in enumerate(parts):
                    c = put(rr, col + off, txt, color=color,
                            underline="single" if is_ref else "none")
                    c.alignment = Alignment(vertical="top", wrap_text=True)
                    if is_ref:
                        first_link = next((l for l in cell["links"] if l), None)
                        if first_link:
                            c.hyperlink = first_link
                    if fill:
                        c.fill = PatternFill("solid", start_color=fill)

        for ri in range(n_r):
            ws.row_dimensions[r_top + ri].height = max(14, 11 * line_counts[ri] + 3)
        r = r_bot + 1

    for i, (_t, w) in enumerate(IDENTITY):
        ws.column_dimensions[get_column_letter(i + 1)].width = w
    for no, _t, _u, _ac in MATRIX_PANEL:
        col, w = groups[no]
        ws.column_dimensions[get_column_letter(col)].width = RESULT_W.get(no, 11)
        if w == 3:
            ws.column_dimensions[get_column_letter(col + 1)].width = GRADE_W
        ws.column_dimensions[get_column_letter(col + w - 1)].width = REF_W
    ws.freeze_panes = "G5"

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
        head1 = [t.replace("\n", " ") for t, _w in IDENTITY]
        head2 = [""] * N_ID
        for no, title, unit, ac in MATRIX_PANEL:
            head1.append("%s — %s%s" % (no, title, " (%s)" % unit if unit else ""))
            head2.append("A.C. %s" % ac)
            if no == THC_ITEM:
                head1.append("Grade (v.02)")
                head2.append("")
            head1.append("eCoA reference")
            head2.append("")
        w.writerow(head1)
        w.writerow(head2)
        for b in rows:
            n_r = len(b["rounds"])
            for ri in range(n_r):
                if ri == 0:
                    line = [b["chrono"], b["prod"], b["coq"], b["batch"], b["p"],
                            b["strain"], b["code"]]
                else:
                    line = [""] * N_ID
                for no, _t, _u, _ac in MATRIX_PANEL:
                    cell = b["rounds"][ri][no]
                    tested_any = any(b["rounds"][x][no]["values"] for x in range(n_r))
                    if cell["values"]:
                        line.append(" ; ".join(cell["values"]))
                        if no == THC_ITEM:
                            line.append(" ; ".join(cell["grades"]))
                        line.append(" ; ".join(cell["refs"]))
                    else:
                        txt = "—" if tested_any else (
                            "Missing / not tested" if ri == 0 else "")
                        line.append(txt)
                        if no == THC_ITEM:
                            line.append("—" if txt else "")
                        line.append("—" if txt else "")
                w.writerow(line)


def main():
    listing, stats, n_batches = bl.build_rows()
    rows = pivot(listing)
    index_rows = cert_index(listing)

    # the matrix must hold exactly the fact-checked totals — nothing lost, nothing added
    assert len(rows) == n_batches, (len(rows), n_batches)
    n_lines = sum(len(rnd[no]["values"])
                  for b in rows for rnd in b["rounds"]
                  for no, _t, _u, _ac in MATRIX_PANEL)
    n_missing = sum(1 for b in rows for no, _t, _u, _ac in MATRIX_PANEL
                    if not any(rnd[no]["values"] for rnd in b["rounds"]))
    assert n_lines == stats["results"], (n_lines, stats["results"])
    assert n_missing == stats["missing"], (n_missing, stats["missing"])
    n_rounds = sum(len(b["rounds"]) for b in rows)
    multi = [(b["batch"], len(b["rounds"])) for b in rows if len(b["rounds"]) > 1]

    write_xlsx(rows, index_rows)
    write_tsv(rows)

    print("batches: %d   sub-rows: %d   multi-round batches: %d   "
          "result lines: %d   missing cells: %d   certs: %d"
          % (len(rows), n_rounds, len(multi), n_lines, n_missing, len(index_rows)))
    for name, k in multi:
        print("  %s: %d rounds" % (name, k))
    print("wrote %s (%d KB)" % (os.path.relpath(OUT_XLSX, HERE),
                                os.path.getsize(OUT_XLSX) // 1024))
    print("wrote %s (%d KB)" % (os.path.relpath(OUT_TSV, HERE),
                                os.path.getsize(OUT_TSV) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
