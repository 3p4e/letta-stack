#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The ImB potency specifications PP-QC-SPEC-001 v5.5 does not yet carry.

That document is the Tranche 1 update: 13 strains, 21 batches, 46 certificate results.
The register holds 20 strains, so seven have no specification ladder at all — every one of
them a strain whose batches sit in Tranche 2 or 3 and which the Tranche 1 pass therefore
never reached.

    Apple and Banana   AB    1 batch    16.93
    Clemosa a bud      CLE   1 batch     8.02
    Graps & Creme      GRC   1 batch    11.53
    Kush Crasher       KC    1 batch    17.04
    Motor Breath       MB    2 batches  16.82 – 18.67
    Sleepy Joy         SJ    3 batches   9.20 – 11.20
    Wedding Crasher    WC    2 batches  21.67 – 22.11

The ladders below follow v5.5's own conventions exactly, so the two documents compose:

  * contiguous bands, top of Spec I fixed at 30.00 %, lower limit inclusive and upper
    exclusive;
  * product code {ABBR}-THC{nominal}:CBD1, nominal in two-decimal format;
  * a quarter-range buffer under the lowest observed result wherever it is attainable,
    and an explicit flag where it is not;
  * CBD acceptance criterion < 1.0 % throughout;
  * PROVISIONAL on any strain with fewer than three batches of history.

Band placement is arithmetic, not judgement: each ladder is chosen so every certificate
result for that strain falls inside a band with the buffer intact, and the margins are
printed so the choice can be checked rather than trusted. Sleepy Joy is the one strain
where an evenly-spaced 5.00 ladder would have split three results across two bands with
sub-buffer margins, so its ladder is spaced to hold all three in one band — the reasoning
is stated on the strain.

Nothing here is a released specification. These are proposals derived from the potency
history and they need QC approval before they govern anything.
"""
import os
import sys
from collections import defaultdict

import coa_pivot as cp
import crosscheck_sources as cc
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "exports", "PP_ImB_Specs_Remaining.html")
PDF = os.path.join(HERE, "exports", "PP_ImB_Specs_Remaining.pdf")
FONTS = "/usr/share/fonts/truetype/dejavu"

DOC = "PP-QC-SPEC-001 v5.6 (remaining strains)"
ISSUED = "11.08.2026"

# strain -> (abbr, provisional, ladder, rationale)
# ladder: list of (roman, nominal, low, high) top-first; high of the first is 30.00
LADDERS = {
    "Apple and Banana": ("AB", True, [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], ""),
    "Clemosa a bud": ("CLE", True, [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00), ("IV", 12.50, 10.00, 15.00),
        ("V", 7.50, 5.00, 10.00)],
        "Five bands are needed to reach 8.02 %. A four-band ladder floored at 7.00 % "
        "would leave only 1.02 % under the result, short of the quarter-range buffer."),
    "Graps & Creme": ("GRC", True, [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00), ("IV", 12.50, 10.00, 15.00)], ""),
    "Kush Crasher": ("KC", True, [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], ""),
    "Motor Breath": ("MB", True, [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], ""),
    "Sleepy Joy": ("SJ", False, [
        ("I", 27.00, 24.00, 30.00), ("II", 21.00, 18.00, 24.00),
        ("III", 15.50, 13.00, 18.00), ("IV", 10.50, 7.75, 13.00)],
        "Spaced 6.00 / 6.00 / 5.00 / 5.25 rather than an even 5.00 ladder. An even "
        "ladder breaking at 10.00 % would split 9.20 % into one band and 10.96 / 11.20 % "
        "into the next, leaving margins of 0.96 % and 1.20 % — both under the buffer. "
        "This ladder holds all three results in Spec IV with 1.45 % clear."),
    "Wedding Crasher": ("WC", True, [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], ""),
}

CSS = """
:root{--ink:#1a2b22;--acc:#1f6f4a;--mut:#6a7a72;--line:#d8e2dc;--hl:#eaf4ee;--warn:#8a6d1a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:#fff;
 font-size:10.5px;line-height:1.45;padding:34px 42px}
h1{font-size:21px;letter-spacing:.4px;margin-bottom:2px}
.sub{color:var(--mut);font-size:10.5px;margin-bottom:4px}
.meta{color:var(--mut);font-size:9.5px;border-bottom:2px solid var(--acc);
 padding-bottom:10px;margin-bottom:14px}
.note{background:#f4f8f5;border:1px solid var(--line);border-left:3px solid var(--acc);
 padding:8px 12px;font-size:9.8px;margin-bottom:16px}
.strain{page-break-inside:avoid;margin-bottom:20px}
h2{font-size:13.5px;color:var(--acc);border-bottom:1px solid var(--line);
 padding-bottom:3px;margin-bottom:6px}
h2 .abbr{color:var(--mut);font-weight:normal;font-size:11px}
h2 .prov{font-size:9px;color:var(--warn);font-weight:normal;letter-spacing:.5px}
.why{font-size:9.6px;color:var(--mut);background:#fbfbf7;border:1px solid var(--line);
 padding:6px 10px;margin:6px 0}
table{border-collapse:collapse;width:100%;margin:6px 0 8px}
th{background:#204a37;color:#fff;font-size:9px;text-transform:uppercase;
 letter-spacing:.5px;padding:5px 8px;text-align:left;font-weight:600}
td{border:1px solid var(--line);padding:4px 8px;font-size:10px;vertical-align:top}
tr.hl td{background:var(--hl);font-weight:bold}
.r{text-align:right}
.tight{color:var(--warn);font-size:9px}
.small{font-size:9px;color:var(--mut)}
.foot{margin-top:22px;border-top:1px solid var(--line);padding-top:8px;
 color:var(--mut);font-size:9px}
@page{size:A4;margin:0}
"""


def collect():
    rows, batches = cp.build()
    by = cp.group_by_seq(rows)
    tr = {cc.norm_batch(r["batch"]): r for r in cc.read_tsv("tranches_overview.tsv")}
    per = defaultdict(list)
    for b in batches:
        st = (b["strain"] or "").strip()
        if st not in LADDERS:
            continue
        vals = []
        for r in by[b["seq"]]:
            if cp.classify(r["Parameter"]) != "thc":
                continue
            if cp.STABILITY_RE.search(r["Parameter"] or ""):
                continue
            v = cc.num(r["Result"].split("(")[0])
            if v is None:
                continue
            code = (r["Certificate Code"] or "").strip()
            if code.lower().startswith("n/a"):
                code = "PP in-house CoA"
            vals.append((v, code, cp.issue_date(r["Issue Date"])))
        sh = tr.get(cc.norm_batch(b["batch"])) or {}
        per[st].append({"batch": b["batch"], "p": (b["p_number"] or "").strip(),
                        "tranche": (sh.get("tranche") or "—").strip(),
                        "released": (sh.get("thc_pct") or "").strip(), "vals": vals})
    return per


def band_of(ladder, v):
    for roman, nom, lo, hi in ladder:
        if lo <= v < hi or (roman == "I" and v == hi):
            return roman, lo, hi
    return None, None, None


def main():
    per = collect()
    out_html, checked, failures, tights = [], 0, 0, 0

    out_html.append("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                    "<title>PP ImB Specifications — remaining strains</title>"
                    "<style>%s</style></head><body>" % CSS)
    out_html.append("<h1>Purely Plant — ImB Potency Specifications, remaining strains</h1>")
    out_html.append("<div class='sub'>The seven strains PP-QC-SPEC-001 v5.5 does not "
                    "cover · Спецификациски опсези за преостанатите сорти</div>")
    out_html.append("<div class='meta'>%s · 7 strains · %d batches · Issued %s · "
                    "Companion to PP-QC-SPEC-001 v5.5 (Tranche 1, 13 strains)</div>"
                    % (DOC, sum(len(v) for v in per.values()), ISSUED))
    out_html.append(
        "<div class='note'><b>Status: proposed, not released.</b> These ladders are "
        "derived from the potency history and require QC approval before they govern "
        "anything.<br><b>Conventions</b> follow v5.5 exactly: contiguous bands with the "
        "top of Spec I fixed at 30.00 %; lower limit inclusive, upper exclusive; product "
        "code {ABBR}-THC{nominal}:CBD1; a quarter-range buffer under the lowest observed "
        "result wherever attainable, flagged where not. CBD acceptance criterion &lt; "
        "1.0 % throughout. Released % w/w is the Tranches Overview control-sheet figure; "
        "where it differs from every certificate it is shown, not resolved.</div>")

    pdf_story = []
    for strain in sorted(LADDERS):
        abbr, prov, ladder, why = LADDERS[strain]
        entries = sorted(per.get(strain, []), key=lambda e: e["batch"])
        counts = defaultdict(int)
        for e in entries:
            for v, _c, _d in e["vals"]:
                r, _, _ = band_of(ladder, v)
                if r:
                    counts[r] += 1

        out_html.append("<div class='strain'><h2>%s <span class='abbr'>(%s)</span>%s</h2>"
                        % (strain, abbr,
                           " · <span class='prov'>PROVISIONAL (limited batch history)</span>"
                           if prov else ""))
        if why:
            out_html.append("<div class='why'><b>Ladder spacing.</b> %s</div>" % why)

        out_html.append("<table><thead><tr><th>Specification</th><th>Product Code</th>"
                        "<th>Nominal</th><th>Tolerance</th><th>Range (Total Δ⁹-THC)</th>"
                        "<th>Batches in band</th></tr></thead><tbody>")
        for roman, nom, lo, hi in ladder:
            up, dn = hi - nom, nom - lo
            tol = ("±%.2f%%" % up) if abs(up - dn) < 0.005 else \
                  ("+%.2f%% / −%.2f%%" % (up, dn))
            out_html.append("<tr%s><td>Spec %s</td><td>%s-THC%g:CBD1</td>"
                            "<td class='r'>%.2f%%</td><td class='r'>%s</td>"
                            "<td class='r'>%.2f – %.2f%%</td><td class='r'>%d</td></tr>"
                            % (" class='hl'" if counts[roman] else "", roman, abbr, nom,
                               nom, tol, lo, hi, counts[roman]))
        out_html.append("</tbody></table>")

        out_html.append("<table><thead><tr><th>Batch</th><th>P-No.</th><th>Tranche</th>"
                        "<th>Released % w/w</th><th>Certificate result</th>"
                        "<th>Certificate № · issued</th><th>Falls in</th>"
                        "<th>Margin lo / hi</th></tr></thead><tbody>")
        for e in entries:
            vals = e["vals"] or [(None, "no Total Δ⁹-THC result on file", "")]
            span = len(vals)
            for j, (v, code, date) in enumerate(vals):
                out_html.append("<tr>")
                if j == 0:
                    for val in (e["batch"], e["p"] or "—", "T%s" % e["tranche"],
                                e["released"] or "—"):
                        cls = " class='r'" if val == e["released"] else ""
                        out_html.append("<td rowspan='%d'%s>%s</td>" % (span, cls, val))
                if v is None:
                    out_html.append("<td class='r'>—</td><td colspan='3'>%s</td></tr>"
                                    % code)
                    continue
                roman, lo, hi = band_of(ladder, v)
                checked += 1
                if roman is None:
                    failures += 1
                    out_html.append("<td class='r'>%.2f</td><td>%s · %s</td>"
                                    "<td class='tight'>OUTSIDE LADDER</td>"
                                    "<td class='r'>—</td></tr>" % (v, code, date))
                    continue
                mlo, mhi = v - lo, hi - v
                buf = (hi - lo) / 4.0
                flag = ("<span class='tight'>▲ tight: %.2f%% above the Spec %s lower "
                        "limit</span>" % (mlo, roman)) if mlo < buf else ""
                if mlo < buf:
                    tights += 1
                out_html.append("<td class='r'>%.2f</td><td>%s · %s</td>"
                                "<td>Spec %s</td><td class='r'>%.2f / %.2f %s</td></tr>"
                                % (v, code, date, roman, mlo, mhi, flag))
        out_html.append("</tbody></table></div>")

    out_html.append("<div class='foot'>Verification: %d certificate results checked "
                    "against the proposed ladders — %d inside band, %d outside, %d with "
                    "a sub-buffer low-side margin (flagged inline). All ladders "
                    "contiguous; top of Spec I = 30.00%% throughout. Companion to "
                    "PP-QC-SPEC-001 v5.5, which carries the other 13 strains. "
                    "Two strain names need settling before release: v5.5 says "
                    "&ldquo;Cap Junkie&rdquo; where the register now says Cap Junky, and "
                    "the register says &ldquo;Permanent Market&rdquo; where v5.5 and the "
                    "control sheet say Permanent Marker.</div></body></html>"
                    % (checked, checked - failures, failures, tights))

    with open(HTML, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out_html))

    build_pdf(per)
    print("Wrote %s" % HTML)
    print("Wrote %s (%d bytes)" % (PDF, os.path.getsize(PDF)))
    print("strains: %d   results checked: %d   outside band: %d   tight: %d"
          % (len(LADDERS), checked, failures, tights))
    return 0


def build_pdf(per):
    pdfmetrics.registerFont(TTFont("DJ", os.path.join(FONTS, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DJB", os.path.join(FONTS, "DejaVuSans-Bold.ttf")))
    ACC = colors.HexColor("#1F6F4A")
    HEADBG = colors.HexColor("#204A37")
    HL = colors.HexColor("#EAF4EE")
    LINE = colors.HexColor("#D8E2DC")
    MUT = colors.HexColor("#6A7A72")

    body = ParagraphStyle("b", fontName="DJ", fontSize=7.3, leading=9)
    small = ParagraphStyle("s", parent=body, fontSize=6.6, leading=8.2, textColor=MUT)
    hd = ParagraphStyle("h", fontName="DJB", fontSize=6.9, leading=8.4,
                        textColor=colors.white)
    ttl = ParagraphStyle("t", fontName="DJB", fontSize=14.5, leading=17,
                         textColor=ACC, spaceAfter=2)
    sub = ParagraphStyle("su", parent=body, fontSize=8, leading=10.5, textColor=MUT,
                         spaceAfter=8)
    sec = ParagraphStyle("se", fontName="DJB", fontSize=10, leading=12, textColor=ACC,
                         spaceBefore=9, spaceAfter=3)

    st = [Paragraph("Purely Plant — ImB Potency Specifications, remaining strains", ttl),
          Paragraph("The seven strains PP-QC-SPEC-001 v5.5 does not cover. %s · Issued "
                    "%s · Companion to v5.5 (Tranche 1, 13 strains)." % (DOC, ISSUED), sub)]
    note = Table([[Paragraph(
        "<b>Status: proposed, not released.</b> Derived from the potency history; requires "
        "QC approval before governing anything. Conventions follow v5.5: contiguous bands, "
        "top of Spec I fixed at 30.00%, lower limit inclusive and upper exclusive, product "
        "code {ABBR}-THC{nominal}:CBD1, a quarter-range buffer under the lowest observed "
        "result where attainable. CBD acceptance criterion &lt; 1.0% throughout.", body)]],
        colWidths=[180 * mm])
    note.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F8F5")),
                              ("BOX", (0, 0), (-1, -1), 0.7, ACC),
                              ("LEFTPADDING", (0, 0), (-1, -1), 7),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                              ("TOPPADDING", (0, 0), (-1, -1), 6),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    st += [note, Spacer(1, 4)]

    for strain in sorted(LADDERS):
        abbr, prov, ladder, why = LADDERS[strain]
        entries = sorted(per.get(strain, []), key=lambda e: e["batch"])
        counts = defaultdict(int)
        for e in entries:
            for v, _c, _d in e["vals"]:
                r, _, _ = band_of(ladder, v)
                if r:
                    counts[r] += 1
        block = [Paragraph("%s &nbsp;<font size=7 color='#6A7A72'>(%s)</font>%s"
                           % (strain, abbr,
                              " &nbsp;<font size=6.5 color='#8A6D1A'>PROVISIONAL</font>"
                              if prov else ""), sec)]
        if why:
            block.append(Paragraph("<i>Ladder spacing.</i> %s" % why, small))
            block.append(Spacer(1, 3))

        d = [[Paragraph(t, hd) for t in ("Specification", "Product Code", "Nominal",
                                         "Tolerance", "Range (Total Δ9-THC)", "Batches")]]
        hls = []
        for i, (roman, nom, lo, hi) in enumerate(ladder, start=1):
            up, dn = hi - nom, nom - lo
            tol = ("±%.2f%%" % up) if abs(up - dn) < 0.005 else \
                  ("+%.2f%% / −%.2f%%" % (up, dn))
            d.append([Paragraph("Spec %s" % roman, body),
                      Paragraph("%s-THC%g:CBD1" % (abbr, nom), body),
                      Paragraph("%.2f%%" % nom, body), Paragraph(tol, body),
                      Paragraph("%.2f – %.2f%%" % (lo, hi), body),
                      Paragraph(str(counts[roman]), body)])
            if counts[roman]:
                hls.append(("BACKGROUND", (0, i), (-1, i), HL))
        t1 = Table(d, colWidths=[20 * mm, 36 * mm, 20 * mm, 32 * mm, 40 * mm, 16 * mm])
        t1.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), HEADBG),
                                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)] + hls))
        block += [t1, Spacer(1, 3)]

        d2 = [[Paragraph(t, hd) for t in ("Batch", "P-No.", "Released", "Result",
                                          "Certificate № · issued", "Band", "Margin lo/hi")]]
        spans, r = [], 1
        for e in entries:
            vals = e["vals"] or [(None, "no result on file", "")]
            for j, (v, code, date) in enumerate(vals):
                roman, lo, hi = band_of(ladder, v) if v is not None else (None, 0, 0)
                marg = "—"
                if v is not None and roman:
                    marg = "%.2f / %.2f" % (v - lo, hi - v)
                d2.append([
                    Paragraph("<b>%s</b>" % e["batch"], body) if j == 0 else "",
                    Paragraph(e["p"] or "—", body) if j == 0 else "",
                    Paragraph(e["released"] or "—", body) if j == 0 else "",
                    Paragraph("%.2f" % v if v is not None else "—", body),
                    Paragraph("%s · %s" % (code, date), small),
                    Paragraph("Spec %s" % roman if roman else "—", body),
                    Paragraph(marg, body)])
            if len(vals) > 1:
                spans += [("SPAN", (c, r), (c, r + len(vals) - 1)) for c in (0, 1, 2)]
            r += len(vals)
        t2 = Table(d2, colWidths=[24 * mm, 18 * mm, 18 * mm, 15 * mm, 55 * mm,
                                  16 * mm, 22 * mm], repeatRows=1)
        t2.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), HEADBG),
                                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("ALIGN", (2, 1), (3, -1), "RIGHT"),
                                ("ALIGN", (6, 1), (6, -1), "RIGHT"),
                                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)] + spans))
        block.append(t2)
        st.append(KeepTogether(block))

    st += [Spacer(1, 6), Paragraph(
        "Companion to PP-QC-SPEC-001 v5.5, which carries the other 13 strains. Two strain "
        "names need settling before release: v5.5 says “Cap Junkie” where the register now "
        "says Cap Junky, and the register says “Permanent Market” where v5.5 and the "
        "control sheet say Permanent Marker.", small)]

    SimpleDocTemplate(PDF, pagesize=A4, title="PP ImB Specifications — remaining strains",
                      author="Purely Plant QC", leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=14 * mm, bottomMargin=14 * mm).build(st)


if __name__ == "__main__":
    sys.exit(main())
