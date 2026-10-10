#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every certificate's potency grade, nominal, tolerance and window from the owner's specification.

    python3 deliverables/qc_gap_analysis/apply_potency_grades.py [--dry-run]

The Head of QC, 17.09.2026, with `Potency_specifications_25.pdf` (specs/, generated 17.09.2026
from the potency specification of 15.09.2026): "the potency and specification nominals and
ranges in accordance with the new specification distribution and grades — to all CoQs."

The PDF was parsed grade by grade (`specs/potency_specifications_25_2026-09-17.json`) and set
against the desk's table, `potency_grades_2026-09-15.csv`. Twenty-two of its twenty-four
strains matched to the digit. Two did not: Amnesia Core Cut, where the desk had carried a
tolerance of ± 0.95 (window 11.05 – 12.94) against the specification's ± 1.20 (10.80 – 13.19);
and Wedding Cake, absent from the desk's table, which the specification grades at 26.00 ±
2.60 (23.40 – 28.59). The table is corrected; this re-grades every certificate from it, through
the same `potency_grading` the schedule uses — the grade is the window the printed Total THC
result falls in, the product code and the specification document code follow from it, the
numeral is the table's — and reports every certificate whose grade, code or window moved.
"""
import argparse, io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import potency_grading as PGR                                          # noqa: E402
SRC = os.path.join(HERE, "coq_artifact_data.json")
ATTR = os.path.join(HERE, "spec_attributes_2026-09-10.csv")


def attributes():
    """Specification code -> the product attributes its issued document prints, and the same
    keyed by strain abbreviation (the attributes are the strain's, the same on every grade —
    the exporter's rule since 15.09.2026)."""
    import csv, re
    by_code, by_abbr = {}, {}
    if os.path.exists(ATTR):
        for r in csv.DictReader(io.open(ATTR, encoding="utf-8")):
            by_code[r["code"].strip()] = r
            m = re.match(r"QCSP_001_([A-Z0-9]+)-", r["code"].strip())
            if m:
                by_abbr.setdefault(m.group(1), r)
    return by_code, by_abbr


def issued_potency(row):
    """What the issued specification document behind a spec_attributes row prints for potency —
    product code and nominal ± tolerance — read off the PDF where it is on disk, else None."""
    import re, glob
    f = (row or {}).get("file") or ""
    if not f:
        return None
    hits = glob.glob(os.path.join(os.path.dirname(os.path.dirname(HERE)), "**", os.path.basename(f)), recursive=True)
    if not hits:
        return None
    try:
        import pymupdf
        t = re.sub(r"\s+", " ", pymupdf.open(hits[0])[0].get_text())
        m = re.search(r"([A-Z0-9]+_THC[\d.]+\s*:\s*CBD1)\s*([\d.]+%\s*±\s*[\d.]+%)", t)
        return (m.group(1), m.group(2)) if m else None
    except Exception:
        return None


def apply(data, dry=False):
    changed, ungraded = [], []
    by_code, by_abbr = attributes()
    for c in data["coqs"]:
        r4 = next((r for r in c["rows"] if r["no"] == "4"), None)
        if not r4:
            continue
        g = PGR.grading(c.get("cb") or c.get("pp") or "", c.get("strain") or "", r4.get("res") or "")
        if not g.get("grade"):
            if g.get("thc") is not None:
                ungraded.append((c["regcode"], c.get("strain"), g["thc"], g.get("note")))
            continue
        crit = "%s  (grade %s, nominal %.2f ± %.2f)" % (g["window"], g["roman"], g["nominal"], g["tol"])
        before = (c.get("grade"), c.get("pcode"), c.get("spec"), r4.get("crit"))
        after = (g["roman"], g["product_code"], g["spec_code"], crit)
        stale_status = (c.get("spec_status") == "for review — new" and by_code.get(g["spec_code"]))
        if before == after and not stale_status and (isinstance(c.get("spc"), dict) or not (by_code.get(g["spec_code"]) or by_abbr.get(g["abbr"]))):
            continue
        changed.append((c["regcode"], c.get("strain"), g["thc"], before, "->", after))
        if not dry:
            status = g["spec_status"]
            if status == "for review — new" and by_code.get(g["spec_code"]):
                # the code was issued before (a document in spec_attributes) though no lot of the
                # register carried it: the status records what that document printed (15.09 rule)
                was = issued_potency(by_code[g["spec_code"]])
                status = "for review — replaces the issued %s (was %s); now %s %s" % (
                    g["spec_code"], ("%s, %s" % was) if was else "issued under this code", g["product_code"], g["window"])
            c["grade"], c["cls"], c["pcode"], c["spec"], c["spec_status"] = g["roman"], int(round(g["nominal"])), g["product_code"], g["spec_code"], status
            r4["crit"] = crit
            if isinstance(c.get("spc"), dict):
                c["spc"]["code"] = g["spec_code"]
            else:
                # a certificate graded for the first time takes its product attributes from the
                # strain's issued specification, as the exporter would have (Wedding Cake: the
                # issued QCSP_001_WED-I…IV documents are in spec_attributes_2026-09-10.csv)
                r = by_code.get(g["spec_code"]) or by_abbr.get(g["abbr"])
                if r:
                    c["spc"] = {"code": g["spec_code"], "attributes_from": r["code"], "pheno": r["phenotype"],
                                "chemo": r["chemotype"], "proc": r["processing"], "dominance": r["dominance"],
                                "dom": r["dom"], "pack": r["packaging"]}
    return changed, ungraded


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])
    data = json.load(io.open(SRC, encoding="utf-8"))
    changed, ungraded = apply(data, dry=a.dry_run)
    print("certificates re-graded: %d" % len(changed))
    for x in changed: print("   ", x)
    print("results in no window of the specification (unchanged, for the Head of QC): %d" % len(ungraded))
    for x in ungraded: print("   ", x)
    if not a.dry_run and changed:
        with io.open(SRC, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)   # the layout every other writer uses
        print("written:", os.path.relpath(SRC))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
