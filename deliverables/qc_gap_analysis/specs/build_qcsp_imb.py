#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QCSP 001 — the intermediate-bulk product specification, filled onto its own template.

    python3 deliverables/qc_gap_analysis/specs/build_qcsp_imb.py [--check]

The owner, 21.09.2026: *"use the template i gave you in full and dont make any changes to
the columns and make them as in the templates"*, *"the templates did not have doc code in
bottom right corner"*, *"the specification template is v.03 not v.04"*.

The earlier sheets (`QCSP_001_v04/SHEETS`) were drawn by this desk rather than filled onto
the approved design, and they differ from it in every structural way that matters: Section
01 as a label-and-value grid instead of the cultivar banner with its three tick pills,
Section 02 sub-numbered 9.1-9.7 / 10.1-10.3 / 11.1-11.4 instead of the template's grouped
families, a Section 03 the design does not have, and an assay acceptance repeating the
numeric window where the template refers to Section 01. Drive settles which is authority:
the 57-sheet PROD_SPEC folder carries a `_SUPERSEDED.md` of 20.09.2026 naming the canonical
design and the template this build fills.

WHAT IS FILLED, AND NOTHING ELSE. Every replacement below is anchored on the template's own
markup and asserted to match exactly once; a template that changes shape stops the build
rather than being silently half-filled.

    <title>            .hb-code            .pb-name            .pbp-val / .pbp-tol
    the three pills    .pcr-val x 3        .ap-date-val x 2    .foot-right (emptied)

SECTION 02 IS NOT DATA. Its twenty-eight rows and four columns are the template's and are
carried through untouched — no row is added, renumbered or reworded, and #4 keeps the
template's *Per target grade as per Section 01*.

THE WINDOWS. The Head of QC, 18.09.2026: *"update the actual product specification that we
built according to this new and latest decisions regarding ranges."* The nominal, tolerance
and window therefore come from the potency decision of 17.09.2026 — the same numbers all
172 certificates of quality print. The document keeps the version the owner named today,
v.03, and the per-sheet code keeps its `_v.01` suffix, which is what both fleets cite.
"""
import argparse
import html as H
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
TEMPLATE = os.path.join(HERE, "base", "Product_Specification_ImB.html")
OUT = os.path.join(HERE, "QCSP_001_ImB")
SHEETS = os.path.join(OUT, "SHEETS")

DOC_VERSION = "QCSP 001 v.03"          # the owner, 21.09.2026 — not v.04
SIGNED = "01.06.2026"                  # the date v.03 carries
# Head of QC, 07.10.2026: the grades are the current table, which is the 17.09.2026 decision plus WED-II
# (26.09), GRC-IV (27.09), and GRC as three ranges with GRC-III gone (07.10, KVM4 builder finished). The numeral is
# the table's, read off the code; it is not a rank by nominal (numerals are sequential by creation).
BASIS = "potency_grades_2026-09-15.csv (17.09.2026; WED-II 26.09.2026; GRC 07.10.2026)"
GRADES = os.path.join(GAP, "potency_grades_2026-09-15.csv")
ROM = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
BOX, TICK = "&#9744;", "&#9746;"


def one(hay, needle, repl, what):
    """Replace an anchor that must appear exactly once."""
    n = hay.count(needle)
    if n != 1:
        raise SystemExit("template anchor %s appears %d times, expected 1" % (what, n))
    return hay.replace(needle, repl, 1)


def esc(s):
    return H.escape(str("" if s is None else s), quote=False)


# --------------------------------------------------------------------- the record
def records():
    """One record per specification code, from the current grade table and the certificates.

    The grade (nominal, tolerance, window) is the table's row for the code's strain and numeral.
    The attributes are read off the certificates that print them, Tranche 3 first. Head of QC,
    07.10.2026: *"Don't concern yourself with tranche one and tranche 2 batches since they're
    already sent"*. So a sheet takes its attributes from its Tranche 3 lots where it has any, then
    from the lots outside the tranches, and from the issued Tranche 1/2 lots only when nothing else
    cites it. Lots of the chosen group that disagree about an attribute stop the build.
    """
    import csv
    sys.path.insert(0, os.path.join(GAP, "tracker"))
    import audit_empty_results as A
    table = {}
    with open(GRADES, encoding="utf-8") as fh:
        for g in csv.DictReader(fh):
            table[(g["abbr"], g["numeral"])] = (g["strain"], float(g["nominal"]), float(g["tolerance"]),
                                                float(g["window_low"]), float(g["window_high"]))
    tm = A.tranche_map()

    def group(c):
        for k in (c.get("pp"), c.get("cb"), (c.get("cb") or "").replace("\uff0a", "")):
            if k and k in tm:
                return {"T3": 0, "T1": 2, "T2": 2}.get(tm[k], 2)
        return 1                                  # outside every tranche

    data = json.load(open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))
    codes = {}
    for c in data["coqs"]:
        code = (c.get("spec") or "").strip()
        m = re.match(r"QCSP_001_([A-Z0-9]+)-([IVX]+)_v\.(\d+)$", code)
        if not m or c.get("withdrawn"):
            continue
        cult = m.group(1)
        if (cult, m.group(2)) not in table:
            raise SystemExit("%s: the grade table has no %s-%s" % (code, cult, m.group(2)))
        strain, nom, tol, lo, hi = table[(cult, m.group(2))]
        r = codes.setdefault(code, {"code": code, "cult": cult, "numeral": m.group(2),
                                    "strain": strain, "nominal": nom, "tol": tol,
                                    "lo": lo, "hi": hi, "by": {}, "lots": set()})
        g = r["by"].setdefault(group(c), {k: set() for k in ("pcode", "pheno", "chemo", "proc", "dominance")})
        if c.get("pcode"):
            g["pcode"].add(c["pcode"])
        sp = c.get("spc") or {}
        for k in ("pheno", "chemo", "proc", "dominance"):
            v = (sp.get(k) or "").strip()
            if v:
                g[k].add(v)
        lot = c.get("pp") or c.get("cb")
        if lot:
            r["lots"].add(lot)
    for code, r in sorted(codes.items()):
        first = min(r["by"])
        g = r.pop("by")[first]
        r["t3"] = first == 0
        for k in ("pcode", "pheno", "chemo", "proc", "dominance"):
            if len(g[k]) > 1:
                raise SystemExit("%s: its lots disagree about %s — %s" % (code, k, sorted(g[k])))
            r[k] = sorted(g[k])[0] if g[k] else ""
    return [codes[c] for c in sorted(codes)]


# ---------------------------------------------------------------------- the pills
PHENO = ('<span class="var-opt">%s Hybrid <span class="vo-dom">INDICA<span class="pn">00</span>'
         ' : SATIVA<span class="pn">00</span></span></span><span class="var-stack">'
         '<span class="var-opt">%s Indica</span><span class="var-opt">%s Sativa</span></span>'
         % (BOX, BOX, BOX))
CHEMO = ('<span class="chem-stack"><span class="var-opt">%s THC</span>'
         '<span class="var-opt">%s CBD</span></span>' % (BOX, BOX))
PROC = ('<span class="proc-stack"><span class="var-opt">%s Machine <span class="mk">Машинска</span></span>'
        '<span class="var-opt">%s Hand <span class="mk">Рачна</span></span></span>' % (BOX, BOX))


def pheno_pill(pheno, dominance, lean=False):
    """Tick one of Hybrid / Indica / Sativa, and carry a ratio only if one is stated.

    The record's dominance is sometimes a ratio (INDICA 60 : SATIVA 40) and sometimes a
    word — INDICA-DOMINANT, BALANCED, TO BE DETERMINED. A word is not a ratio: BALANCED is
    not written as 50 : 50 here, because that would be this desk asserting a number the
    record does not carry. Where no ratio is stated the Hybrid option carries no figures.
    """
    p = (pheno or "").upper()
    hy, ind, sat = (TICK if p == "HYBRID" else BOX), (TICK if p == "INDICA" else BOX), \
                   (TICK if p == "SATIVA" else BOX)
    m = re.search(r"INDICA\s*(\d+)\s*:\s*SATIVA\s*(\d+)", dominance or "", re.I)
    if not m:
        m2 = re.search(r"SATIVA\s*(\d+)\s*:\s*INDICA\s*(\d+)", dominance or "", re.I)
        dom = ('<span class="vo-dom">INDICA<span class="pn">%s</span> : SATIVA<span class="pn">%s</span></span>'
               % (m2.group(2), m2.group(1))) if m2 else ""
        # Head of QC, 07.10.2026, Tranche 3: a hybrid whose leaning is known and whose split is not says which way
        # it leans, as its certificate of quality does
        m3 = re.match(r"^\s*(INDICA|SATIVA)-DOMINANT\s*$", dominance or "", re.I)
        if not dom and m3 and lean:
            dom = '<span class="vo-dom">· %s <span class="pn">DOMINANT</span></span>' % m3.group(1).upper()
    else:
        dom = ('<span class="vo-dom">INDICA<span class="pn">%s</span> : SATIVA<span class="pn">%s</span></span>'
               % (m.group(1), m.group(2)))
    hybrid = '<span class="var-opt">%s Hybrid%s</span>' % (hy, (" " + dom) if dom else "")
    return ('%s<span class="var-stack"><span class="var-opt">%s Indica</span>'
            '<span class="var-opt">%s Sativa</span></span>' % (hybrid, ind, sat))


def chemo_pill(chemo):
    c = (chemo or "").upper()
    return ('<span class="chem-stack"><span class="var-opt">%s THC</span>'
            '<span class="var-opt">%s CBD</span></span>'
            % (TICK if c == "THC" else BOX, TICK if c == "CBD" else BOX))


def proc_pill(proc):
    p = (proc or "").upper()
    machine = TICK if "MACHINE" in p else BOX
    hand = TICK if "HAND" in p else BOX
    return ('<span class="proc-stack"><span class="var-opt">%s Machine <span class="mk">Машинска</span></span>'
            '<span class="var-opt">%s Hand <span class="mk">Рачна</span></span></span>'
            % (machine, hand))


# ---------------------------------------------------------------------- the filling
def sheet(tpl, r):
    code = "QCSP_001_%s-%s_v.01" % (r["cult"], r["numeral"])
    h = tpl
    h = one(h, "<title>Purely Plant — Product Specification — Intermediate Bulk (blank template)</title>",
            "<title>Purely Plant — Product Specification — %s (%s) — Grade %s</title>"
            % (esc(r["strain"]), esc(r["cult"]), esc(r["numeral"])), "<title>")
    h = one(h, '<div class="hb-code">QCSP 001_XX-I_v.03</div>',
            '<div class="hb-code">%s</div>' % esc(code.replace("QCSP_001_", "QCSP 001_")), ".hb-code")
    h = one(h, '<div class="pb-name">Cultivar name</div>',
            '<div class="pb-name">%s</div>' % esc(r["strain"].upper()), ".pb-name")
    h = one(h, '<span class="pbp-val">00.00%</span><span class="pbp-tol">± 0.00%</span>',
            '<span class="pbp-val">%.2f%%</span><span class="pbp-tol">± %.2f%%</span>'
            % (r["nominal"], r["tol"]), ".pbp-val/.pbp-tol")
    h = one(h, PHENO, pheno_pill(r["pheno"], r["dominance"], r.get("t3")), "Phenotype pill")
    h = one(h, CHEMO, chemo_pill(r["chemo"]), "Chemotype pill")
    h = one(h, PROC, proc_pill(r["proc"]), "Processing pill")
    h = one(h, '<span class="pcr-val">XX_THC00 : CBD1</span>',
            '<span class="pcr-val">%s</span>' % esc(r["pcode"]), "Product Code")
    h = one(h, '<span class="pcr-val">00.00 &ndash; 00.00 %</span>',
            '<span class="pcr-val">%.2f &ndash; %.2f %%</span>' % (r["lo"], r["hi"]), "Potency")
    h = one(h, '<span class="pcr-val">QCSP_001_XX-I_v.03</span>',
            '<span class="pcr-val">%s</span>' % esc(code), "Spec. doc. code")
    # both approval dates
    n = h.count('<span class="ap-date-val tpl">DD.MM.YYYY</span>')
    if n != 2:
        raise SystemExit("template has %d approval dates, expected 2" % n)
    h = h.replace('<span class="ap-date-val tpl">DD.MM.YYYY</span>',
                  '<span class="ap-date-val">%s</span>' % SIGNED)
    # the owner, 21.09.2026: no document code in the bottom right corner
    h = one(h, '<div class="foot-right">QCSP 001 v.03</div>',
            '<div class="foot-right"></div>', ".foot-right")
    # Orbitron has no Cyrillic: the Macedonian of every Orbitron label fell through to Liberation Sans in print.
    # Montserrat goes behind Orbitron, as on the iCoA since 27.09.2026 (build_t3_bundle_2026-09-26.house_stack);
    # Latin text keeps Orbitron.
    for a, b in ORBITRON_STACK:
        h = h.replace(a, b)
    rules = re.sub(r"@font-face\s*\{[^}]*\}", "", h)
    left = sorted({v for v in re.findall(r"font-family:\s*([^;}\"]+)", rules)
                   if v.strip().strip("'\"").startswith("Orbitron") and "Montserrat" not in v})
    if left:
        raise SystemExit("%s: Orbitron without Montserrat behind it (%s)" % (code, ", ".join(left)))
    return code, h


ORBITRON_STACK = (("font-family:'Orbitron','Roboto Mono',monospace", "font-family:'Orbitron','Montserrat','Roboto Mono',monospace"),
                  ("font-family:'Orbitron',sans-serif", "font-family:'Orbitron','Montserrat',sans-serif"),
                  ("font-family:'Orbitron',monospace", "font-family:'Orbitron','Montserrat',monospace"))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="build nothing, report only")
    a = ap.parse_args(argv[1:])

    tpl = open(TEMPLATE, encoding="utf-8").read()
    recs = records()
    if not a.check:
        os.makedirs(SHEETS, exist_ok=True)
    made = []
    for r in recs:
        code, h = sheet(tpl, r)
        name = "%s_%s_Grade_%s.html" % (code, r["strain"].replace(" ", "_"), r["numeral"])
        if not a.check:
            open(os.path.join(SHEETS, name), "w", encoding="utf-8").write(h)
        made.append({"code": code, "cultivar": r["cult"], "strain": r["strain"],
                     "grade": r["numeral"], "nominal": r["nominal"], "tolerance": r["tol"],
                     "window": "%.2f – %.2f %%" % (r["lo"], r["hi"]),
                     "product_code": r["pcode"], "phenotype": r["pheno"],
                     "dominance": r["dominance"], "chemotype": r["chemo"],
                     "processing": r["proc"], "lots": len(r["lots"]), "file": name})
    if not a.check:
        json.dump({"document": DOC_VERSION, "signed": SIGNED, "potency_basis": BASIS,
                   "template": "base/Product_Specification_ImB.html",
                   "sheets": made}, open(os.path.join(OUT, "INDEX.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print("%s — %d sheets on the template, %d cultivars"
          % (DOC_VERSION, len(made), len({m["cultivar"] for m in made})))
    noratio = [m["code"] for m in made if m["phenotype"].upper() == "HYBRID"
               and not re.search(r"\d+\s*:\s*\w*\s*\d+", m["dominance"] or "")]
    if noratio:
        print("hybrid with no stated ratio, so none printed: %d" % len(noratio))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
