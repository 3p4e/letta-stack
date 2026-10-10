#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue the QCSP 001 product specifications with the potency ladders extended.

This replaces build_imb_product_specs.py, which emitted a document in a format I
invented before the real house documents came to light. Purely Plant already has a
QCSP 001 layout — bilingual English/Macedonian, "Grade I/II/III" rather than "Spec",
product codes written ABBR_THCnn:CBD1, twelve numbered analytical parameters including
three identification tests — and a specification that does not look like the others is
worse than useless in a QMS. So the ladder work now comes out in that format.

Why the ladders needed extending
--------------------------------
Every bottom grade in v5.5 was floored exactly 1.00 percentage point below whatever
the lowest batch had assayed at the time it was written:

    Cap Junky        floor 13.93   lowest then 14.93
    Gorilla Glue     floor 12.34   lowest then 13.34
    Grape Pie        floor 13.83   lowest then 14.83
    Permanent Marker floor  9.01   lowest then 10.01
    Fat Bastard      floor 13.68   lowest then 14.68  (FB012601/1)

A floor set that way is guaranteed to be breached by the first batch that comes in
lower, which is exactly what happened: CC112501 at 13.35% and FB032601 at 12.39% fall
below every grade their cultivar has. Twelve further ladders sit one point above their
lowest result and would break the same way.

So rather than patching the two that failed, every ladder is extended downward on its
own spacing. The owner asked for "another grade or even 2 more"; two are added wherever
the arithmetic allows.

How the extension is derived
----------------------------
PUBLISHED below is v5.5/v5.6 verbatim and is never modified — it is the provenance, and
the released documents have to remain reconstructible from it. The new grades are
derived from it at build time, so the diff between what was issued and what is proposed
is visible in the document itself rather than buried in a rewritten constant.

  step         the spacing between the last two published nominals, i.e. the local
               spacing at the end being extended (some ladders are not evenly spaced,
               and the top spacing is the wrong guide for the bottom)
  nominal      previous nominal minus one step
  ceiling      the published floor, unchanged — no issued boundary moves
  floor        nominal minus half a step
  stop         after two added grades, or at a 5.00% floor — below roughly that the
               material is not THC-dominant, and this document's own banner claims it
               is, so grades reaching to 0.50% would make the page contradict itself

Nothing here judges a batch pass or fail. Extending a specification does not make an
already-released batch conforming: CC112501 and FB032601 were tested against the spec in
force at the time and still need dispositioning against that. This revision governs
batches tested from its effective date onward, which is why the documents go out as
v.02 rather than as a correction to v.01.
"""
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict

import coa_pivot as cp
import house_fonts

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "house_specs")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

TEMPLATE_VERSION = "QCSP 001 v.03"     # the layout, unchanged by this revision
DOC_REVISION = "v.02"                  # per-cultivar document revision
APPROVED = "01.06.2026"

MAX_ADDED = 2
MIN_FLOOR = 5.00        # no grade may reach below this
MIN_TAIL_WIDTH = 2.00   # narrower than this and the tail is stretched, not added

# v5.5/v5.6 exactly as issued, keyed by the cultivar name the register uses:
#   (abbr, name printed on the specification, house filename stem,
#    [(grade, nominal, floor, cap)], source)

PUBLISHED = {
    "Apple and Banana": ("AB", "Apples &amp; Bananas", "AB_Apples_Bananas", [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], "v5.6"),
    "Blue Gelato": ("BG", "Blue Gelato", "BG_Blue_Gelato", [
        ("I", 27.50, 25.25, 30.00), ("II", 23.00, 20.80, 25.25)], "v5.5"),
    "Blue Sunset Sherbet": ("BSS", "Blue Sunset Sherbet", "BSS_Blue_Sunset_Sherbet", [
        ("I", 27.50, 24.75, 30.00), ("II", 22.00, 19.39, 24.75)], "v5.5"),
    "Cap Junky": ("CJ", "Cap Junky", "CJ_Cap_Junky", [
        ("I", 28.00, 25.25, 30.00), ("II", 22.50, 19.75, 25.25),
        ("III", 17.00, 13.93, 19.75)], "v5.5"),
    "Cash Cow": ("CC", "Cash Cow", "CC_Cash_Cow", [
        ("I", 28.00, 25.50, 30.00), ("II", 23.00, 20.50, 25.50),
        ("III", 18.00, 15.50, 20.50)], "v5.5"),
    "Clemosa a bud": ("CLE", "Clemosa", "CLE_Clemosa", [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00), ("IV", 12.50, 10.00, 15.00),
        ("V", 7.50, 5.00, 10.00)], "v5.6"),
    "Fat Bastard": ("FB", "Fat Bastard", "FB_Fat_Bastard", [
        ("I", 27.50, 24.75, 30.00), ("II", 22.00, 19.25, 24.75),
        ("III", 16.50, 13.68, 19.25)], "v5.5"),
    "Gorilla Glue": ("GG", "Gorilla Glue", "GG_Gorilla_Glue", [
        ("I", 27.00, 24.00, 30.00), ("II", 21.00, 18.00, 24.00),
        ("III", 15.00, 12.34, 18.00)], "v5.5"),
    "Grape Pie": ("GP", "Grape Pie", "GP_Grape_Pie", [
        ("I", 28.00, 26.00, 30.00), ("II", 24.00, 22.00, 26.00),
        ("III", 20.00, 18.00, 22.00), ("IV", 16.00, 13.83, 18.00)], "v5.5"),
    "Graps & Creme": ("GRC", "Graps Cr&egrave;me", "GRC_Graps_Cr_me", [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00), ("IV", 12.50, 10.00, 15.00)], "v5.6"),
    "High Pro Amnesia": ("HPA", "High Pro Amnesia", "HPA_High_Pro_Amnesia", [
        ("I", 27.50, 24.75, 30.00), ("II", 22.00, 19.39, 24.75),
        ("III", 16.00, 13.50, 19.39)], "v5.5"),
    "Jelly Donutz": ("JD", "Jelly Donutz", "JD_Jelly_Donutz", [
        ("I", 28.00, 26.00, 30.00), ("II", 24.00, 22.00, 26.00),
        ("III", 20.00, 18.00, 22.00), ("IV", 15.00, 12.50, 18.00)], "v5.5"),
    "Jokerz 31": ("J31", "Jokerz 31", "J31_Jokerz_31", [
        ("I", 27.00, 23.50, 30.00), ("II", 20.00, 16.50, 23.50)], "v5.5"),
    "Kush Crasher": ("KC", "Kush Crasher", "KC_Kush_Crasher", [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], "v5.6"),
    "Motor Breath": ("MB", "Motor Breath", "MB_Motor_Breath", [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], "v5.6"),
    "Orange Punch Mimosa": ("OPM", "Orange Punch Mimosa", "OPM_Orange_Punch_Mimosa", [
        ("I", 28.00, 25.00, 30.00), ("II", 22.00, 19.00, 25.00),
        ("III", 16.00, 13.00, 19.00), ("IV", 10.00, 7.09, 13.00)], "v5.5"),
    "Permanent Marker": ("PM", "Permanent Marker", "PM_Permanent_Marker", [
        ("I", 26.50, 24.00, 30.00), ("II", 21.50, 19.00, 24.00),
        ("III", 16.50, 14.00, 19.00), ("IV", 11.50, 9.01, 14.00)], "v5.5"),
    "Scrambler": ("SCR", "Scrambler", "SCR_Scrambler", [
        ("I", 27.50, 25.25, 30.00), ("II", 23.00, 20.75, 25.25),
        ("III", 18.50, 16.13, 20.75)], "v5.5"),
    "Sleepy Joy": ("SJ", "Sleepy Joe", "SJ_Sleepy_Joe", [
        ("I", 27.00, 24.00, 30.00), ("II", 21.00, 18.00, 24.00),
        ("III", 15.50, 13.00, 18.00), ("IV", 10.50, 7.75, 13.00)], "v5.6"),
    "Wedding Crasher": ("WC", "Wedding Crasher", "WC_Wedding_Crasher", [
        ("I", 27.50, 25.00, 30.00), ("II", 22.50, 20.00, 25.00),
        ("III", 17.50, 15.00, 20.00)], "v5.6"),
}

# Which grade carries the TARGET marker. This is a commercial decision, not something
# derivable from the assays — Kush Crasher's v.01 marks Grade III while its Blue Gelato,
# Cash Cow and Fat Bastard siblings all mark Grade I, and no result pattern explains the
# difference. The four below are read off the issued v.01 documents; the rest default to
# Grade I and want the owner's confirmation before these go out.
TARGET_GRADE = {"KC": "III", "BG": "I", "CC": "I", "FB": "I"}
TARGET_CONFIRMED = set(TARGET_GRADE)

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def roman(n):
    return ROMAN[n - 1] if n <= len(ROMAN) else str(n)


def extend(grades):
    """Continue a published ladder downward on its own spacing.

    Returns (full ladder, list of added grade labels). Published entries come back
    untouched, floors included — each published floor becomes the ceiling of the grade
    below it, so no boundary already in circulation moves.

    The ladder stops at MIN_FLOOR. Below about 5% the product is not THC-dominant in any
    meaningful sense, and the banner on this very document says it is, so a Grade whose
    range opened at 0.50% would make the page contradict itself. Two shapes handle the
    bottom: if a full step still clears MIN_FLOOR it is taken as-is, and if it does not,
    one final grade spans MIN_FLOOR up to the last floor with its nominal at the
    midpoint — a wider bottom band, which is the normal shape for a low-potency grade.
    A tail narrower than MIN_TAIL_WIDTH is not worth its own row, so the last grade's
    floor is stretched to MIN_FLOOR instead.
    """
    out = list(grades)
    if len(grades) < 2:
        return out, []
    step = round(grades[-2][1] - grades[-1][1], 2)
    if step <= 0:
        return out, []

    added = []
    nominal, ceiling = grades[-1][1], grades[-1][2]
    while len(added) < MAX_ADDED:
        cand = round(nominal - step, 2)
        floor = round(cand - step / 2.0, 2)
        if floor >= MIN_FLOOR:
            label = roman(len(out) + 1)
            out.append((label, cand, floor, ceiling))
            added.append(label)
            nominal, ceiling = cand, floor
            continue
        # a full step would go too low: close the ladder off at MIN_FLOOR
        if ceiling - MIN_FLOOR >= MIN_TAIL_WIDTH:
            label = roman(len(out) + 1)
            # the midpoint, snapped to a half-point: a product code reading
            # FB_THC6.62:CBD1 next to FB_THC27.5 and FB_THC16.5 announces itself as
            # machine output rather than a specification somebody set
            mid = round((MIN_FLOOR + ceiling) / 2.0 * 2.0) / 2.0
            mid = min(max(mid, MIN_FLOOR + 0.5), ceiling - 0.5)
            out.append((label, mid, MIN_FLOOR, ceiling))
            added.append(label)
        elif added:
            label, nom, _floor, cap = out[-1]
            out[-1] = (label, nom, MIN_FLOOR, cap)
        break
    return out, added


def code(abbr, nominal):
    """Product code in house form: trailing zeros dropped, e.g. CC_THC28:CBD1."""
    return "%s_THC%g:CBD1" % (abbr, nominal)


def collect():
    """Every release Total-Δ9-THC result on file, by cultivar."""
    rows, batches = cp.build()
    by_seq = cp.group_by_seq(rows)
    obs = defaultdict(list)
    for b in batches:
        strain = (b["strain"] or "").strip()
        for r in by_seq[b["seq"]]:
            if cp.classify(r["Parameter"]) != "thc":
                continue
            if cp.STABILITY_RE.search(r["Parameter"] or ""):
                continue
            head = r["Result"].split("(")[0]
            if any(t in head.lower() for t in ("<", "≤", "loq", "blq")):
                continue
            m = re.search(r"(\d+(?:[.,]\d+)?)", head)
            if not m:
                continue
            obs[strain].append({
                "batch": b["batch"], "value": float(m.group(1).replace(",", ".")),
                "cert": (r["Certificate Code"] or "").strip(),
                "date": cp.issue_date(r["Issue Date"]),
            })
    return obs


def grade_of(ladder, v):
    for label, _nominal, floor, cap in ladder:
        if floor <= v <= cap:
            return label
    return None


CSS = """
  @page { size: A4; margin: 0; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  :root {
    --navy:#1B3A5C; --navy-deep:#0F2540; --navy-mid:#2C5282; --navy-soft:#3B6BA5;
    --gold:#A67C2E; --gold-bright:#C9A227; --gold-deep:#7A5C1E; --gold-tint:#FBF6E9;
    --zebra:#F4F7FB; --zebra-head:#EEF3F9;
    --paper:#FFFFFF; --surface:#F8FAFC;
    --ink:#0F172A; --text:#1E293B; --text-sec:#475569; --text-ter:#8C9BB0;
    --border:#C9D4E3; --border-light:#E3EAF3;
    --MARGIN-H: 0.4in;
    --PAD-V:    0.4in;
  }
  body { font-family:'Montserrat','Helvetica Neue',Arial,sans-serif; background:#64748B; color:var(--text); display:flex; justify-content:center; padding:20px; }
  .page { width:210mm; min-height:297mm; background:var(--paper); overflow:hidden; box-shadow:0 8px 60px rgba(15,37,64,.25); display:flex; flex-direction:column; }

  .header-bar { background:#F3E8CE; padding:var(--PAD-V) var(--MARGIN-H) 4mm; display:flex; justify-content:space-between; align-items:center; border-bottom:2.5px solid var(--gold); }
  /* a fixed box rather than width:auto, so the header stays balanced whether or not
     assets/logo/PP_Leaf_T2.svg is sitting beside the document */
  .hb-logo { height:62px; width:168px; object-fit:contain; object-position:left center;
             display:block; flex-shrink:0; }
  .hb-center { text-align:center; }
  .hb-title { font-size:18px; font-weight:800; letter-spacing:4px; text-transform:uppercase; color:#1B3A5C; }
  .hb-sub { font-size:8.5px; font-weight:400; letter-spacing:2px; color:#5A7391; text-transform:uppercase; margin-top:2px; }
  .hb-right { text-align:right; }
  .hb-code { font-size:12px; font-weight:700; color:var(--gold-deep); font-family:'Roboto Mono',monospace; }
  .hb-mk-title { font-size:8.5px; font-weight:500; letter-spacing:2px; text-transform:uppercase; color:#8C9BB0; font-style:italic; margin-top:3px; }
  .hb-mk-sub { font-size:7.5px; font-weight:400; letter-spacing:1px; color:#8C9BB0; font-style:italic; margin-top:1px; }

  .product-banner { display:flex; align-items:stretch; border-bottom:2px solid var(--gold-deep); }
  .pb-main { flex:1; min-width:0; background:var(--surface); padding:5px var(--MARGIN-H); display:flex; flex-direction:row; align-items:center; justify-content:space-between; gap:16px; }
  .pb-name { font-size:27px; font-weight:800; letter-spacing:.6px; text-transform:uppercase; color:var(--navy); line-height:1; position:relative; padding-bottom:5px; white-space:nowrap; }
  .pb-name .pb-cultivar-lbl { font-size:11px; font-weight:700; font-style:italic; letter-spacing:.3px; text-transform:none; color:var(--navy-soft); vertical-align:baseline; margin-right:3px; }
  .pb-name::after { content:""; position:absolute; left:0; bottom:0; width:64px; height:3px; background:linear-gradient(90deg,var(--gold-bright),var(--gold)); border-radius:2px; }
  .pb-types { display:flex; flex-direction:column; align-items:flex-start; gap:3px; flex-wrap:nowrap; flex-shrink:0; }
  .pb-type-pill { font-size:7.5px; font-weight:700; letter-spacing:0; text-transform:uppercase; padding:2px 7px; border-radius:10px; line-height:1; white-space:nowrap; display:inline-flex; align-items:center; }
  .pb-type-pill.botanical { background:#FBF6E9; color:var(--gold-deep); border:1px solid var(--gold); padding-left:8px; gap:4px; }
  .pb-type-pill.chemo { background:var(--gold-tint); color:var(--gold-deep); border:1px solid var(--gold); }
  .pb-type-pill.processing { background:#FBF6E9; color:var(--gold-deep); border:1px solid var(--gold); padding-left:8px; gap:4px; }
  .pb-type-pill.botanical .var-opt,
  .pb-type-pill.processing .var-opt { color:#A9A08A; font-weight:700; margin:0 1px; }
  .pb-type-pill.botanical .var-opt.sel,
  .pb-type-pill.processing .var-opt.sel { background:var(--navy); color:#fff; border-radius:8px; padding:1px 6px; font-weight:800; letter-spacing:.3px; box-shadow:0 1px 2px rgba(27,58,92,.28); }
  .pb-type-pill.botanical .var-sep,
  .pb-type-pill.processing .var-sep { color:#D3C39A; margin:0 5px; }
  .pb-ref { background:#F3E8CE; color:#1B3A5C; padding:5px var(--MARGIN-H) 5px 14px; text-align:center; display:flex; flex-direction:column; justify-content:center; flex-shrink:0; border-left:3px solid var(--gold-deep); min-width:180px; box-sizing:border-box; }
  .pb-ref-label { font-size:8.5px; color:var(--gold-deep); letter-spacing:1.5px; text-transform:uppercase; }
  .pb-ref-val { font-size:12px; font-weight:700; letter-spacing:.3px; margin-top:1px; font-family:'Roboto Mono',monospace; white-space:nowrap; }

  .info-grid { display:grid; grid-template-columns:1.5fr 1.65fr 1.9fr 0.95fr; margin:0 var(--MARGIN-H); border-bottom:1px solid var(--border); }
  .ig-cell { padding:3px 12px 2px; border-right:1px solid var(--border-light); border-bottom:1px solid var(--border-light); }
  .ig-cell:last-child { border-right:none; }
  .ig-label { font-size:8.5px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:var(--text-ter); margin-bottom:1px; }
  .ig-val { font-size:9.5px; font-weight:600; color:var(--ink); line-height:1.2; }
  .ig-val .mk { display:block; color:#8C9BB0; font-style:italic; font-weight:500; font-size:7.5px; line-height:1.15; margin-top:1px; }

  .sec-label { font-size:8.5px; font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:#1B3A5C; background:#F3E8CE; padding:3px var(--MARGIN-H); border-top:1.5px solid var(--gold-deep); border-bottom:1.5px solid var(--gold-deep); display:flex; align-items:baseline; gap:10px; white-space:nowrap; overflow:hidden; }
  .sec-label .sec-no { font-family:'Roboto Mono',monospace; color:var(--gold-deep); font-size:11px; }

  .tbl-wrap { padding:0 var(--MARGIN-H); }
  table.potency { width:100%; border-collapse:collapse; margin-bottom:2px; }
  table.potency thead th { background:var(--zebra-head); font-size:8.5px; font-weight:700; letter-spacing:.8px; text-transform:uppercase; color:var(--navy); padding:4px 6px; text-align:center; border-bottom:2px solid var(--navy); }
  table.potency thead th:first-child { text-align:left; }
  table.potency tbody td { padding:3px 6px; border-bottom:1px solid var(--border-light); font-size:9.5px; text-align:center; color:var(--ink); font-family:'Roboto Mono',monospace; font-weight:500; }
  table.potency tbody td:first-child { text-align:left; font-family:'Montserrat',sans-serif; font-weight:700; color:var(--navy); }
  table.potency tbody tr:nth-child(even) td { background:var(--zebra); }
  table.potency tbody tr:first-child td { padding-top:3px; }
  table.potency tbody tr.highlight td { background:#EAF0F6; font-weight:700; color:var(--navy); border-top:1px solid var(--navy); border-bottom:1px solid var(--navy); padding-top:3px; padding-bottom:3px; vertical-align:middle; line-height:1; }
  table.potency tbody tr.highlight td:first-child { box-shadow:inset 4px 0 0 var(--navy); position:relative; }
  table.potency tbody tr.highlight td:nth-child(3) { font-size:11px; font-weight:800; color:var(--navy); line-height:1; }
  table.potency tbody tr.highlight td:first-child::after { content:"TARGET"; position:absolute; top:50%; right:6px; transform:translateY(-50%); font-family:'Roboto Mono',monospace; font-size:6.5px; letter-spacing:.5px; color:#fff; background:var(--navy); padding:1px 4px; border-radius:3px; font-weight:700; }
  table.potency tbody tr.added td { background:#FCFAF3; }
  table.potency tbody tr.added td:first-child::before { content:"NEW"; font-family:'Roboto Mono',monospace; font-size:6px; letter-spacing:.5px; color:var(--gold-deep); border:1px solid var(--gold); border-radius:3px; padding:0 3px; margin-right:5px; font-weight:700; vertical-align:1px; }
  .pot-note { font-size:8px; color:var(--text-sec); padding:3px var(--MARGIN-H) 3px; line-height:1.35; }
  .pot-note strong { color:var(--navy); }

  table.params { width:100%; border-collapse:collapse; table-layout:fixed; }
  table.params th:nth-child(1){ width:22px; } table.params th:nth-child(2){ width:28%; }
  table.params th:nth-child(3){ width:25%; } table.params th:nth-child(4){ width:auto; }
  table.params thead th { background:var(--zebra-head); font-size:8.5px; font-weight:700; letter-spacing:.8px; text-transform:uppercase; color:var(--navy); padding:3px 6px; text-align:left; border-bottom:2px solid var(--navy); }
  table.params thead th:first-child { text-align:center; }
  table.params tbody td { padding:0 6px; border-bottom:1px solid var(--border-light); font-size:9px; line-height:1.25; vertical-align:middle; }
  table.params tbody tr:first-child td { padding-top:7px; }
  table.params tbody tr:nth-child(even) td:not(.row-group-cell) { background:var(--zebra); }
  table.params tbody td:first-child { text-align:center; font-family:'Roboto Mono',monospace; font-weight:700; color:var(--navy-soft); }
  .p-name { font-weight:700; color:var(--ink); }
  .p-name .mk { font-size:7px; line-height:1; letter-spacing:.1px; margin-top:0; }
  .p-sub { font-size:8.5px; color:var(--text-sec); display:block; line-height:1.05; }
  .p-method { font-size:8.5px; color:var(--text-sec); font-family:'Roboto Mono',monospace; white-space:normal; overflow-wrap:anywhere; line-height:1.15; }
  .p-meth-eq { display:block; margin-top:1px; }
  .p-spec { font-size:9px; color:var(--text); font-family:'Roboto Mono',monospace; }
  .p-tag { font-weight:600; color:var(--text-ter); font-size:8.5px; letter-spacing:.2px; }
  .row-group td { padding-top:3px; background:var(--gold-tint); }
  .row-group .row-group-cell { background:var(--gold-tint) !important; color:var(--gold-deep); }
  .sub-row td { padding-left:14px; }
  .sub-row td:first-child { border-bottom-color:transparent; color:var(--text-ter); }

  .approval-grid { display:grid; grid-template-columns:1fr 1fr; gap:30px; padding:5px var(--MARGIN-H) 2px; margin-top:22px; }
  .ap-block { text-align:center; position:relative; }
  .ap-role { font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--gold-deep); margin-bottom:3px; }
  .ap-sign { position:relative; height:34px; margin-bottom:2px; }
  .ap-sign .ap-line { position:absolute; left:0; right:0; bottom:0; border-bottom:1px solid var(--navy); }
  .ap-title { font-size:11px; font-weight:700; color:var(--navy); }
  .ap-name { font-size:12.5px; font-weight:700; color:var(--navy); margin-top:2px; }
  .ap-date-row { margin-top:3px; display:flex; justify-content:center; align-items:center; gap:6px; }
  .ap-date-label { font-size:8.5px; font-weight:600; color:var(--text-ter); text-transform:uppercase; }
  .ap-date-val { font-size:10px; font-weight:700; color:var(--ink); font-family:'Roboto Mono',monospace; }

  .footer { margin-top:auto; padding:3mm var(--MARGIN-H) var(--PAD-V); background:#F3E8CE; color:#1B3A5C; border-top:2.5px solid var(--gold); display:flex; justify-content:space-between; align-items:center; gap:12px; }
  .foot-left { font-size:8px; color:#5A7391; line-height:1.25; flex:1; }
  .foot-right { font-size:8px; color:#5A7391; line-height:1.4; text-align:right; flex:1; font-family:'Roboto Mono',monospace; }
  .foot-center-num { text-align:center; flex:0 0 auto; font-family:'Roboto Mono',monospace; font-weight:600; font-size:10px; letter-spacing:1px; color:#5A7391; }

  .mk { color:#8C9BB0; font-style:italic; font-weight:500; }
  .ig-label .mk, .hb-title .mk, .hb-sub .mk, table.params thead th .mk, table.potency thead th .mk, .ap-role .mk, .ap-title .mk { display:block; text-transform:none; letter-spacing:.1px; line-height:1.05; margin-top:.5px; font-weight:400; font-size:7.5px; }
  .ap-role .mk, .ap-title .mk { color:#8C9BB0; }
  .sec-label .mk { display:inline; font-weight:400; text-transform:none; letter-spacing:.4px; color:#5A7391; font-style:italic; font-size:8px; }
  .sec-label .mk::before { content:" | "; font-style:normal; color:#8C9BB0; }
  @media print { body { background:white; padding:0; } .page { box-shadow:none; } }
"""

# Section 02 is identical on every cultivar's specification, so it is a constant.
PARAMS = """
        <tr><td>1</td><td><span class="p-name">Macroscopic Identification <span class="p-tag">· Test A</span> <span class="mk" style="display:block">Макроскопска идентификација</span></span></td><td><span class="p-method">Ph. Eur. mon. 3028</span></td><td><span class="p-spec">Conforms to monograph <span class="mk">Соодветствува со монографијата</span></span></td></tr>
        <tr><td>2</td><td><span class="p-name">Microscopic Identification <span class="p-tag">· Test B</span> <span class="mk" style="display:block">Микроскопска идентификација</span></span></td><td><span class="p-method">Ph. Eur. 2.8.23 (microscopy)</span></td><td><span class="p-spec">Conforms to monograph <span class="mk">Соодветствува со монографијата</span></span></td></tr>
        <tr><td>3</td><td><span class="p-name">HPTLC Identification <span class="p-tag">· Test C</span> <span class="mk" style="display:block">HPTLC идентификација</span></span></td><td><span class="p-method">Ph. Eur. 2.8.25 (HPTLC)</span></td><td><span class="p-spec">Conforms to monograph <span class="mk">Соодветствува со монографијата</span></span></td></tr>
        <tr><td>4</td><td><span class="p-name">Assay — Total Δ<sup>9</sup>-THC <span class="mk" style="display:block">Анализа — вкупен Δ⁹-THC</span></span></td><td><span class="p-method">Ph. Eur. 2.2.29 (HPLC)</span></td><td><span class="p-spec">Per target grade as per Section 01 <span class="mk" style="display:block">Според целна класа од Дел 01</span></span></td></tr>
        <tr><td>5</td><td><span class="p-name">Assay — Total CBD <span class="mk" style="display:block">Анализа — вкупен CBD</span></span></td><td><span class="p-method">Ph. Eur. 2.2.29 (HPLC)</span></td><td><span class="p-spec">≤ 1.0%</span></td></tr>
        <tr><td>6</td><td><span class="p-name">Total CBN <span class="mk" style="display:block">Вкупен CBN</span></span></td><td><span class="p-method">Ph. Eur. 2.2.29 (HPLC)</span></td><td><span class="p-spec">≤ 1.0%</span></td></tr>
        <tr><td>7</td><td><span class="p-name">Foreign Matter <span class="mk" style="display:block">Страни материи</span></span></td><td><span class="p-method">Ph. Eur. 2.8.2<span class="p-meth-eq">In-house · интерна</span></span></td><td><span class="p-spec">≤ 2.0% · no seeds · leaves &lt; 1 cm · sample 25–50 g <span class="mk">≤ 2.0% · без семки · листови &lt; 1 cm · мостра 25–50 g</span></span></td></tr>
        <tr><td>8</td><td><span class="p-name">Loss on Drying <span class="mk" style="display:block">Губиток при сушење</span></span></td><td><span class="p-method">Ph. Eur. 2.2.32 (gravimetric)</span></td><td><span class="p-spec">≤ 12.0% (mol. sieve R, 40 °C, 24 h, 15–25 mbar) <span class="mk">≤ 12.0% (мол. сито R, 40 °C, 24 h, 15–25 mbar)</span></span></td></tr>
        <tr class="row-group"><td rowspan="6" class="row-group-cell">9</td><td colspan="3"><span class="p-name">Microbiological Quality <span class="mk">Микробиолошки квалитет</span></span> <span class="p-sub" style="display:inline; margin-left:6px;">Ph. Eur. 5.1.4 / 5.1.8 cat. C</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">TAMC <span class="mk">вкупен аеробен микробен број</span></span></td><td><span class="p-method">Ph. Eur. 2.6.12</span></td><td><span class="p-spec">≤ 10<sup>5</sup> CFU/g</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">TYMC <span class="mk">вкупен број квасци/мувли</span></span></td><td><span class="p-method">Ph. Eur. 2.6.12</span></td><td><span class="p-spec">≤ 10<sup>4</sup> CFU/g</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Bile-tolerant gram-neg. <span class="mk">жолчно-толерантни грам-нег.</span></span></td><td><span class="p-method">Ph. Eur. 2.6.31</span></td><td><span class="p-spec">≤ 10<sup>4</sup> CFU/g</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Salmonella <span class="mk">салмонела</span></span></td><td><span class="p-method">Ph. Eur. 2.6.31</span></td><td><span class="p-spec">Absence / 25 g <span class="mk">отсуство / 25 g</span></span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Escherichia coli <span class="mk">ешерихија коли</span></span></td><td><span class="p-method">Ph. Eur. 2.6.13</span></td><td><span class="p-spec">Absence / 1 g <span class="mk">отсуство / 1 g</span></span></td></tr>
        <tr class="row-group"><td rowspan="4" class="row-group-cell">10</td><td colspan="3"><span class="p-name">Mycotoxins <span class="mk">Микотоксини</span></span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Aflatoxin B<sub>1</sub> <span class="mk">афлатоксин B<sub>1</sub></span></span></td><td><span class="p-method">Ph. Eur. 2.8.18 (HPLC-FLD)</span></td><td><span class="p-spec">≤ 2 µg/kg</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Total Aflatoxins (B<sub>1</sub>+B<sub>2</sub>+G<sub>1</sub>+G<sub>2</sub>) <span class="mk">вкупни афлатоксини</span></span></td><td><span class="p-method">Ph. Eur. 2.8.18 (HPLC-FLD)</span></td><td><span class="p-spec">≤ 4 µg/kg</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Ochratoxin A <span class="mk">охратоксин A</span></span></td><td><span class="p-method">Ph. Eur. 2.8.22 (HPLC-FLD)</span></td><td><span class="p-spec">≤ 20 µg/kg</span></td></tr>
        <tr class="row-group"><td rowspan="5" class="row-group-cell">11</td><td colspan="3"><span class="p-name">Heavy Metals <span class="mk">Тешки метали</span></span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Lead (Pb) <span class="mk">олово (Pb)</span></span></td><td><span class="p-method">Ph. Eur. 2.4.27 (ICP-MS)</span></td><td><span class="p-spec">≤ 0.5 mg/kg</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Cadmium (Cd) <span class="mk">кадмиум (Cd)</span></span></td><td><span class="p-method">Ph. Eur. 2.4.27 (ICP-MS)</span></td><td><span class="p-spec">≤ 0.3 mg/kg</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Arsenic (As) <span class="mk">арсен (As)</span></span></td><td><span class="p-method">Ph. Eur. 2.4.27 (ICP-MS)</span></td><td><span class="p-spec">≤ 0.2 mg/kg</span></td></tr>
        <tr class="sub-row"><td><span class="p-sub">Mercury (Hg) <span class="mk">жива (Hg)</span></span></td><td><span class="p-method">Ph. Eur. 2.4.27 (ICP-MS)</span></td><td><span class="p-spec">≤ 0.1 mg/kg</span></td></tr>
        <tr><td>12</td><td><span class="p-name">Pesticide Residues <span class="mk" style="display:block">Остатоци од пестициди</span></span><span class="p-sub">Multi-residue panel <span class="mk">мулти-резидуален панел</span></span></td><td><span class="p-method">Ph. Eur. 2.8.13 (GC-MS/MS · LC-MS/MS)<span class="p-meth-eq">CUMCS Equivalency</span></span></td><td><span class="p-spec">≤ LOQ per Ph. Eur. 2.8.13 <span class="mk">≤ LOQ според Ph. Eur. 2.8.13</span></span></td></tr>
"""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Purely Plant — Product Specification — @@DISPLAY@@ (@@ABBR@@)</title>
<style>@@FONTS@@
@@CSS@@</style>
</head>
<body>
<div class="page">
  <div class="header-bar">
    <img class="hb-logo" src="../assets/logo/PP_Leaf_T2.svg" alt="">
    <div class="hb-center"><div class="hb-title">Product Specification</div><div class="hb-sub">Intermediate Bulk — Dry Cannabis Flower for Medical Use</div><div class="hb-mk-title">Спецификација на производ</div><div class="hb-mk-sub">Интермедиер балк — сув цвет од канабис за медицинска употреба</div></div>
    <div class="hb-right"><div class="hb-code">QCSP 001_@@ABBR@@_@@REV@@</div></div>
  </div>

  <div class="product-banner">
    <div class="pb-main">
      <div class="pb-name"><span class="pb-cultivar-lbl">Cultivar:</span> @@DISPLAY@@</div>
      <div class="pb-types">
        <span class="pb-type-pill botanical">Variety: <span class="var-opt">Indica</span><span class="var-sep">|</span><span class="var-opt">Sativa</span><span class="var-sep">|</span><span class="var-opt sel">Hybrid</span></span>
        <span class="pb-type-pill chemo">THC-dominant · Ph. Eur. type</span>
        <span class="pb-type-pill processing">Processing: <span class="var-opt sel">Hand Trimmed</span><span class="var-sep">|</span><span class="var-opt">Machine Trimmed</span></span>
      </div>
    </div>
    <div class="pb-ref"><div class="pb-ref-label">Dry Cannabis Flower —<br>Cannabis Sativa L.</div><div class="pb-ref-val">Ph. Eur. 11.5 / 3028</div></div>
  </div>

  <div class="info-grid">
    <div class="ig-cell"><div class="ig-label">Primary Packaging <span class="mk">Примарно пакување</span></div><div class="ig-val">Triplex Alu Bag · 300 × 500 mm<br>fill 400.0 g ±3% <span class="mk">Триплекс алу кеса · 300 × 500 mm<br>полнење 400.0 g ±3%</span></div></div>
    <div class="ig-cell"><div class="ig-label">Product Form <span class="mk">Форма на производ</span></div><div class="ig-val">Dried herbal substance · Intermediate Bulk product <span class="mk">Сушена билна супстанца · Меѓупроизвод балк</span></div></div>
    <div class="ig-cell"><div class="ig-label">Storage <span class="mk">Чување</span></div><div class="ig-val">15–25 °C · &lt;60% RH · protect from light <span class="mk">15–25 °C · &lt;60% RH · заштита од светлина</span></div></div>
    <div class="ig-cell"><div class="ig-label">Shelf Life <span class="mk">Рок на употреба</span></div><div class="ig-val">EXP. TBD</div></div>
  </div>

  <div class="sec-label" style="margin-top:12px"><span class="sec-no">01</span> Potency Classification <span class="mk">Класификација по јачина</span></div>
  <div class="tbl-wrap">
    <table class="potency">
      <thead><tr><th>Grade <span class="mk">Класа</span></th><th>Product Code <span class="mk">Код на производ</span></th><th>Nominal <span class="mk">Номинал</span></th><th>Range <span class="mk">Опсег</span></th><th>CBD <span class="mk">ЦБД</span></th></tr></thead>
      <tbody>
@@ROWS@@
      </tbody>
    </table>
  </div>
  <div class="pot-note">@@NOTE@@</div>

  <div class="sec-label" style="margin-top:12px"><span class="sec-no">02</span> Analytical Parameters &amp; Acceptance Criteria <span class="mk">Аналитички параметри и критериуми за прифатливост</span></div>
  <div class="tbl-wrap">
    <table class="params">
      <thead><tr><th>№</th><th>Parameter <span class="mk">Параметар</span></th><th><span style="white-space:nowrap">Method / Reference</span> <span class="mk" style="display:block">Метода / Референца</span></th><th>Acceptance Criteria <span class="mk">Критериум за прифатливост</span></th></tr></thead>
      <tbody>@@PARAMS@@      </tbody>
    </table>
  </div>

  <div class="approval-grid">
    <div class="ap-block"><div class="ap-role">Prepared &amp; Approved by <span class="mk">Изготвил и одобрил</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">QC Manager <span class="mk">Менаџер за КК</span></div><div class="ap-name">Blagoj Nikolov</div><div class="ap-date-row"><span class="ap-date-label">Date · Датум</span><span class="ap-date-val">@@APPROVED@@</span></div></div>
    <div class="ap-block"><div class="ap-role">Reviewed by <span class="mk">Прегледал</span></div><div class="ap-sign"><div class="ap-line"></div></div><div class="ap-title">QA Manager <span class="mk">Менаџер за ОК</span></div><div class="ap-name">Jovana Romevska Cvetkovski</div><div class="ap-date-row"><span class="ap-date-label">Date · Датум</span><span class="ap-date-val">@@APPROVED@@</span></div></div>
  </div>

  <div class="footer">
    <div class="foot-left">Purely Plant DOOEL · Industriska ulica 9, br. 9,<br>s. Kojlija 1043 · Petrovec-Skopje, North Macedonia</div>
    <div class="foot-center-num">1 | 1</div>
    <div class="foot-right">@@TEMPLATE@@</div>
  </div>
</div>
</body>
</html>
"""


def render(abbr, display, ladder, added, fonts=""):
    """One QCSP 001 specification page.

    Substitution is by explicit token rather than %-formatting or str.format, because
    the stylesheet is full of both % and {} and every escaping scheme collides with
    one or the other. Tokens cannot.
    """
    target = TARGET_GRADE.get(abbr, "I")
    rows = []
    for label, nominal, floor, cap in ladder:
        cls = []
        if label == target:
            cls.append("highlight")
        if label in added:
            cls.append("added")
        attr = ' class="%s"' % " ".join(cls) if cls else ""
        rows.append(
            "        <tr%s><td>Grade %s</td><td>%s</td><td>%.2f%%</td>"
            "<td>%.2f \u2013 %.2f%%</td><td>\u2264 1.0%%</td></tr>"
            % (attr, label, code(abbr, nominal), nominal, floor, cap))

    if added:
        lo = min(g[2] for g in ladder if g[0] in added)
        plural = "s" if len(added) > 1 else ""
        verb = "are" if len(added) > 1 else "is"
        note = ("<strong>Revision %s.</strong> Grade%s %s %s added, extending the "
                "classification down to %.2f%% on this cultivar\u2019s own grade "
                "spacing. No grade, nominal or boundary issued in v.01 is altered. "
                "<span class=\"mk\">\u0420\u0435\u0432\u0438\u0437\u0438\u0458\u0430 %s "
                "\u2014 \u0434\u043e\u0434\u0430\u0434\u0435\u043d\u0438 "
                "\u043d\u043e\u0432\u0438 \u043a\u043b\u0430\u0441\u0438; "
                "\u043f\u043e\u0441\u0442\u043e\u0458\u043d\u0438\u0442\u0435 "
                "\u043e\u0441\u0442\u0430\u043d\u0443\u0432\u0430\u0430\u0442 "
                "\u043d\u0435\u043f\u0440\u043e\u043c\u0435\u043d\u0435\u0442\u0438."
                "</span>"
                % (DOC_REVISION, plural, " and ".join(added), verb, lo, DOC_REVISION))
    else:
        note = ("<strong>Revision %s.</strong> The classification is unchanged from "
                "v.01 \u2014 this cultivar\u2019s ladder already reaches its lowest "
                "practicable grade. "
                "<span class=\"mk\">\u0420\u0435\u0432\u0438\u0437\u0438\u0458\u0430 %s "
                "\u2014 \u0431\u0435\u0437 \u043f\u0440\u043e\u043c\u0435\u043d\u0430 "
                "\u0432\u043e \u043a\u043b\u0430\u0441\u0438\u0444\u0438"
                "\u043a\u0430\u0446\u0438\u0458\u0430\u0442\u0430.</span>"
                % (DOC_REVISION, DOC_REVISION))

    out = PAGE
    for token, value in (("@@CSS@@", CSS), ("@@PARAMS@@", PARAMS),
                         ("@@FONTS@@", fonts),
                         ("@@ROWS@@", "\n".join(rows)), ("@@NOTE@@", note),
                         ("@@DISPLAY@@", display), ("@@ABBR@@", abbr),
                         ("@@REV@@", DOC_REVISION), ("@@APPROVED@@", APPROVED),
                         ("@@TEMPLATE@@", TEMPLATE_VERSION)):
        out = out.replace(token, value)
    assert "@@" not in out, "unsubstituted token remains"
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    obs = collect()

    audit, still_out, files, pages = [], [], [], []
    added_total = 0

    for strain in sorted(PUBLISHED, key=lambda s: s.lower()):
        abbr, display, stem, published, _source = PUBLISHED[strain]
        ladder, added = extend(published)
        added_total += len(added)

        for r in sorted(obs.get(strain, []), key=lambda x: x["batch"]):
            audit.append([strain, abbr, r["batch"], "%.2f" % r["value"], r["cert"],
                          r["date"], grade_of(published, r["value"]) or "OUTSIDE",
                          grade_of(ladder, r["value"]) or "OUTSIDE"])
            if grade_of(ladder, r["value"]) is None:
                still_out.append((strain, r))

        pages.append((stem, abbr, display, ladder, added))
        files.append((os.path.join(OUT, stem + ".html"), strain, abbr,
                      published, ladder, added))

    # First pass tells us which glyphs the set actually needs; the faces are cut to
    # exactly those, then every page is written with them inlined.
    draft = "".join(render(a, d, l, ad) for _s, a, d, l, ad in pages)
    seen = re.sub(r"<[^>]+>|&[a-z]+;", " ", draft.split("<style>")[0]
                  + "".join(draft.split("</style>")[1:]))
    fonts, raw_kb, sub_kb = house_fonts.font_face_css(seen)

    for (stem, abbr, display, ladder, added), (path, _s, _a, _p, _l, _ad) in zip(
            pages, files):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(abbr, display, ladder, added, fonts))

    with open(os.path.join(HERE, "exports", "PP_Potency_Grade_Audit.tsv"),
              "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["Cultivar", "Abbr", "Batch", "Total D9-THC %", "Certificate",
                    "Issue Date", "Grade under v.01", "Grade under v.02"])
        w.writerows(audit)

    print("QCSP 001 %s \u2014 %d cultivars, %d grades added, %d results checked"
          % (DOC_REVISION, len(PUBLISHED), added_total, len(audit)))
    print("Montserrat + Roboto Mono inlined: %.0f KB upstream subset to %.0f KB "
          "per document\n" % (raw_kb / 1024.0, sub_kb / 1024.0))
    print("%-22s %-4s %10s %10s  %s"
          % ("cultivar", "abbr", "v.01 floor", "v.02 floor", "grades added"))
    print("-" * 80)
    for _p, strain, abbr, published, ladder, added in files:
        print("%-22s %-4s %10.2f %10.2f  %s"
              % (strain, abbr, min(g[2] for g in published),
                 min(g[2] for g in ladder),
                 ", ".join("Grade " + a for a in added) or "\u2014"))

    recovered = [r for r in audit if r[6] == "OUTSIDE" and r[7] != "OUTSIDE"]
    print("\nResults with no grade under v.01 that now have one:")
    for r in recovered:
        print("   %-14s %-11s %6s%%  %-13s -> Grade %s"
              % (r[0], r[2], r[3], r[4], r[7]))
    if not recovered:
        print("   (none)")

    print("\nStill outside every grade: %d" % len(still_out))
    for strain, r in still_out:
        print("   %-14s %-11s %6.2f%%  %s" % (strain, r["batch"], r["value"], r["cert"]))

    unconfirmed = sorted(a for _p, _s, a, _pb, _l, _ad in files
                         if a not in TARGET_CONFIRMED)
    if unconfirmed:
        print("\nTARGET grade defaulted to Grade I, wants owner confirmation (%d):"
              "\n   %s" % (len(unconfirmed), ", ".join(unconfirmed)))

    if os.path.exists(CHROME):
        for path, _s, _a, _pb, _l, _ad in files:
            subprocess.run(
                [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                 "--no-pdf-header-footer", "--virtual-time-budget=4000",
                 "--print-to-pdf=" + path[:-5] + ".pdf", path],
                check=True, capture_output=True)
        print("\nWrote %d HTML and %d PDF into %s"
              % (len(files), len(files), os.path.relpath(OUT, HERE)))
    else:
        print("\nWrote %d HTML into %s (no Chromium; PDFs skipped)"
              % (len(files), os.path.relpath(OUT, HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
