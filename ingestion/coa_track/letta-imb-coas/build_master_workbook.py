#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the master PP eCoA workbook: two sheets from the merged long-form TSV.

Sheet 1 'Batch Summary'  - row-per-batch wide view (2 rows/batch: Results + Sources)
Sheet 2 'Audit Trail'    - full per-parameter long form (verbatim, 2339 rows)
"""
import re
import csv
from collections import defaultdict, OrderedDict

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import PieChart, Reference

SRC = "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad/master_coa_ALL.tsv"
OUT = "/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad/PP_eCoA_Master_Database.xlsx"

FONT_NAME = "Arial"

# ---------------------------------------------------------------- load ----
rows = []
with open(SRC, encoding="utf-8") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        row["Seq"] = int(row["Seq"])
        rows.append(row)

by_seq = defaultdict(list)
for row in rows:
    by_seq[row["Seq"]].append(row)

seqs = sorted(by_seq.keys())
assert seqs == list(range(1, 81)), "Seq coverage broken: %r" % (seqs,)

# ---------------------------------------------------------- classify ------
BUCKETS = [
    ("identification", re.compile(r"identification|идентифика", re.I)),
    ("foreign_matter", re.compile(r"foreign matter|страни матери", re.I)),
    ("loss_on_drying", re.compile(r"loss on drying|губиток.*сушењ", re.I)),
    ("cbn", re.compile(r"\btotal cbn\b|вкупен cbn|^cbn$|^cbn\s", re.I)),
    ("cbd", re.compile(r"total cbd|вкупен cbd|total cannabidiol\b(?!ic)", re.I)),
    ("thc", re.compile(r"total.*(δ9|delta.?9|thc)|вкупно.*thc|total δ9-tetrahydrocannabinol", re.I)),
    ("aflatoxins", re.compile(r"sum aflatoxins|total aflatoxin", re.I)),
    ("ochratoxin", re.compile(r"ochratoxin", re.I)),
    ("pb", re.compile(r"\blead\b|олово", re.I)),
    ("cd", re.compile(r"cadmium|кадмиум", re.I)),
    ("as_", re.compile(r"\barsenic\b|арсен", re.I)),
    ("hg", re.compile(r"\bmercury\b|жива", re.I)),
    ("tamc", re.compile(r"\btamc\b|total aerobic microbial", re.I)),
    ("tymc", re.compile(r"\btymc\b|yeasts.*moulds|combined yeast", re.I)),
    ("bile", re.compile(r"bile.?tolerant", re.I)),
    ("ecoli", re.compile(r"escherichia|e\.\s?coli", re.I)),
    ("salmonella", re.compile(r"salmonella", re.I)),
]
PESTICIDE_RE = re.compile(r"pesticide|insecticide", re.I)
# Stability-study results describe the batch over time under ICH storage conditions.
# They must never merge into the release-disposition columns, or a cell reads e.g.
# "Total CBD: 0.17% | 0.05% | 22.83%" mixing release with month-3/6/9 timepoints.
STABILITY_RE = re.compile(r"stabilit|стабилн|month\s*\d|месец|\d+\s*°?C\s*/\s*\d+\s*%\s*RH", re.I)
GAP_RE = re.compile(r"^\[COVERAGE GAP\]$")
OVERALL_RE = re.compile(r"overall result|заклучок|^\[NOTE\]", re.I)
NOTFOUND_RESULT_RE = re.compile(r"^(н\.?д\.?|n\.?d\.?|nd)\b", re.I)
FLAG_RE = re.compile(r"DATA INTEGRITY FLAG|NONCONFORM|NON-CONFORM|DOES NOT CONFORM|Не одговара", re.I)

COLS = OrderedDict([
    ("identification", "Identification"),
    ("foreign_matter", "Foreign Matter"),
    ("loss_on_drying", "Loss on Drying"),
    ("cbn", "Total CBN"),
    ("cbd", "Total CBD"),
    ("thc", "Total Δ9-THC"),
    ("aflatoxins", "Aflatoxins (ΣB1+B2+G1+G2)"),
    ("ochratoxin", "Ochratoxin A"),
    ("pb", "Lead (Pb)"),
    ("cd", "Cadmium (Cd)"),
    ("as_", "Arsenic (As)"),
    ("hg", "Mercury (Hg)"),
    ("tamc", "TAMC"),
    ("tymc", "TYMC"),
    ("bile", "Bile-tolerant GNB"),
    ("ecoli", "E. coli"),
    ("salmonella", "Salmonella"),
    ("pesticides", "Pesticide/Insecticide Screen"),
])


def classify(param_text):
    if GAP_RE.match(param_text):
        return "gap"
    if OVERALL_RE.search(param_text):
        return "overall"
    if STABILITY_RE.search(param_text):
        return "stability"
    if PESTICIDE_RE.search(param_text):
        return "pesticides"
    for key, rx in BUCKETS:
        if rx.search(param_text):
            return key
    return None


def cite(r):
    """One-line certificate citation for a row."""
    code = r["Certificate Code"].strip()
    date = r["Issue Date"].strip()
    inst = r["Issuing Institution"].strip()
    parts = [p for p in (code, date, inst) if p and p not in ("n/a", "N/A")]
    return " • ".join(parts) if parts else ""


def batch_pivot(seq):
    """Return dict: bucket_key -> {'value': str, 'source': str, 'link': str}"""
    brows = by_seq[seq]
    out = {}
    pest_total = 0
    pest_detected = []
    gap_notes = []
    overall_notes = []
    flags = []
    stability_count = 0

    bucket_hits = defaultdict(list)

    for r in brows:
        param = r["Parameter"]
        kind = classify(param)
        if kind == "gap":
            gap_notes.append(r["Result"])
            continue
        if kind == "overall":
            overall_notes.append(r["Result"])
            continue
        if kind == "stability":
            stability_count += 1
            continue
        if kind == "pesticides":
            pest_total += 1
            res = r["Result"].strip()
            if not NOTFOUND_RESULT_RE.match(res):
                pest_detected.append("%s: %s" % (param, res))
            bucket_hits["pesticides"].append(r)
            continue
        if kind:
            bucket_hits[kind].append(r)
        if FLAG_RE.search(r["Result"]):
            flags.append(param)

    for key in COLS:
        if key == "pesticides":
            if pest_total == 0:
                out[key] = {"value": "—", "source": "", "link": ""}
            elif pest_detected:
                out[key] = {
                    "value": "%d/%d N.D. — DETECTED: %s" % (pest_total - len(pest_detected), pest_total, "; ".join(pest_detected)),
                    "source": cite(bucket_hits["pesticides"][0]) if bucket_hits["pesticides"] else "",
                    "link": bucket_hits["pesticides"][0]["Drive File Link"] if bucket_hits["pesticides"] else "",
                }
            else:
                out[key] = {
                    "value": "All N.D. (%d compounds)" % pest_total,
                    "source": cite(bucket_hits["pesticides"][0]) if bucket_hits["pesticides"] else "",
                    "link": bucket_hits["pesticides"][0]["Drive File Link"] if bucket_hits["pesticides"] else "",
                }
            continue
        hits = bucket_hits.get(key, [])
        if not hits:
            out[key] = {"value": "—", "source": "", "link": ""}
        else:
            vals = []
            srcs = []
            link = hits[0]["Drive File Link"]
            for h in hits:
                v = h["Result"].strip()
                vals.append(v)
                s = cite(h)
                if s and s not in srcs:
                    srcs.append(s)
            out[key] = {
                "value": " | ".join(dict.fromkeys(vals)),
                "source": " | ".join(srcs),
                "link": link,
            }

    meta = brows[0]
    identity = {
        "seq": seq,
        "cultivation_batch": meta["Cultivation Batch"],
        "p_number": meta["P-Number"],
        "strain": meta["Strain"],
    }

    # status determination
    is_open_issue = any("DOES NOT CONFORM" in n or "NON-CONFORM" in n for n in overall_notes) or \
        any("DOES NOT CONFORM" in n or "NONCONFORM" in n for n in gap_notes)
    has_gap = len(gap_notes) > 0
    has_flag = len(flags) > 0

    if is_open_issue:
        status = "OPEN QC ISSUE"
    elif has_gap:
        status = "PARTIAL"
    elif has_flag:
        status = "COMPLETE (flag noted)"
    else:
        status = "COMPLETE"

    notes_parts = []
    if overall_notes:
        notes_parts.append("OVERALL: " + " / ".join(overall_notes)[:300])
    if gap_notes:
        # summarize gap categories rather than dumping full text
        cats = set()
        for n in gap_notes:
            low = n.lower()
            if "pesticide" in low:
                cats.add("pesticides")
            if "heavy" in low or "metal" in low:
                cats.add("heavy metals")
            if "mycotox" in low:
                cats.add("mycotoxins")
            if "microbio" in low:
                cats.add("microbiology")
            if "identification" in low or "foreign" in low or "loss on drying" in low:
                cats.add("ID/foreign matter/LoD")
        notes_parts.append("Missing: " + ", ".join(sorted(cats)) if cats else "Coverage gap noted")
    if flags:
        notes_parts.append("Data-integrity flag on: " + ", ".join(sorted(set(flags))))
    if stability_count:
        notes_parts.append("%d stability-study results — see 'Stability Studies' sheet" % stability_count)

    return identity, status, out, " ; ".join(notes_parts)


# ------------------------------------------------------------ workbook ----
wb = openpyxl.Workbook()

# ---- styles ----
hdr_font = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
hdr_fill = PatternFill("solid", fgColor="1F4E78")
sub_font = Font(name=FONT_NAME, size=9, italic=True, color="595959")
sub_fill = PatternFill("solid", fgColor="F2F2F2")
base_font = Font(name=FONT_NAME, size=10)
bold_font = Font(name=FONT_NAME, size=10, bold=True)
link_font = Font(name=FONT_NAME, size=9, color="0563C1", underline="single")
title_font = Font(name=FONT_NAME, size=16, bold=True, color="1F4E78")
legend_font = Font(name=FONT_NAME, size=9, italic=True)

GREEN = PatternFill("solid", fgColor="C6EFCE")
GREEN_TXT = Font(name=FONT_NAME, size=10, color="006100")
AMBER = PatternFill("solid", fgColor="FFEB9C")
AMBER_TXT = Font(name=FONT_NAME, size=10, color="9C6500")
RED = PatternFill("solid", fgColor="FFC7CE")
RED_TXT = Font(name=FONT_NAME, size=10, bold=True, color="9C0006")
GRAY = PatternFill("solid", fgColor="F2F2F2")
GRAY_TXT = Font(name=FONT_NAME, size=10, color="808080", italic=True)

thin = Side(style="thin", color="D9D9D9")
box = Border(left=thin, right=thin, top=thin, bottom=thin)

STATUS_STYLE = {
    "COMPLETE": ("\U0001F7E2 Complete", GREEN, GREEN_TXT),
    "COMPLETE (flag noted)": ("\U0001F7E2 Complete (flag)", GREEN, AMBER_TXT),
    "PARTIAL": ("\U0001F7E1 Partial", AMBER, AMBER_TXT),
    "OPEN QC ISSUE": ("\U0001F534 OPEN QC ISSUE", RED, RED_TXT),
}


def result_fill_font(value):
    if value == "—":
        return GRAY, GRAY_TXT
    low = value.lower()
    if "does not conform" in low or "nonconform" in low or "не одговара" in low or "detected:" in low:
        return RED, RED_TXT
    if "data integrity flag" in low:
        return AMBER, AMBER_TXT
    return None, base_font


# =========================================================== SHEET 1 ======
ws1 = wb.active
ws1.title = "Batch Summary"

ws1.sheet_view.showGridLines = False

# --- title block ---
ws1.merge_cells("A1:F1")
ws1["A1"] = "Purely Plant GmbH — eCoA Master Database"
ws1["A1"].font = title_font
ws1.merge_cells("A2:F2")
ws1["A2"] = "Chronological batch-level QC summary — outsourced laboratory certificates (Farmahem, UKIM Faculty of Pharmacy, IPH)"
ws1["A2"].font = Font(name=FONT_NAME, size=10, italic=True, color="595959")
ws1.merge_cells("A3:F3")
ws1["A3"] = "Generated 2026-08-10 from ImB_QC_COAs RAG + Drive folder 16oMK_j0FUusjveV61B5rxWi6Sl5kQsn5 — 80 batches, 2339 verified parameter records"
ws1["A3"].font = Font(name=FONT_NAME, size=9, italic=True, color="808080")

# --- summary dashboard (counts via COUNTIF against the Status column further down) ---
DASH_ROW = 5
ws1["A%d" % DASH_ROW] = "Total batches"
ws1["B%d" % DASH_ROW] = 80
ws1["C%d" % DASH_ROW] = "\U0001F7E2 Complete"
ws1["D%d" % DASH_ROW] = None  # filled with formula after table written
ws1["E%d" % DASH_ROW] = "\U0001F7E1 Partial"
ws1["F%d" % DASH_ROW] = None
ws1["G%d" % DASH_ROW] = "\U0001F534 Open issue"
ws1["H%d" % DASH_ROW] = None
for c in ("A", "C", "E", "G"):
    ws1["%s%d" % (c, DASH_ROW)].font = bold_font
for c in ("B", "D", "F", "H"):
    ws1["%s%d" % (c, DASH_ROW)].font = Font(name=FONT_NAME, size=12, bold=True)

# --- legend ---
LEG_ROW = 7
ws1["A%d" % LEG_ROW] = "Legend:"
ws1["A%d" % LEG_ROW].font = bold_font
legend_items = [
    ("\U0001F7E2 Complete", GREEN, "All core Ph.Eur. 3028 parameters on file, all within spec"),
    ("\U0001F7E1 Partial", AMBER, "One or more parameter categories have no certificate on file"),
    ("\U0001F534 OPEN QC ISSUE", RED, "Unresolved non-conformance or discrepancy — see Notes"),
    ("— (gray)", GRAY, "No data available for this parameter"),
]
lc = 1
for label, fill, desc in legend_items:
    cell = ws1.cell(row=LEG_ROW + 1, column=lc, value=label)
    cell.fill = fill
    cell.font = Font(name=FONT_NAME, size=9, bold=True)
    cell.alignment = Alignment(horizontal="center")
    ws1.merge_cells(start_row=LEG_ROW + 2, start_column=lc, end_row=LEG_ROW + 2, end_column=lc + 1)
    dcell = ws1.cell(row=LEG_ROW + 2, column=lc, value=desc)
    dcell.font = legend_font
    dcell.alignment = Alignment(wrap_text=True, vertical="top")
    lc += 3
ws1.row_dimensions[LEG_ROW + 2].height = 28

TABLE_HDR_ROW = LEG_ROW + 5  # header row for the batch table

# --- table headers ---
id_cols = ["Seq", "Status", "Cultivation Batch", "P-Number", "Strain", "Row"]
val_cols = list(COLS.values())
all_headers = id_cols + val_cols + ["Notes"]

for ci, htext in enumerate(all_headers, start=1):
    c = ws1.cell(row=TABLE_HDR_ROW, column=ci, value=htext)
    c.font = hdr_font
    c.fill = hdr_fill
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = box

ws1.freeze_panes = ws1.cell(row=TABLE_HDR_ROW + 1, column=7).coordinate  # freeze header + id columns
ws1.row_dimensions[TABLE_HDR_ROW].height = 30

# column widths
widths = {1: 5, 2: 16, 3: 20, 4: 11, 5: 16, 6: 9}
for i, w in widths.items():
    ws1.column_dimensions[get_column_letter(i)].width = w
for i in range(len(id_cols) + 1, len(id_cols) + len(val_cols) + 1):
    ws1.column_dimensions[get_column_letter(i)].width = 22
ws1.column_dimensions[get_column_letter(len(all_headers))].width = 40

r_ptr = TABLE_HDR_ROW + 1
for seq in seqs:
    identity, status, vals, notes = batch_pivot(seq)
    label, fill, font = STATUS_STYLE[status]

    # -------- results row --------
    res_row = r_ptr
    ws1.cell(row=res_row, column=1, value=identity["seq"]).font = bold_font
    scell = ws1.cell(row=res_row, column=2, value=label)
    scell.fill = fill
    scell.font = font
    scell.alignment = Alignment(horizontal="center")
    ws1.cell(row=res_row, column=3, value=identity["cultivation_batch"]).font = bold_font
    ws1.cell(row=res_row, column=4, value=identity["p_number"]).font = base_font
    ws1.cell(row=res_row, column=5, value=identity["strain"]).font = base_font
    rc = ws1.cell(row=res_row, column=6, value="Result")
    rc.font = sub_font

    for j, key in enumerate(COLS):
        col = len(id_cols) + 1 + j
        v = vals[key]["value"]
        cell = ws1.cell(row=res_row, column=col, value=v)
        cell.font = base_font
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.border = box
        rf, rfnt = result_fill_font(v)
        if rf:
            cell.fill = rf
            cell.font = rfnt
        elif v == "—":
            cell.fill = GRAY
            cell.font = GRAY_TXT

    ncell = ws1.cell(row=res_row, column=len(all_headers), value=notes or "")
    ncell.font = Font(name=FONT_NAME, size=9, italic=bool(notes), color="9C0006" if "OPEN" in status else "595959")
    ncell.alignment = Alignment(wrap_text=True, vertical="top")

    # -------- sources row --------
    src_row = r_ptr + 1
    ws1.cell(row=src_row, column=6, value="Source").font = sub_font
    for c in range(1, 6):
        ws1.cell(row=src_row, column=c).fill = sub_fill
    ws1.cell(row=src_row, column=6).fill = sub_fill

    for j, key in enumerate(COLS):
        col = len(id_cols) + 1 + j
        src = vals[key]["source"]
        link = vals[key]["link"]
        cell = ws1.cell(row=src_row, column=col, value=src or "")
        cell.font = link_font if link else sub_font
        cell.fill = sub_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.border = box
        if link:
            cell.hyperlink = link
    ws1.cell(row=src_row, column=len(all_headers)).fill = sub_fill

    for c in range(1, len(all_headers) + 1):
        ws1.cell(row=res_row, column=c).border = box
        ws1.cell(row=src_row, column=c).border = box

    r_ptr += 2

LAST_ROW = r_ptr - 1
ws1.auto_filter.ref = "A%d:%s%d" % (TABLE_HDR_ROW, get_column_letter(len(all_headers)), LAST_ROW)

# dashboard formulas (COUNTIF over Status column B, results rows only -> every other row from TABLE_HDR_ROW+1)
status_range = "B%d:B%d" % (TABLE_HDR_ROW + 1, LAST_ROW)
ws1["D%d" % DASH_ROW] = '=COUNTIF(%s,"*Complete*")' % status_range
ws1["F%d" % DASH_ROW] = '=COUNTIF(%s,"*Partial*")' % status_range
ws1["H%d" % DASH_ROW] = '=COUNTIF(%s,"*OPEN*")' % status_range

# ---- pie chart of status counts ----
# NOTE: chart source cells must sit BELOW the batch table; placing them at a fixed
# offset from the dashboard silently overwrote batch rows in an earlier build.
chart_data_row = LAST_ROW + 3
ws1.cell(row=chart_data_row, column=1, value="Status").font = Font(name=FONT_NAME, size=8)
ws1.cell(row=chart_data_row, column=2, value="Count").font = Font(name=FONT_NAME, size=8)
ws1.cell(row=chart_data_row + 1, column=1, value="Complete")
ws1.cell(row=chart_data_row + 1, column=2).value = "=D%d" % DASH_ROW
ws1.cell(row=chart_data_row + 2, column=1, value="Partial")
ws1.cell(row=chart_data_row + 2, column=2).value = "=F%d" % DASH_ROW
ws1.cell(row=chart_data_row + 3, column=1, value="Open Issue")
ws1.cell(row=chart_data_row + 3, column=2).value = "=H%d" % DASH_ROW

pie = PieChart()
pie.title = "Batch QC Status"
data = Reference(ws1, min_col=2, min_row=chart_data_row, max_row=chart_data_row + 3)
cats = Reference(ws1, min_col=1, min_row=chart_data_row + 1, max_row=chart_data_row + 3)
pie.add_data(data, titles_from_data=True)
pie.set_categories(cats)
pie.height = 6
pie.width = 9
ws1.add_chart(pie, "J5")

# =========================================================== SHEET 2 ======
ws2 = wb.create_sheet("Audit Trail")
ws2.sheet_view.showGridLines = False

headers2 = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter", "Acceptance Criterion",
            "Result", "Certificate Code", "Issue Date", "Issuing Institution", "Drive File Link"]
for ci, h in enumerate(headers2, start=1):
    c = ws2.cell(row=1, column=ci, value=h)
    c.font = hdr_font
    c.fill = hdr_fill
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws2.row_dimensions[1].height = 22
ws2.freeze_panes = "A2"

col_widths2 = [6, 18, 10, 16, 42, 26, 30, 20, 22, 34, 14]
for i, w in enumerate(col_widths2, start=1):
    ws2.column_dimensions[get_column_letter(i)].width = w

for ri, r in enumerate(rows, start=2):
    ws2.cell(row=ri, column=1, value=r["Seq"]).font = base_font
    ws2.cell(row=ri, column=2, value=r["Cultivation Batch"]).font = base_font
    ws2.cell(row=ri, column=3, value=r["P-Number"]).font = base_font
    ws2.cell(row=ri, column=4, value=r["Strain"]).font = base_font
    pcell = ws2.cell(row=ri, column=5, value=r["Parameter"])
    pcell.font = bold_font if r["Parameter"].startswith("[") else base_font
    pcell.alignment = Alignment(wrap_text=True, vertical="top")
    accell = ws2.cell(row=ri, column=6, value=r["Acceptance Criterion"])
    accell.font = base_font
    accell.alignment = Alignment(wrap_text=True, vertical="top")
    rescell = ws2.cell(row=ri, column=7, value=r["Result"])
    rescell.alignment = Alignment(wrap_text=True, vertical="top")
    rf, rfnt = result_fill_font(r["Result"])
    if rf:
        rescell.fill = rf
        rescell.font = rfnt
    else:
        rescell.font = base_font
    ws2.cell(row=ri, column=8, value=r["Certificate Code"]).font = base_font
    ws2.cell(row=ri, column=9, value=r["Issue Date"]).font = base_font
    ws2.cell(row=ri, column=10, value=r["Issuing Institution"]).font = base_font
    link = r["Drive File Link"].strip()
    lcell = ws2.cell(row=ri, column=11, value="Open" if link else "")
    if link:
        lcell.hyperlink = link.split(" (folder")[0].strip()
        lcell.font = link_font
        lcell.alignment = Alignment(horizontal="center")

ws2.auto_filter.ref = "A1:K%d" % (len(rows) + 1)

# =========================================================== SHEET 3 ======
# Stability studies kept separate from release disposition: same batch, different
# storage condition and timepoint, so these must not be read as release results.
stab_rows = [r for r in rows if STABILITY_RE.search(r["Parameter"])]

ws3 = wb.create_sheet("Stability Studies")
ws3.sheet_view.showGridLines = False
ws3.merge_cells("A1:E1")
ws3["A1"] = "ICH Stability Study Results — held separate from batch-release disposition"
ws3["A1"].font = title_font
ws3.merge_cells("A2:H2")
ws3["A2"] = ("These are the same batches re-tested after storage (month 3 / 6 / 9 at 25°C/60%RH and 40°C/75%RH). "
             "They are NOT release results and must not be substituted for the release certificate values on the Batch Summary sheet.")
ws3["A2"].font = Font(name=FONT_NAME, size=9, italic=True, color="9C6500")
ws3["A2"].alignment = Alignment(wrap_text=True)
ws3.row_dimensions[2].height = 26

for ci, h in enumerate(headers2, start=1):
    c = ws3.cell(row=4, column=ci, value=h)
    c.font = hdr_font
    c.fill = hdr_fill
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws3.freeze_panes = "A5"
for i, w in enumerate(col_widths2, start=1):
    ws3.column_dimensions[get_column_letter(i)].width = w

for ri, r in enumerate(stab_rows, start=5):
    ws3.cell(row=ri, column=1, value=r["Seq"]).font = base_font
    ws3.cell(row=ri, column=2, value=r["Cultivation Batch"]).font = base_font
    ws3.cell(row=ri, column=3, value=r["P-Number"]).font = base_font
    ws3.cell(row=ri, column=4, value=r["Strain"]).font = base_font
    pc = ws3.cell(row=ri, column=5, value=r["Parameter"])
    pc.font = base_font
    pc.alignment = Alignment(wrap_text=True, vertical="top")
    ac = ws3.cell(row=ri, column=6, value=r["Acceptance Criterion"])
    ac.font = base_font
    ac.alignment = Alignment(wrap_text=True, vertical="top")
    rc2 = ws3.cell(row=ri, column=7, value=r["Result"])
    rc2.alignment = Alignment(wrap_text=True, vertical="top")
    rf, rfnt = result_fill_font(r["Result"])
    if rf:
        rc2.fill = rf
        rc2.font = rfnt
    else:
        rc2.font = base_font
    ws3.cell(row=ri, column=8, value=r["Certificate Code"]).font = base_font
    ws3.cell(row=ri, column=9, value=r["Issue Date"]).font = base_font
    ws3.cell(row=ri, column=10, value=r["Issuing Institution"]).font = base_font
    link = r["Drive File Link"].strip()
    lc2 = ws3.cell(row=ri, column=11, value="Open" if link else "")
    if link:
        lc2.hyperlink = link.split(" (folder")[0].strip()
        lc2.font = link_font
        lc2.alignment = Alignment(horizontal="center")

if stab_rows:
    ws3.auto_filter.ref = "A4:K%d" % (len(stab_rows) + 4)

wb.save(OUT)
print("Sheet3 (stability) rows:", len(stab_rows))
print("Saved:", OUT)
print("Sheet1 rows written:", LAST_ROW - TABLE_HDR_ROW, "(", (LAST_ROW - TABLE_HDR_ROW)//2, "batches )")
print("Sheet2 rows written:", len(rows))
