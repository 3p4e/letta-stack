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


def apply(data, dry=False):
    changed, ungraded = [], []
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
        if before == after:
            continue
        changed.append((c["regcode"], c.get("strain"), g["thc"], before, "->", after))
        if not dry:
            c["grade"], c["cls"], c["pcode"], c["spec"], c["spec_status"] = g["roman"], int(round(g["nominal"])), g["product_code"], g["spec_code"], g["spec_status"]
            r4["crit"] = crit
            if isinstance(c.get("spc"), dict):
                c["spc"]["code"] = g["spec_code"]
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
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", os.path.relpath(SRC))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
