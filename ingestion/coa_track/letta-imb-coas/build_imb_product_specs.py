#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ImB Dry Cannabis Flower — the full product specification for every Purely Plant strain.

PP-QC-SPEC-001 v5.5 and its v5.6 companion carry the potency ladders and nothing else. A
product specification is the whole release contract: what the product is, how it is
presented, and every parameter it must satisfy with the limit and the method beside it.
This builds that, one sheet per strain, for all 20 strains in the register.

Two halves per sheet, because they come from different places and are trusted differently:

  The potency ladder is strain-specific and empirical — derived from that strain's own
  certificate history, band by band, and carried through unchanged from v5.5 (13 strains)
  and v5.6 (the remaining 7).

  The quality panel is common to every strain and is not invented here. Each limit is the
  one Purely Plant already applies, as evidenced on its compiled CoQs and on the
  outsourced certificates, against Ph. Eur. Cannabis flos 07/2024:3028 and the general
  chapters. The method column names the chapter so any limit can be checked at source.

Three points where the evidence is not unanimous are stated on the sheet rather than
silently resolved:

  Loss on drying is ≤ 12.0 % per the current 07/2024:3028 monograph. Certificates issued
  before it took effect carry ≤ 10.00 %, and the owner has ruled that the current
  monograph governs regardless of what an older certificate printed.

  Bile-tolerant gram-negative bacteria is ≤ 10^4 CFU/g under Ph. Eur. 5.1.8 category C.
  The Purely Plant in-house CoA applies a tighter < 10^2 CFU/g, and some IPH reports print
  ≤ 10^2. The monograph limit is specified and the tighter in-house practice is noted.

  Mycotoxins are specified as all three parameters — aflatoxin B1, total aflatoxins and
  ochratoxin A. Batches assayed before the 197-series retests carry total aflatoxins only;
  those are recorded as not tested on the other two rather than left blank.

Pesticides are specified as a conformity statement against Ph. Eur. 2.8.13 rather than as
a list of every analyte, per the owner's instruction: a value is stated only where there
is an actual finding.

Nothing here is a released specification. These are proposals compiled from the potency
history and the applied limits, and they require QC approval before they govern anything.
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
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "exports", "PP_ImB_Product_Specifications.html")
PDF = os.path.join(HERE, "exports", "PP_ImB_Product_Specifications.pdf")
FONTS = "/usr/share/fonts/truetype/dejavu"

DOC, ISSUED = "PP-QC-SPEC-001 v5.7 (proposed, consolidated)", "11.08.2026"
MONOGRAPH = "Ph. Eur. 11.5 Cannabis flos 07/2024:3028"

# Ladder spacing notes, carried over from v5.6 where the spacing was not an even ladder.
WHY = {
    "Clemosa a bud":
        "Five bands are needed to reach 8.02 %. A four-band ladder floored at 7.00 % "
        "would leave only 1.02 % under the result, short of the quarter-range buffer.",
    "Sleepy Joy":
        "Spaced 6.00 / 6.00 / 5.00 / 5.25 rather than an even 5.00 ladder. An even ladder "
        "breaking at 10.00 % would split 9.20 % into one band and 10.96 / 11.20 % into the "
        "next, leaving margins of 0.96 % and 1.20 % — both under the buffer. This ladder "
        "holds all three results in Spec IV with 1.45 % clear.",
}

# strain -> (abbr, provisional, ladder top-first, source document)
LADDERS = {
    "Blue Gelato": ("BG", True, [("I", 27.50, 25.25, 30.00), ("II", 23.00, 20.80, 25.25)], "v5.5"),
    "Blue Sunset Sherbet": ("BSS", False, [("I", 27.50, 24.75, 30.00), ("II", 22.00, 19.39, 24.75)], "v5.5"),
    "Cap Junky": ("CJ", False, [("I", 28.00, 25.25, 30.00), ("II", 22.50, 19.75, 25.25),
                                ("III", 17.00, 13.93, 19.75)], "v5.5"),
    "Cash Cow": ("CC", True, [("I", 28.00, 25.50, 30.00), ("II", 23.00, 20.50, 25.50),
                              ("III", 18.00, 15.50, 20.50)], "v5.5"),
    "Fat Bastard": ("FB", False, [("I", 27.50, 24.75, 30.00), ("II", 22.00, 19.25, 24.75),
                                  ("III", 16.50, 13.68, 19.25)], "v5.5"),
    "Gorilla Glue": ("GG", False, [("I", 27.00, 24.00, 30.00), ("II", 21.00, 18.00, 24.00),
                                   ("III", 15.00, 12.34, 18.00)], "v5.5"),
    "Grape Pie": ("GP", False, [("I", 28.00, 26.00, 30.00), ("II", 24.00, 22.00, 26.00),
                                ("III", 20.00, 18.00, 22.00), ("IV", 16.00, 13.83, 18.00)], "v5.5"),
    "High Pro Amnesia": ("HPA", False, [("I", 27.50, 24.75, 30.00), ("II", 22.00, 19.39, 24.75),
                                        ("III", 16.00, 13.50, 19.39)], "v5.5"),
    "Jelly Donutz": ("JD", False, [("I", 28.00, 26.00, 30.00), ("II", 24.00, 22.00, 26.00),
                                   ("III", 20.00, 18.00, 22.00), ("IV", 15.00, 12.50, 18.00)], "v5.5"),
    "Jokerz 31": ("J31", False, [("I", 27.00, 23.50, 30.00), ("II", 20.00, 16.50, 23.50)], "v5.5"),
    "Orange Punch Mimosa": ("OPM", False, [("I", 28.00, 25.00, 30.00), ("II", 22.00, 19.00, 25.00),
                                           ("III", 16.00, 13.00, 19.00), ("IV", 10.00, 7.09, 13.00)], "v5.5"),
    "Permanent Marker": ("PM", False, [("I", 26.50, 24.00, 30.00), ("II", 21.50, 19.00, 24.00),
                                       ("III", 16.50, 14.00, 19.00), ("IV", 11.50, 9.01, 14.00)], "v5.5"),
    "Scrambler": ("SCR", True, [("I", 27.50, 25.25, 30.00), ("II", 23.00, 20.75, 25.25),
                                ("III", 18.50, 16.13, 20.75)], "v5.5"),
    "Apple and Banana": ("AB", True, [("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
                                      ("III", 17.50, 15.00, 20.00)], "v5.6"),
    "Clemosa a bud": ("CLE", True, [("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
                                    ("III", 17.50, 15.00, 20.00), ("IV", 12.50, 10.00, 15.00),
                                    ("V", 7.50, 5.00, 10.00)], "v5.6"),
    "Graps & Creme": ("GRC", True, [("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
                                    ("III", 17.50, 15.00, 20.00), ("IV", 12.50, 10.00, 15.00)], "v5.6"),
    "Kush Crasher": ("KC", True, [("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
                                  ("III", 17.50, 15.00, 20.00)], "v5.6"),
    "Motor Breath": ("MB", True, [("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
                                  ("III", 17.50, 15.00, 20.00)], "v5.6"),
    "Sleepy Joy": ("SJ", False, [("I", 27.00, 24.00, 30.00), ("II", 21.00, 18.00, 24.00),
                                 ("III", 15.50, 13.00, 18.00), ("IV", 10.50, 7.75, 13.00)], "v5.6"),
    "Wedding Crasher": ("WC", True, [("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
                                     ("III", 17.50, 15.00, 20.00)], "v5.6"),
}

# (group, parameter, acceptance criterion, method / reference)
PANEL = [
    ("Description", "Appearance", "Dark green to pale yellow or light brown to "
     "reddish-brown female inflorescence, with characteristic aromatic odour", "Visual"),
    ("Description", "Identification", "Retention time of each cannabinoid of the test "
     "solution corresponds to that of the standard solution",
     "HPLC/DAD · Ph. Eur. 2.8.23"),
    ("Description", "Foreign matter", "&lt; 2.0 %", "Ph. Eur. 2.8.2"),
    ("Description", "Loss on drying", "≤ 12.0 %", "Ph. Eur. 2.2.32:2024"),
    ("Assay", "Total Δ⁹-THC", "Per the potency specification band above", "HPLC/DAD"),
    ("Assay", "Total CBD", "&lt; 1.0 %", "HPLC/DAD"),
    ("Assay", "Total CBN", "&lt; 1.0 %", "HPLC/DAD"),
    ("Mycotoxins", "Aflatoxin B1", "≤ 2 µg/kg", "Ph. Eur. 2.8.18"),
    ("Mycotoxins", "Total aflatoxins (B1+B2+G1+G2)", "≤ 4 µg/kg",
     "Ph. Eur. 2.8.18 / Afla test fluorometric"),
    ("Mycotoxins", "Ochratoxin A", "≤ 20 µg/kg", "Ph. Eur. 2.8.18"),
    ("Heavy metals", "Lead (Pb)", "≤ 0.5 mg/kg", "Ph. Eur. 2.4.27 / MKC EN 17853:2023"),
    ("Heavy metals", "Cadmium (Cd)", "≤ 0.3 mg/kg", "Ph. Eur. 2.4.27 / MKC EN 17853:2023"),
    ("Heavy metals", "Arsenic (As)", "≤ 0.2 mg/kg", "Ph. Eur. 2.4.27 / MKC EN 17853:2023"),
    ("Heavy metals", "Mercury (Hg)", "≤ 0.1 mg/kg", "Ph. Eur. 2.4.27 / MKC EN 17853:2023"),
    ("Pesticides", "Pesticide residues", "Complies. Individual limits per Ph. Eur. table "
     "2.8.13-1; a value is reported only where there is a finding, otherwise ND / &lt; LOQ",
     "Ph. Eur. 2.8.13 / MKC EN 15662:2020"),
    ("Microbiological quality", "Total aerobic microbial count (TAMC)", "≤ 10⁵ CFU/g",
     "Ph. Eur. 2.6.12 · 5.1.8 category C"),
    ("Microbiological quality", "Total combined yeasts/moulds (TYMC)", "≤ 10⁴ CFU/g",
     "Ph. Eur. 2.6.12 · 5.1.8 category C"),
    ("Microbiological quality", "Bile-tolerant gram-negative bacteria", "≤ 10⁴ CFU/g",
     "Ph. Eur. 2.6.13 · 5.1.8 category C"),
    ("Microbiological quality", "Escherichia coli", "Absent / 1 g", "Ph. Eur. 2.6.31"),
    ("Microbiological quality", "Salmonella", "Absent / 25 g", "Ph. Eur. 2.6.31"),
]

PRESENTATION = [
    ("Dosage form", "Dried cannabis flower for medicinal use (Cannabis flos)"),
    ("Monograph", MONOGRAPH),
    ("Primary packaging", "400.0 g ± 3 % triplex aluminium bag, heat-sealed"),
    ("Storage", "Below 25 °C, protected from light and moisture, in the original package"),
    ("Retest period", "12 months from date of manufacture"),
    ("Manufacturer", "Purely Plant DOOEL, s. Kojlija, Petrovec, North Macedonia"),
]

NOTES = [
    "<b>Loss on drying</b> is ≤ 12.0 %% per the current %s. Certificates issued before "
    "that monograph took effect carry ≤ 10.00 %%; the current monograph governs."
    % MONOGRAPH,
    "<b>Bile-tolerant gram-negative bacteria</b> is specified at the Ph. Eur. 5.1.8 "
    "category C limit of ≤ 10⁴ CFU/g. The Purely Plant in-house CoA applies a tighter "
    "&lt; 10² CFU/g and some IPH reports print ≤ 10²; the tighter practice is not "
    "specified here but is not prohibited by it.",
    "<b>Mycotoxins</b> are specified as all three parameters. Batches assayed before the "
    "Farmahem 197-series retests carry total aflatoxins only; on those the other two are "
    "recorded as not tested rather than left blank.",
    "<b>Pesticides</b> are specified as a conformity statement, not an analyte list. A "
    "value is stated only where there is an actual finding.",
]

CSS = """
:root{--ink:#1a2b22;--acc:#1f6f4a;--mut:#6a7a72;--line:#d8e2dc;--hl:#eaf4ee;--warn:#8a6d1a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:#fff;
 font-size:10.5px;line-height:1.45;padding:30px 38px}
h1{font-size:20px;margin-bottom:2px}
.sub{color:var(--mut);font-size:10.5px;margin-bottom:4px}
.meta{color:var(--mut);font-size:9.5px;border-bottom:2px solid var(--acc);
 padding-bottom:10px;margin-bottom:14px}
.note{background:#f4f8f5;border:1px solid var(--line);border-left:3px solid var(--acc);
 padding:8px 12px;font-size:9.6px;margin-bottom:8px}
.note ul{margin:4px 0 0 16px}.note li{margin-bottom:3px}
.sheet{page-break-before:always;page-break-inside:avoid;margin-bottom:24px}
.sheet:first-of-type{page-break-before:avoid}
h2{font-size:14px;color:var(--acc);border-bottom:1.5px solid var(--acc);
 padding-bottom:3px;margin:14px 0 6px}
h2 .abbr{color:var(--mut);font-weight:normal;font-size:11px}
h2 .prov{font-size:9px;color:var(--warn);font-weight:normal;letter-spacing:.5px}
h3{font-size:10px;color:var(--acc);text-transform:uppercase;letter-spacing:.6px;
 margin:9px 0 3px}
table{border-collapse:collapse;width:100%;margin:4px 0 6px}
th{background:#204a37;color:#fff;font-size:8.6px;text-transform:uppercase;
 letter-spacing:.4px;padding:4px 7px;text-align:left;font-weight:600}
td{border:1px solid var(--line);padding:3px 7px;font-size:9.6px;vertical-align:top}
tr.hl td{background:var(--hl);font-weight:bold}
td.grp{background:#f4f8f5;font-weight:bold;font-size:9px;color:var(--acc)}
.r{text-align:right}.small{font-size:9px;color:var(--mut)}
.foot{margin-top:20px;border-top:1px solid var(--line);padding-top:8px;
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
            return roman
    return None


def main():
    per = collect()
    checked = [0, 0, 0]        # results seen, outside ladder, sub-buffer margin
    h = ["<!DOCTYPE html><html><head><meta charset='utf-8'>"
         "<title>PP ImB Dry Cannabis Flower — Product Specifications</title>"
         "<style>%s</style></head><body>" % CSS]
    h.append("<h1>Purely Plant — ImB Dry Cannabis Flower</h1>")
    h.append("<div class='sub'>Product specifications, all strains · "
             "Спецификации на производот, сите сорти</div>")
    h.append("<div class='meta'>%s · %d strains · %s · Issued %s · Potency ladders from "
             "PP-QC-SPEC-001 v5.5 and v5.6</div>"
             % (DOC, len(LADDERS), MONOGRAPH, ISSUED))
    h.append("<div class='note'><b>Status: proposed, not released.</b> Compiled from the "
             "potency history and the limits Purely Plant already applies; requires QC "
             "approval before it governs anything.<ul>"
             + "".join("<li>%s</li>" % n for n in NOTES) + "</ul></div>")

    for strain in sorted(LADDERS, key=lambda s: s.lower()):
        abbr, prov, ladder, src = LADDERS[strain]
        entries = sorted(per.get(strain, []), key=lambda e: e["batch"])
        counts = defaultdict(int)
        for e in entries:
            for v, _c, _d in e["vals"]:
                r = band_of(ladder, v)
                if r:
                    counts[r] += 1

        h.append("<div class='sheet'><h2>%s <span class='abbr'>(%s)</span>%s</h2>"
                 % (strain, abbr,
                    " · <span class='prov'>PROVISIONAL — limited batch history</span>"
                    if prov else ""))

        h.append("<h3>1 · Product identification</h3><table><tbody>")
        for k, v in [("Product name", "%s — Dry Cannabis Flower" % strain),
                     ("Strain / cultivar", strain),
                     ("Product code family", "%s-THC{nominal}:CBD1" % abbr)] + PRESENTATION:
            h.append("<tr><td style='width:26%%'><b>%s</b></td><td>%s</td></tr>" % (k, v))
        h.append("</tbody></table>")

        h.append("<h3>2 · Potency specification (Total Δ⁹-THC, %% w/w) — source %s</h3>"
                 % src)
        if strain in WHY:
            h.append("<p class='small'><b>Ladder spacing.</b> %s</p>" % WHY[strain])
        h.append("<table><thead><tr><th>Specification</th><th>Product code</th>"
                 "<th>Nominal</th><th>Tolerance</th><th>Range</th>"
                 "<th>Batches</th></tr></thead><tbody>")
        for roman, nom, lo, hi in ladder:
            up, dn = hi - nom, nom - lo
            tol = ("±%.2f%%" % up) if abs(up - dn) < 0.005 else \
                  ("+%.2f%% / −%.2f%%" % (up, dn))
            h.append("<tr%s><td>Spec %s</td><td>%s-THC%g:CBD1</td><td class='r'>%.2f%%</td>"
                     "<td class='r'>%s</td><td class='r'>%.2f – %.2f%%</td>"
                     "<td class='r'>%d</td></tr>"
                     % (" class='hl'" if counts[roman] else "", roman, abbr, nom, nom,
                        tol, lo, hi, counts[roman]))
        h.append("</tbody></table>")

        h.append("<h3>3 · Quality specification</h3><table><thead><tr>"
                 "<th style='width:15%'>Group</th><th style='width:24%'>Parameter</th>"
                 "<th>Acceptance criterion</th><th style='width:26%'>Method / reference"
                 "</th></tr></thead><tbody>")
        last = None
        for grp, param, crit, meth in PANEL:
            h.append("<tr><td class='grp'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % (grp if grp != last else "", param, crit, meth))
            last = grp
        h.append("</tbody></table>")

        h.append("<h3>4 · Batch history and specification verification</h3>")
        if entries:
            h.append("<table><thead><tr><th>Batch</th><th>P-No.</th><th>Tr.</th>"
                     "<th>Released</th><th>Result</th><th>Certificate № · issued</th>"
                     "<th>Falls in</th><th>Margin lo / hi</th></tr></thead><tbody>")
            for e in entries:
                vals = e["vals"] or [(None, "no Total Δ⁹-THC result on file", "")]
                span = len(vals)
                for j, (v, code, date) in enumerate(vals):
                    h.append("<tr>")
                    if j == 0:
                        h.append("<td rowspan='%d'>%s</td><td rowspan='%d'>%s</td>"
                                 "<td rowspan='%d'>T%s</td>"
                                 "<td rowspan='%d' class='r'>%s</td>"
                                 % (span, e["batch"], span, e["p"] or "—", span,
                                    e["tranche"], span, e["released"] or "—"))
                    if v is None:
                        h.append("<td class='r'>—</td><td colspan='3'>%s</td></tr>" % code)
                        continue
                    roman = band_of(ladder, v)
                    checked[0] += 1
                    if roman is None:
                        checked[1] += 1
                        h.append("<td class='r'>%.2f</td><td>%s · %s</td>"
                                 "<td class='tight'>OUTSIDE LADDER</td>"
                                 "<td class='r'>—</td></tr>" % (v, code, date))
                        continue
                    lo, hi = next((l, hh) for r2, _n, l, hh in ladder if r2 == roman)
                    mlo, mhi, buf = v - lo, hi - v, (hi - lo) / 4.0
                    flag = ""
                    if mlo < buf:
                        checked[2] += 1
                        flag = ("<span class='tight'>▲ tight: %.2f%% above the Spec %s "
                                "lower limit</span>" % (mlo, roman))
                    h.append("<td class='r'>%.2f</td><td>%s · %s</td><td>Spec %s</td>"
                             "<td class='r'>%.2f / %.2f %s</td></tr>"
                             % (v, code, date, roman, mlo, mhi, flag))
            h.append("</tbody></table>")
        else:
            h.append("<p class='small'>No batches on the register for this strain.</p>")
        h.append("</div>")

    h.append("<div class='foot'>%d strain specifications. Verification: %d certificate "
             "results checked against the ladders — %d inside band, %d outside, %d with a "
             "sub-buffer low-side margin (flagged inline). Potency ladders carried "
             "unchanged from PP-QC-SPEC-001 v5.5 (13 strains) and v5.6 (7 strains); the "
             "quality panel is common to all strains and reflects the limits already "
             "applied, against %s. Strain names are settled: Cap Junky (Capulator × Seed "
             "Junky Genetics) and Permanent Marker, both consistent across the register "
             "and these documents. PP-QC-SPEC-001 v5.5 in Drive still carries the old "
             "&ldquo;Cap Junkie&rdquo; heading and needs the same edit."
             "</div></body></html>"
             % (len(LADDERS), checked[0], checked[0] - checked[1], checked[1], checked[2],
                MONOGRAPH))

    with open(HTML, "w", encoding="utf-8") as fh:
        fh.write("\n".join(h))

    build_pdf(per)
    print("Wrote %s" % HTML)
    print("Wrote %s (%d bytes)" % (PDF, os.path.getsize(PDF)))
    print("strains: %d   panel parameters: %d   batches covered: %d"
          % (len(LADDERS), len(PANEL), sum(len(per.get(s, [])) for s in LADDERS)))
    print("verification: %d results checked, %d outside band, %d sub-buffer margin"
          % (checked[0], checked[1], checked[2]))
    return 0


def build_pdf(per):
    pdfmetrics.registerFont(TTFont("DJ", os.path.join(FONTS, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DJB", os.path.join(FONTS, "DejaVuSans-Bold.ttf")))
    ACC = colors.HexColor("#1F6F4A")
    HEADBG = colors.HexColor("#204A37")
    HL = colors.HexColor("#EAF4EE")
    LINE = colors.HexColor("#D8E2DC")
    MUT = colors.HexColor("#6A7A72")
    GRPBG = colors.HexColor("#F4F8F5")

    body = ParagraphStyle("b", fontName="DJ", fontSize=6.9, leading=8.6)
    small = ParagraphStyle("s", parent=body, fontSize=6.3, leading=7.9, textColor=MUT)
    hd = ParagraphStyle("h", fontName="DJB", fontSize=6.4, leading=7.9,
                        textColor=colors.white)
    grp = ParagraphStyle("g", fontName="DJB", fontSize=6.5, leading=8.2, textColor=ACC)
    ttl = ParagraphStyle("t", fontName="DJB", fontSize=14, leading=17, textColor=ACC)
    sub = ParagraphStyle("su", parent=body, fontSize=7.6, leading=10, textColor=MUT,
                         spaceAfter=7)
    sec = ParagraphStyle("se", fontName="DJB", fontSize=11, leading=13.5, textColor=ACC,
                         spaceBefore=2, spaceAfter=4)
    h3 = ParagraphStyle("h3", fontName="DJB", fontSize=7.2, leading=9, textColor=ACC,
                        spaceBefore=6, spaceAfter=2)

    st = [Paragraph("Purely Plant — ImB Dry Cannabis Flower", ttl),
          Paragraph("Product specifications, all strains. %s · %d strains · %s · Issued "
                    "%s · Potency ladders from PP-QC-SPEC-001 v5.5 and v5.6."
                    % (DOC, len(LADDERS), MONOGRAPH, ISSUED), sub)]
    note = Table([[Paragraph("<b>Status: proposed, not released.</b> Compiled from the "
                             "potency history and the limits Purely Plant already applies; "
                             "requires QC approval before it governs anything.<br/><br/>"
                             + "<br/>".join("• " + n for n in NOTES), body)]],
                 colWidths=[180 * mm])
    note.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GRPBG),
                              ("BOX", (0, 0), (-1, -1), 0.7, ACC),
                              ("LEFTPADDING", (0, 0), (-1, -1), 7),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                              ("TOPPADDING", (0, 0), (-1, -1), 6),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    st += [note]

    grid = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]

    for strain in sorted(LADDERS, key=lambda s: s.lower()):
        abbr, prov, ladder, src = LADDERS[strain]
        entries = sorted(per.get(strain, []), key=lambda e: e["batch"])
        counts = defaultdict(int)
        for e in entries:
            for v, _c, _d in e["vals"]:
                r = band_of(ladder, v)
                if r:
                    counts[r] += 1
        st.append(PageBreak())
        blk = [Paragraph("%s &nbsp;<font size=8 color='#6A7A72'>(%s)</font>%s"
                         % (strain, abbr,
                            " &nbsp;<font size=6.5 color='#8A6D1A'>PROVISIONAL</font>"
                            if prov else ""), sec),
               Paragraph("1 · Product identification", h3)]
        d = [[Paragraph("<b>%s</b>" % k, body), Paragraph(v, body)]
             for k, v in [("Product name", "%s — Dry Cannabis Flower" % strain),
                          ("Strain / cultivar", strain),
                          ("Product code family", "%s-THC{nominal}:CBD1" % abbr)] + PRESENTATION]
        t = Table(d, colWidths=[42 * mm, 138 * mm])
        t.setStyle(TableStyle(grid))
        blk += [t, Paragraph("2 · Potency specification (Total Δ9-THC, %% w/w) — source %s"
                             % src, h3)]

        d = [[Paragraph(x, hd) for x in ("Specification", "Product code", "Nominal",
                                         "Tolerance", "Range", "Batches")]]
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
        t = Table(d, colWidths=[22 * mm, 38 * mm, 22 * mm, 34 * mm, 40 * mm, 24 * mm])
        t.setStyle(TableStyle(grid + [("BACKGROUND", (0, 0), (-1, 0), HEADBG),
                                      ("ALIGN", (2, 1), (-1, -1), "RIGHT")] + hls))
        if strain in WHY:
            blk.append(Paragraph("<i>Ladder spacing.</i> %s" % WHY[strain], small))
        blk += [t, Paragraph("3 · Quality specification", h3)]

        d = [[Paragraph(x, hd) for x in ("Group", "Parameter", "Acceptance criterion",
                                         "Method / reference")]]
        last = None
        for g, param, crit, meth in PANEL:
            d.append([Paragraph(g if g != last else "", grp), Paragraph(param, body),
                      Paragraph(crit.replace("&lt;", "<"), body), Paragraph(meth, body)])
            last = g
        t = Table(d, colWidths=[27 * mm, 42 * mm, 62 * mm, 49 * mm], repeatRows=1)
        t.setStyle(TableStyle(grid + [("BACKGROUND", (0, 0), (-1, 0), HEADBG),
                                      ("BACKGROUND", (0, 1), (0, -1), GRPBG)]))
        blk += [t, Paragraph("4 · Batch history and specification verification", h3)]

        if entries:
            d = [[Paragraph(x, hd) for x in ("Batch", "P-No.", "Tr.", "Released",
                                             "Result", "Certificate № · issued",
                                             "Falls in", "Margin lo / hi")]]
            spans, rr = [], 1
            for e in entries:
                vals = e["vals"] or [(None, "no result on file", "")]
                for j, (v, code, date) in enumerate(vals):
                    roman = band_of(ladder, v) if v is not None else None
                    marg = "—"
                    if roman:
                        lo, hi = next((l, hh) for r2, _n, l, hh in ladder if r2 == roman)
                        marg = "%.2f / %.2f" % (v - lo, hi - v)
                    d.append([
                        Paragraph(e["batch"], body) if j == 0 else "",
                        Paragraph(e["p"] or "—", body) if j == 0 else "",
                        Paragraph("T%s" % e["tranche"], body) if j == 0 else "",
                        Paragraph(e["released"] or "—", body) if j == 0 else "",
                        Paragraph("%.2f" % v if v is not None else "—", body),
                        Paragraph("%s · %s" % (code, date), small),
                        Paragraph("Spec %s" % roman if roman else "—", body),
                        Paragraph(marg, body)])
                if len(vals) > 1:
                    spans += [("SPAN", (c, rr), (c, rr + len(vals) - 1))
                              for c in (0, 1, 2, 3)]
                rr += len(vals)
            t = Table(d, colWidths=[26 * mm, 20 * mm, 11 * mm, 18 * mm, 15 * mm,
                                    48 * mm, 18 * mm, 24 * mm], repeatRows=1)
            t.setStyle(TableStyle(grid + [("BACKGROUND", (0, 0), (-1, 0), HEADBG),
                                          ("ALIGN", (3, 1), (4, -1), "RIGHT"),
                                          ("ALIGN", (7, 1), (7, -1), "RIGHT")] + spans))
            blk.append(t)
        else:
            blk.append(Paragraph("No batches on the register for this strain.", small))
        st.append(KeepTogether(blk))

    st += [Spacer(1, 6), Paragraph(
        "Potency ladders carried unchanged from PP-QC-SPEC-001 v5.5 and v5.6; the quality "
        "panel is common to all strains and reflects the limits already applied, against "
        "%s. Strain names are settled: Cap Junky (Capulator × Seed Junky Genetics) and "
        "Permanent Marker, both consistent across the register and these documents. "
        "PP-QC-SPEC-001 v5.5 in Drive still carries the old “Cap Junkie” heading and needs "
        "the same edit." % MONOGRAPH, small)]

    SimpleDocTemplate(PDF, pagesize=A4,
                      title="PP ImB Dry Cannabis Flower — Product Specifications",
                      author="Purely Plant QC", leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=13 * mm, bottomMargin=13 * mm).build(st)


if __name__ == "__main__":
    sys.exit(main())
