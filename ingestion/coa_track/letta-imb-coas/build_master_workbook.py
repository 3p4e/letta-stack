#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the master eCoA workbook.

Sheets
  Batch Summary     one row per batch, release-critical reads, colour-coded status
  Audit Trail       every parameter record, one row each, with its certificate
  Stability Studies ICH storage results, kept away from release disposition

A previous version put a second "sources" row under every batch across 24 columns; the
citations made those rows fifteen lines tall and every column too narrow to read. Provenance
now lives on the Audit Trail sheet, where each parameter has a full row to itself.

Usage:  python3 build_master_workbook.py [input.tsv] [output.xlsx]
"""
import os
import sys

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import coa_pivot as cp

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "exports", "PP_eCoA_Master_Database.xlsx")
FONT = "Arial"

# Release-critical reads for the summary sheet. The full parameter set is on Audit Trail;
# a summary that repeats all 24 buckets is unreadable at any column width.
SUMMARY_COLS = [
    ("identification", "Identification", 18),
    ("foreign_matter", "Foreign matter", 18),
    ("loss_on_drying", "Loss on drying", 15),
    ("thc", "Total Δ9-THC", 22),
    ("cbd", "Total CBD", 18),
    ("cbn", "Total CBN", 16),
    ("aflatoxins", "Aflatoxins", 20),
    ("ochratoxin", "Ochratoxin A", 15),
    ("pb", "Lead", 13), ("cd", "Cadmium", 13), ("as_", "Arsenic", 13), ("hg", "Mercury", 13),
    ("pesticides", "Pesticide screen", 26),
    ("tamc", "TAMC", 15), ("tymc", "TYMC", 15), ("bile", "Bile-tol. GNB", 15),
    ("ecoli", "E. coli", 14), ("salmonella", "Salmonella", 14),
]

STATUS_TEXT = {"complete": "Complete", "flag": "Complete (flag)",
               "partial": "Partial", "open": "OPEN QC ISSUE"}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    rows, batches = cp.build(src)

    wb = openpyxl.Workbook()

    hdr_font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="16232B")
    base = Font(name=FONT, size=10)
    bold = Font(name=FONT, size=10, bold=True)
    small = Font(name=FONT, size=9, color="5A6E75")
    link_font = Font(name=FONT, size=9, color="0E6E6E", underline="single")
    title_font = Font(name=FONT, size=15, bold=True, color="16232B")

    GREEN, GREEN_T = PatternFill("solid", fgColor="E3F3E9"), Font(name=FONT, size=10, color="1B7F4B", bold=True)
    AMBER, AMBER_T = PatternFill("solid", fgColor="FAEDD4"), Font(name=FONT, size=10, color="9A6300", bold=True)
    RED, RED_T = PatternFill("solid", fgColor="F9DEDB"), Font(name=FONT, size=10, color="AE2318", bold=True)
    GREY_T = Font(name=FONT, size=10, color="8B9EA3")

    thin = Side(style="thin", color="DBE3E1")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)

    status_style = {"complete": (GREEN, GREEN_T), "flag": (GREEN, AMBER_T),
                    "partial": (AMBER, AMBER_T), "open": (RED, RED_T)}

    # ------------------------------------------------ Sheet 1: Batch Summary
    ws = wb.active
    ws.title = "Batch Summary"
    ws.sheet_view.showGridLines = False

    ws["A1"] = "Purely Plant GmbH — eCoA Master Database"
    ws["A1"].font = title_font
    ws["A2"] = ("One row per tested batch, release-critical parameters. "
                "Full parameter detail and certificate links on the Audit Trail sheet.")
    ws["A2"].font = small
    ws["A3"] = ("%d batches · %d parameter records · %d accredited laboratories · "
                "values transcribed verbatim, pass/fail never derived from a value"
                % (len(batches), len(rows), cp.count_labs(rows)))
    ws["A3"].font = Font(name=FONT, size=9, color="8B9EA3")

    HDR = 5
    headers = ["Seq", "Status", "Cultivation batch", "P-number", "Strain"] + \
              [lbl for _, lbl, _ in SUMMARY_COLS] + ["Notes"]
    for ci, h in enumerate(headers, start=1):
        c = ws.cell(row=HDR, column=ci, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c.border = box
    ws.row_dimensions[HDR].height = 28
    ws.freeze_panes = ws.cell(row=HDR + 1, column=6).coordinate

    for i, w in enumerate([6, 16, 22, 12, 20], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for j, (_k, _lbl, width) in enumerate(SUMMARY_COLS):
        ws.column_dimensions[get_column_letter(6 + j)].width = width
    ws.column_dimensions[get_column_letter(len(headers))].width = 52

    r = HDR + 1
    for b in batches:
        fill, fnt = status_style[b["status"]]
        ws.cell(row=r, column=1, value=b["seq"]).font = base
        sc = ws.cell(row=r, column=2, value=STATUS_TEXT[b["status"]])
        sc.fill, sc.font = fill, fnt
        ws.cell(row=r, column=3, value=b["batch"]).font = bold
        ws.cell(row=r, column=4, value=b["p_number"]).font = base
        ws.cell(row=r, column=5, value=b["strain"]).font = base
        for j, (key, _lbl, _w) in enumerate(SUMMARY_COLS):
            v = b["vals"][key]["value"]
            cell = ws.cell(row=r, column=6 + j, value=v)
            cell.alignment = Alignment(vertical="top", wrap_text=False)
            sev = cp.severity(v)
            if sev == "crit":
                cell.fill, cell.font = RED, RED_T
            elif sev == "warn":
                cell.fill, cell.font = AMBER, AMBER_T
            elif sev == "na":
                cell.font = GREY_T
            else:
                cell.font = base
        nc = ws.cell(row=r, column=len(headers), value=b["notes"])
        nc.font = Font(name=FONT, size=9, color="AE2318" if b["status"] == "open" else "5A6E75")
        nc.alignment = Alignment(vertical="top", wrap_text=False)
        for c in range(1, len(headers) + 1):
            ws.cell(row=r, column=c).border = box
        r += 1
    LAST = r - 1
    ws.auto_filter.ref = "A%d:%s%d" % (HDR, get_column_letter(len(headers)), LAST)

    # ------------------------------------------------ Sheet 2: Audit Trail
    ws2 = wb.create_sheet("Audit Trail")
    ws2.sheet_view.showGridLines = False
    head2 = ["Seq", "Cultivation batch", "P-number", "Strain", "Parameter",
             "Acceptance criterion", "Result", "Certificate code", "Issue date",
             "Issuing institution", "Certificate"]
    widths2 = [6, 18, 11, 18, 46, 30, 34, 20, 24, 38, 12]
    for ci, h in enumerate(head2, start=1):
        c = ws2.cell(row=1, column=ci, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws2.row_dimensions[1].height = 26
    ws2.freeze_panes = "E2"
    for i, w in enumerate(widths2, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    for ri, rec in enumerate(rows, start=2):
        ws2.cell(row=ri, column=1, value=rec["Seq"]).font = base
        ws2.cell(row=ri, column=2, value=rec["Cultivation Batch"]).font = base
        ws2.cell(row=ri, column=3, value=rec["P-Number"]).font = base
        ws2.cell(row=ri, column=4, value=rec["Strain"]).font = base
        pc = ws2.cell(row=ri, column=5, value=rec["Parameter"])
        pc.font = base
        pc.alignment = Alignment(vertical="top", wrap_text=True)
        ac = ws2.cell(row=ri, column=6, value=rec["Acceptance Criterion"])
        ac.font = small
        ac.alignment = Alignment(vertical="top", wrap_text=True)
        rc = ws2.cell(row=ri, column=7, value=rec["Result"])
        rc.alignment = Alignment(vertical="top", wrap_text=True)
        sev = cp.severity(rec["Result"])
        if sev == "crit":
            rc.fill, rc.font = RED, RED_T
        elif sev == "warn":
            rc.fill, rc.font = AMBER, AMBER_T
        else:
            rc.font = base
        ws2.cell(row=ri, column=8, value=rec["Certificate Code"]).font = base
        ws2.cell(row=ri, column=9, value=rec["Issue Date"]).font = base
        ws2.cell(row=ri, column=10, value=rec["Issuing Institution"]).font = small
        link = cp.clean_link(rec["Drive File Link"])
        lc = ws2.cell(row=ri, column=11, value="Open PDF" if link else "")
        if link:
            lc.hyperlink = link
            lc.font = link_font
    ws2.auto_filter.ref = "A1:K%d" % (len(rows) + 1)

    # ------------------------------------------------ Sheet 3: Stability
    stab = [x for x in rows if cp.STABILITY_RE.search(x["Parameter"])]
    ws3 = wb.create_sheet("Stability Studies")
    ws3.sheet_view.showGridLines = False
    ws3["A1"] = "ICH stability results — not release disposition"
    ws3["A1"].font = title_font
    ws3["A2"] = ("Same batches re-tested after storage (month 3 / 6 / 9 at 25 °C/60 % RH and "
                 "40 °C/75 % RH). These must never be substituted for release values.")
    ws3["A2"].font = Font(name=FONT, size=9, color="9A6300")
    for ci, h in enumerate(head2, start=1):
        c = ws3.cell(row=4, column=ci, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws3.freeze_panes = "A5"
    for i, w in enumerate(widths2, start=1):
        ws3.column_dimensions[get_column_letter(i)].width = w
    for ri, rec in enumerate(stab, start=5):
        ws3.cell(row=ri, column=1, value=rec["Seq"]).font = base
        ws3.cell(row=ri, column=2, value=rec["Cultivation Batch"]).font = base
        ws3.cell(row=ri, column=3, value=rec["P-Number"]).font = base
        ws3.cell(row=ri, column=4, value=rec["Strain"]).font = base
        pc = ws3.cell(row=ri, column=5, value=rec["Parameter"])
        pc.font = base
        pc.alignment = Alignment(vertical="top", wrap_text=True)
        ac = ws3.cell(row=ri, column=6, value=rec["Acceptance Criterion"])
        ac.font = small
        ac.alignment = Alignment(vertical="top", wrap_text=True)
        rc = ws3.cell(row=ri, column=7, value=rec["Result"])
        rc.alignment = Alignment(vertical="top", wrap_text=True)
        sev = cp.severity(rec["Result"])
        if sev == "crit":
            rc.fill, rc.font = RED, RED_T
        elif sev == "warn":
            rc.fill, rc.font = AMBER, AMBER_T
        else:
            rc.font = base
        ws3.cell(row=ri, column=8, value=rec["Certificate Code"]).font = base
        ws3.cell(row=ri, column=9, value=rec["Issue Date"]).font = base
        ws3.cell(row=ri, column=10, value=rec["Issuing Institution"]).font = small
        link = cp.clean_link(rec["Drive File Link"])
        lc = ws3.cell(row=ri, column=11, value="Open PDF" if link else "")
        if link:
            lc.hyperlink = link
            lc.font = link_font
    if stab:
        ws3.auto_filter.ref = "A4:K%d" % (len(stab) + 4)

    # ------------------------------------------------ Sheet 4: Legend
    ws4 = wb.create_sheet("Legend")
    ws4.sheet_view.showGridLines = False
    ws4["A1"] = "How to read this workbook"
    ws4["A1"].font = title_font
    ws4.column_dimensions["A"].width = 26
    ws4.column_dimensions["B"].width = 96
    guide = [
        ("Batch Summary", "One row per batch. Release-critical parameters only, so every column stays readable."),
        ("Audit Trail", "Every parameter record with its acceptance criterion, result, certificate and link."),
        ("Stability Studies", "Storage-condition results. Never a substitute for release values."),
        ("", ""),
        ("Complete", "All core Ph. Eur. 3028 parameters on file and within specification."),
        ("Complete (flag)", "Within specification, but a certificate carries a data-integrity flag."),
        ("Partial", "A parameter category has no certificate on file for this batch."),
        ("OPEN QC ISSUE", "Unresolved non-conformance declared by the issuing laboratory."),
        ("Empty cell / —", "No result recorded for that parameter."),
        ("", ""),
        ("Verbatim values", "N.D., <LOQ, BLQ and Одговара / Не одговара appear exactly as printed."),
        ("No derived verdicts", "A result is marked a finding only where the issuing laboratory says so."),
        ("Added criteria", "Where a lab prints no limit column, the PP release spec / Ph. Eur. 3028 limit "
                           "is shown and marked as added for review."),
    ]
    rr = 3
    for k, v in guide:
        ws4.cell(row=rr, column=1, value=k).font = bold if k else base
        c = ws4.cell(row=rr, column=2, value=v)
        c.font = base
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if k in status_style_keys():
            f, t = status_style[status_key(k)]
            ws4.cell(row=rr, column=1).fill = f
            ws4.cell(row=rr, column=1).font = t
        rr += 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wb.save(out_path)
    print("Wrote %s" % out_path)
    print("Batch Summary rows: %d | Audit Trail rows: %d | Stability rows: %d"
          % (len(batches), len(rows), len(stab)))


def status_style_keys():
    return {"Complete", "Complete (flag)", "Partial", "OPEN QC ISSUE"}


def status_key(label):
    return {"Complete": "complete", "Complete (flag)": "flag",
            "Partial": "partial", "OPEN QC ISSUE": "open"}[label]


if __name__ == "__main__":
    main()
