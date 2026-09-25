#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Farmahem 031 cannabinoid results reach the release certificates that cite them.

    python3 deliverables/qc_gap_analysis/apply_031_assay.py [--dry-run]

The Head of QC, 18.09.2026: "CoQ analysis Master excel must have them ... you had
everything before." He is right, and the defect is narrower than the desk had it.

Three release certificates already CITE their Farmahem cannabinoid certificate — for
Identification C, and on P060112 for Total CBD and Total CBN as well — while the assay
cell beside them prints nothing. The figure is on the same page of the same certificate,
in the same table, one row below the two the certificate already prints.

    031-2-К/26  PUM102501  P060112  Total Δ9-THC 15.63 (U 0.96)  CBD <LOQ**  CBN <LOQ**
    031-5-К/26  ACC102501  P060122  Total Δ9-THC 12.91 (U 0.79)  CBD <LOQ**  CBN <LOQ**
    031-4-К/26  CF102501   P060132  Total Δ9-THC  9.83 (U 0.60)  CBD <LOQ**  CBN <LOQ**

All three received 30.01.2026, analysed 09.02.2026, issued 10.02.2026, HPLC/DAD by
ИР 7.2.1-47К (в.1), accredited to MKC EN ISO 17025:2018.

TWO INDEPENDENT READS, as every laboratory value on these certificates requires: the
Head of QC's own resolution pass of 09.09.2026 (cell_resolution_2026-09-09.tsv) and a
read of the scanned page made on 18.09.2026. They agree figure for figure, including the
uncertainties, so the values are printed.

**P060112 is not graded here and its assay is not printed.** 15.63 % sits above the only
grade the potency decision of 17.09.2026 gives Pure Michigen — 14.00 % ± 1.40, window
12.60 – 15.39 % — by 0.24. Printing a result that fails its specification on a
certificate whose Section 04 declares conformity is not a thing this script decides. Its
retest, CoQ-PP_26-132, reads 13.95 % and sits inside. The lot is left as it stands and
the question goes to the Head of QC.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "coq_artifact_data.json")
SPEC = os.path.join(HERE, "specs", "potency_specifications_25_2026-09-17.json")
ROMAN = ["", "I", "II", "III", "IV", "V", "VI"]

# certificate -> (lot, cultivar, document, issued, THC, CBD, CBN)
APPLY = {
    "CoQ-PP_26-048": ("P060122", "ACC", "031-5-К/26", "10.02.2026", "12.91", "< LOQ** %w/w", "< LOQ** %w/w"),
    "CoQ-PP_26-049": ("P060132", "CF",  "031-4-К/26", "10.02.2026", "9.83",  "< LOQ** %w/w", "< LOQ** %w/w"),
}
HELD = {"CoQ-PP_26-047": ("P060112", "PUM", "031-2-К/26", "10.02.2026", "15.63")}


def window(spec, cultivar, value):
    """(numeral, nominal, tolerance, low, high) of the grade that contains value."""
    grades = sorted(spec[cultivar]["grades"], key=lambda g: -g[0])
    for i, (nom, tol, lo, hi) in enumerate(grades):
        if lo - 0.005 <= value <= hi + 0.005:
            return ROMAN[i + 1], nom, tol, lo, hi
    return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    data = json.load(open(ART, encoding="utf-8"))
    spec = json.load(open(SPEC, encoding="utf-8"))
    by = {c.get("regcode"): c for c in data["coqs"] if c.get("regcode")}

    touched, already, notes = 0, 0, []
    for code, (lot, cult, doc, issued, thc, cbd, cbn) in APPLY.items():
        c = by.get(code)
        if c is None:
            raise SystemExit("%s is not in the register" % code)
        if (c.get("pp") or c.get("cb")) != lot:
            raise SystemExit("%s is %s, not %s — the register has moved under this script"
                             % (code, c.get("pp") or c.get("cb"), lot))
        rows = {str(r["no"]): r for r in c["rows"]}
        if rows["4"].get("res") not in ("—", "", None):
            already += 1
            continue
        w = window(spec, cult, float(thc))
        if not w:
            raise SystemExit("%s: %s %% is in no grade of the potency decision" % (code, thc))
        numeral, nom, tol, lo, hi = w
        rows["4"].update({
            "res": thc, "doc": doc, "dd": issued, "lab": "Farmahem",
            "fam": "Farmahem — cannabinoids", "st": "covered",
            "crit": "%.2f – %.2f %%  (grade %s, nominal %.2f ± %.2f)"
                    % (lo, hi, numeral, nom, tol)})
        for no, val in (("5", cbd), ("6", cbn)):
            if rows[no].get("res") in ("—", "", None):
                rows[no].update({"res": val, "doc": doc, "dd": issued, "lab": "Farmahem",
                                 "fam": "Farmahem — cannabinoids", "st": "covered"})
        c["grade"] = numeral
        c["spec"] = "QCSP_001_%s-%s_v.01" % (cult, numeral)
        c["pcode"] = "%s_THC%d : CBD1" % (cult, int(round(nom)))
        touched += 1
        notes.append("%s  %s  %s %% from %s of %s  -> grade %s (%.2f – %.2f %%)"
                     % (code, lot, thc, doc, issued, numeral, lo, hi))

    for code, (lot, cult, doc, issued, thc) in HELD.items():
        grades = sorted(spec[cult]["grades"], key=lambda g: -g[0])
        notes.append("%s  %s  %s %% from %s of %s  -> HELD: above the only %s grade "
                     "(%.2f – %.2f %%); its retest reads 13.95 %%"
                     % (code, lot, thc, doc, issued, cult, grades[0][2], grades[0][3]))

    for n in notes:
        print("   " + n)
    print("assays applied: %d   already applied: %d   held for the Head of QC: %d"
          % (touched, already, len(HELD)))
    if touched and not a.dry_run:
        with open(ART, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written: %s" % os.path.relpath(ART, os.path.dirname(HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
