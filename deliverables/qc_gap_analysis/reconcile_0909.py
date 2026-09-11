#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The desk against the owner's 09.09.2026 pass, cell by cell.

    python3 deliverables/qc_gap_analysis/reconcile_0909.py        # self-test + summary

Two records describe the same 600 determinations: the desk's own (built from the
release register and the page reads, and exported to `coq_artifact_data.json`)
and the owner's `Cell Resolution 09.09`, which read the 387 certificates in
`eCoA_DATABASE` name for name. This module puts them side by side and says what
each cell is:

  fill       the desk holds nothing and the pass holds a printable result
  blocked    the only document is an in-house iCoA that has not been issued
  uncited    the only document carries no document code at all
  ambiguous  the pass holds a list of values it does not label — see
             cell_resolution.py rule 3
  none       neither holds anything
  agree      both hold a value and they are the same value
  order      both hold the same values against different analytes
  values     both hold a value and the values differ

`order` and `values` are the findings: two records of one certificate that do not
say the same thing. Neither is resolved here. The desk is not overruled by this
pass — the pass itself compared 550 cells against page transcriptions and found
no error in the tracker — so a disagreement is written down and left for a
person, which is what the rest of this folder does with every other one.

Comparison is on what the two records MEAN, not on how they spell it: one writes
`1.6×10⁴` and the other `1,6 x 10⁴ CFU/g`, one `N.D.` and the other `н.д.`, one
`Одговара (absent)` and the other `Одговара /25 g`. Only a difference that
survives that is a difference.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.join(HERE, "coq_artifact_data.json")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import cell_resolution as CR                                        # noqa: E402

# The certificate prints these one line per analyte; the desk numbers those lines.
SUBS = {"9": ["9.1", "9.2", "9.3", "9.4", "9.5"],
        "10": ["10.1", "10.2", "10.3"],
        "11": ["11.1", "11.2", "11.3", "11.4"]}
_SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}


def same(a, b):
    """Do these two spellings of a result mean the same thing?

    >>> same("1.6×10⁴", "1,6 x 10⁴ CFU/g")
    True
    >>> same("N.D.", "н.д. mg/kg")
    True
    >>> same("Одговара (absent)", "Одговара /25 g")
    True
    >>> same("Odgovara (Absent)", "Отсутна/g")
    True
    >>> same("< 10^2 and > 10", "< 10² и > 10 CFU/g")
    True
    >>> same("0.1", "0.10")
    True
    >>> same("0.047", "н.д.")
    False
    >>> same("<10", "700")
    False
    """
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return True
    # 0.1 and 0.10 are one number written twice, not two results
    try:
        return float(na) == float(nb)
    except ValueError:
        return False


def _norm(s):
    """A result reduced to what it asserts.

    >>> _norm("2.8×10⁴ CFU/g")
    '2.8x10^4'
    >>> _norm("<LOQ**  %w/w")
    '<loq'
    """
    s = (s or "").strip().lower()
    s = "".join(_SUP.get(ch, ch) for ch in s)
    s = re.sub(r"\*+|ᴿ|\(l\)", "", s)
    s = re.sub(r"cfu\s*/\s*g|mg\s*/\s*kg|µg\s*/\s*kg|%\s*w\s*/\s*w|%", " ", s)
    # absence and non-detection, in either alphabet and either wording
    s = re.sub(r"одговара|odgovara|отсутна|otsutna|absent|complies", " ABSENT ", s)
    s = re.sub(r"\bн\s*\.?\s*д\s*\.?|\bn\s*\.?\s*d\s*\.?(?![a-z])", " ND ", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("×", "x").replace("·", "x").replace(" и ", " and ")
    s = re.sub(r"10\s*\^?\s*(\d)", r"10^\1", s)
    s = re.sub(r"(?<=\d),(?=\d)", ".", s)
    s = re.sub(r"/\s*\d*\s*g\b", " ", s)
    s = re.sub(r"[^0-9a-z<>.^x+ANDBSENT-]+", "", s.replace(" ", ""))
    return s


def desk_rows(path=DESK):
    """The desk's initial-release CoQ, by batch key."""
    d = json.load(open(path, encoding="utf-8"))
    return {CR.batch_key(c["cb"]): c
            for c in d["coqs"] if c["t"] == "initial release"}


def classify(row, coq):
    """One sheet row against the desk's CoQ for that batch — (state, detail).

    ``coq`` is None when the desk carries no initial-release CoQ for the batch.
    """
    no = CR.det_no(row["Determination"])
    # The sheet's Identification C cell is not a result: it names where identity
    # comes from ("identity by the HPLC cannabinoid profile on this
    # certificate"), which is the same thing the desk's standing conformity
    # sentence says in the form the certificate prints. Comparing the two as
    # values would report nineteen disagreements that are one convention.
    if no == "3" and row["What the document prints"].strip().lower().startswith("identity by"):
        return "basis note", {}
    if coq is None:
        return "no desk lot", {}
    lines = [r for r in coq["rows"]
             if r["no"].split(".")[0] == no and r["no"] not in ("9.6", "9.7")]
    if not lines:
        return "no desk lot", {}
    held = [r for r in lines if (r["res"] or "—") != "—"]
    printed = CR.pieces(row["What the document prints"])
    if not held:
        state, value = CR.resolve(row)
        return (state if state != "fill" else "fill"), {"value": value}
    if len(held) == len(lines) == len(printed):
        if all(same(r["res"], p) for r, p in zip(lines, printed)):
            return "agree", {}
        if sorted(_norm(r["res"]) for r in lines) == sorted(_norm(p) for p in printed):
            return "order", {"desk": [r["res"] for r in lines], "pass": printed}
        return "values", {"desk": [r["res"] for r in lines], "pass": printed}
    if len(held) == len(lines) == 1 and len(printed) == 1:
        return ("agree", {}) if same(held[0]["res"], printed[0]) else \
            ("values", {"desk": [held[0]["res"]], "pass": printed})
    return "not comparable", {}


def compare(cells=CR.SRC, path=DESK):
    """Every cell of the sheet, classified. Returns a list of (row, state, detail)."""
    desk = desk_rows(path)
    out = []
    for r in CR.load(cells):
        out.append((r, *classify(r, desk.get(CR.batch_key(r["Batch"])))))
    return out


def census(cells=CR.SRC, path=DESK):
    from collections import Counter
    return Counter(s for _, s, _ in compare(cells, path))


def findings(cells=CR.SRC, path=DESK):
    """Only the cells where the two records disagree."""
    return [(r, s, d) for r, s, d in compare(cells, path) if s in ("order", "values")]


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    for k, v in sorted(census().items(), key=lambda x: -x[1]):
        print("  %-14s %3d" % (k, v))
    print()
    for r, s, d in findings():
        print("  %-13s #%-3s %-18s %s" % (r["Batch"], CR.det_no(r["Determination"]),
                                          r["Document to cite"][:18], s.upper()))
        print("      desk : %s" % d["desk"])
        print("      09.09: %s" % d["pass"])
    sys.exit(1 if fail else 0)
