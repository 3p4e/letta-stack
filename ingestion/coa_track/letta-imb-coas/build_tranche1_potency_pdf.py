#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche 1 potency, per strain and per batch, as a PDF.

Answers one question and shows its working: does every Tranche 1 batch have a Total
Δ9-THC result, and which certificate is each result on.

Every figure is a transcription. Where a batch was assayed twice — the original release
certificate and a later Farmahem 197-series retest — both are shown side by side rather
than averaged or reconciled, because they are two measurements of two samples and choosing
between them would destroy that. The released figure from the Tranches Overview sits
beside them so any divergence is visible rather than buried.

Formatting follows the house rules: the value alone in its cell, the unit in the column
heading, and measurement uncertainty left out of the result entirely.

DejaVu is embedded rather than using a built-in font because the certificate numbers are
Cyrillic (ППК, НИК) and the PDF base-14 fonts have no glyphs for them — they would render
as empty boxes, which is worse than useless on a document whose whole purpose is to name
certificates precisely.
"""
import os
import sys
from collections import defaultdict

import coa_pivot as cp
import crosscheck_sources as cc
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "exports", "PP_Tranche1_Potency.pdf")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
NAVY = colors.HexColor("#1F3864")
BAND = colors.HexColor("#EEF2F8")
LINE = colors.HexColor("#B4C6E7")
GREY = colors.HexColor("#555555")


def main():
    pdfmetrics.registerFont(TTFont("DJ", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DJB", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

    body = ParagraphStyle("body", fontName="DJ", fontSize=7.6, leading=9.4,
                          alignment=TA_LEFT)
    small = ParagraphStyle("small", parent=body, fontSize=6.8, leading=8.4,
                           textColor=GREY)
    head = ParagraphStyle("head", fontName="DJB", fontSize=7.4, leading=9,
                          textColor=colors.white)
    title = ParagraphStyle("title", fontName="DJB", fontSize=15, leading=18,
                           textColor=NAVY, spaceAfter=2)
    sub = ParagraphStyle("sub", parent=body, fontSize=8, leading=10.5,
                         textColor=GREY, spaceAfter=8)
    sect = ParagraphStyle("sect", fontName="DJB", fontSize=10, leading=12,
                          textColor=NAVY, spaceBefore=9, spaceAfter=3)

    rows, batches = cp.build()
    by_seq = cp.group_by_seq(rows)
    tr = {cc.norm_batch(r["batch"]): r for r in cc.read_tsv("tranches_overview.tsv")}

    per_strain = defaultdict(list)
    total = covered = retested = 0
    for b in batches:
        sheet = tr.get(cc.norm_batch(b["batch"]))
        if not sheet or (sheet.get("tranche") or "").strip() != "1":
            continue
        total += 1
        results = []
        for r in by_seq[b["seq"]]:
            if cp.classify(r["Parameter"]) != "thc":
                continue
            if cp.STABILITY_RE.search(r["Parameter"] or ""):
                continue
            v = cc.num(r["Result"].split("(")[0])
            if v is None:
                continue
            code = (r["Certificate Code"] or "").strip()
            if code.lower().startswith("n/a"):
                code = "Purely Plant in-house CoA — no number printed"
            results.append((v, code, cp.issue_date(r["Issue Date"])))
        if results:
            covered += 1
        if len(results) > 1:
            retested += 1
        per_strain[(b["strain"] or "").strip()].append({
            "batch": b["batch"], "p": (b["p_number"] or "").strip(),
            "released": (sheet.get("thc_pct") or "").strip(), "results": results,
        })

    story = [Paragraph("Purely Plant — Tranche 1 Potency", title),
             Paragraph("Total Δ9-THC by strain and batch, with the certificate every "
                       "result was transcribed from. Values are % w/w. Measurement "
                       "uncertainty is excluded; stability timepoints are excluded.", sub)]

    summary = Table([[Paragraph(
        "<b>%d of %d Tranche 1 batches carry a Total Δ9-THC result</b>, across %d "
        "strains. %d of them were assayed twice — the original release certificate and a "
        "later Farmahem 197-series retest. Both figures are shown; they are separate "
        "measurements of separate samples and are not reconciled here."
        % (covered, total, len(per_strain), retested), body)]],
        colWidths=[180 * mm])
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("BOX", (0, 0), (-1, -1), 0.7, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [summary, Spacer(1, 4)]

    widths = [26 * mm, 20 * mm, 20 * mm, 18 * mm, 74 * mm, 22 * mm]
    for strain in sorted(per_strain, key=lambda s: s.lower()):
        entries = sorted(per_strain[strain], key=lambda e: e["batch"])
        data = [[Paragraph(t, head) for t in
                 ("Batch", "P-Number", "Released<br/>% w/w", "Result<br/>% w/w",
                  "Certificate", "Issued")]]
        spans, r = [], 1
        for e in entries:
            res = e["results"] or [(None, "no Total Δ9-THC result on file", "")]
            for j, (v, code, date) in enumerate(res):
                data.append([
                    Paragraph("<b>%s</b>" % e["batch"], body) if j == 0 else "",
                    Paragraph(e["p"] or "—", body) if j == 0 else "",
                    Paragraph(e["released"] or "—", body) if j == 0 else "",
                    Paragraph("%.2f" % v if v is not None else "—", body),
                    Paragraph(code, small), Paragraph(date or "—", small)])
            if len(res) > 1:
                spans += [("SPAN", (c, r), (c, r + len(res) - 1)) for c in (0, 1, 2)]
            r += len(res)

        t = Table(data, colWidths=widths, repeatRows=1)
        style = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                 ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("ALIGN", (2, 1), (3, -1), "RIGHT"),
                 ("LEFTPADDING", (0, 0), (-1, -1), 4),
                 ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                 ("TOPPADDING", (0, 0), (-1, -1), 3),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 3)] + spans
        t.setStyle(TableStyle(style))
        story.append(KeepTogether([
            Paragraph("%s &nbsp;<font size=7 color='#777777'>(%d batch%s)</font>"
                      % (strain, len(entries), "" if len(entries) == 1 else "es"), sect),
            t]))

    story += [Spacer(1, 6), Paragraph(
        "Released % w/w is the figure carried on the Tranches Overview control sheet. "
        "Where it differs from every certificate the difference is shown rather than "
        "resolved: the certificate is the measurement, the sheet is a control record.",
        small)]

    doc = SimpleDocTemplate(PDF, pagesize=A4, title="Purely Plant — Tranche 1 Potency",
                            author="Purely Plant QC", leftMargin=15 * mm,
                            rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    doc.build(story)

    print("Wrote %s (%d bytes)" % (PDF, os.path.getsize(PDF)))
    print("tranche 1: %d batches, %d with potency, %d strains, %d retested"
          % (total, covered, len(per_strain), retested))
    return 0


if __name__ == "__main__":
    sys.exit(main())
