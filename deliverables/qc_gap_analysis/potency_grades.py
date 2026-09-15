#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The potency grades per strain — nominal, tolerance, specification window — as the
owner's potency specification of 15.09.2026 prints them.

    python3 deliverables/qc_gap_analysis/potency_grades.py     # self-test + census, writes the CSV

Source: `Potency_specifications_233.pdf` (Drive id 1NEZSRNPt5GtPvUfpi1dotAG9dkorEAGn,
created 15.09.2026 by the Head of QC; SHA-256 998daf31…), one page per strain: the
strain and its abbreviation, how many measured Total Δ9-THC results the page rests on
and their range, the number of grades, whether every result or the initial result per
batch was used, and a table of grade nominal / tolerance / specification window, followed
by the measured results as printed. "Starting nominals: QCSP 001 v.03 · Results:
CoQ_Analysis_Master_v25". The text is the PDF's own text layer (pdftotext), not OCR.

The owner asked for this information inside the workbook (15.09.2026); the `Potency
Grades` tab renders this CSV, one row per strain and grade.

Output: potency_grades_2026-09-15.csv — strain, abbr, status, results_n, results_range,
grades_n, basis, numeral, nominal, tolerance, window_low, window_high, measured (the
results as printed, space-separated). `numeral` is the specification's sequential number
within the strain (owner, 15.09.2026): assigned once by `number()` and kept on every later
run, so a specification document code never changes its meaning.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "potency_grades_2026-09-15", "Potency_specifications_233.txt")
OUT = os.path.join(HERE, "potency_grades_2026-09-15.csv")

_HEAD = re.compile(r"^(?P<strain>[A-Za-z0-9 ]+?)\s{2,}(?P<abbr>[A-Z0-9]{1,4}) · (?P<status>[A-Z]+)\s*$", re.M)
_SUMMARY = re.compile(r"^(?P<n>\d+) measured results? · (?P<lo>[\d.]+)–(?P<hi>[\d.]+) % · (?P<g>\d+) grades? · (?P<basis>.+?)\s*$", re.M)
_GRADE = re.compile(r"^\s*(?P<nom>\d+\.\d\d) %\s+± (?P<tol>\d+\.\d\d) %\s+(?P<lo>\d+\.\d\d) – (?P<hi>\d+\.\d\d) %\s*$", re.M)


def parse_page(text):
    """One strain's page -> a list of grade rows.

    >>> rows = parse_page('''PURELY PLANT · POTENCY SPECIFICATION
    ...
    ... Cash Cow                                          CC · FINISHED
    ... 4 measured results · 13.35–17.67 % · 2 grades · all results
    ...
    ... Grade nominal      Tolerance      Specification window
    ...
    ... 14.00 %            ± 1.35 %       12.65 – 15.34 %
    ...
    ... 17.00 %            ± 1.65 %       15.35 – 18.64 %
    ...
    ... Measured Total ”9-THC results
    ... 13.35 14.76 16.36 17.67
    ...
    ... Starting nominals: QCSP 001 v.03''')
    >>> len(rows), rows[0]["strain"], rows[0]["abbr"], rows[1]["nominal"], rows[1]["window_high"]
    (2, 'Cash Cow', 'CC', '17.00', '18.64')
    >>> rows[0]["measured"], rows[0]["basis"]
    ('13.35 14.76 16.36 17.67', 'all results')
    """
    h = _HEAD.search(text)
    s = _SUMMARY.search(text)
    if not h or not s:
        return []
    m = re.search(r"Measured Total .9-THC results\s*\n(?P<vals>(?:[\d. \n]+?))\n\s*\n", text)
    measured = " ".join(m.group("vals").split()) if m else ""
    rows = []
    for g in _GRADE.finditer(text):
        rows.append({"strain": h.group("strain").strip(), "abbr": h.group("abbr"), "status": h.group("status"),
                     "results_n": s.group("n"), "results_range": "%s–%s" % (s.group("lo"), s.group("hi")),
                     "grades_n": s.group("g"), "basis": s.group("basis").strip(),
                     "nominal": g.group("nom"), "tolerance": g.group("tol"),
                     "window_low": g.group("lo"), "window_high": g.group("hi"), "measured": measured})
    return rows


def build(src=SRC):
    text = open(src, encoding="utf-8").read()
    rows = []
    for page in text.split("PURELY PLANT · POTENCY SPECIFICATION")[1:]:
        rows.extend(parse_page(page))
    return rows


COLS = ["strain", "abbr", "status", "results_n", "results_range", "grades_n", "basis",
        "numeral", "nominal", "tolerance", "window_low", "window_high", "measured"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def number(rows, previous=None):
    """Give every grade its specification numeral — SEQUENTIALLY, once, for good.

    Owner, 15.09.2026: the numeral in a specification document code is the order the
    strain's specifications were created, never a rank on the potency scale. A grade
    already numbered in the previous table keeps its numeral; a grade new to a strain
    takes the strain's next free numeral, wherever its nominal sits. The first table
    (this one) was numbered from the highest nominal down, which is how the review set
    reads today; from here on nothing is renumbered.

    >>> rows = [{"abbr": "X", "nominal": "20.00"}, {"abbr": "X", "nominal": "24.00"}, {"abbr": "Y", "nominal": "8.00"}]
    >>> [r["numeral"] for r in number(rows)]
    ['II', 'I', 'I']
    >>> prev = {("X", "24.00"): "I", ("X", "20.00"): "II"}
    >>> [r["numeral"] for r in number(rows + [{"abbr": "X", "nominal": "28.00"}], prev)]
    ['II', 'I', 'I', 'III']
    """
    previous = previous or {}
    used = {}
    for (abbr, nom), num in previous.items():
        used.setdefault(abbr, set()).add(num)
    for r in rows:
        k = (r["abbr"], "%.2f" % float(r["nominal"]))
        if k in previous:
            r["numeral"] = previous[k]
    for abbr in sorted({r["abbr"] for r in rows}):
        todo = [r for r in rows if r["abbr"] == abbr and not r.get("numeral")]
        if previous and any(r.get("numeral") for r in rows if r["abbr"] == abbr):
            todo.sort(key=lambda r: float(r["nominal"]) * -1)      # appended in the order the table lists them
        else:
            todo.sort(key=lambda r: -float(r["nominal"]))          # the first numbering: highest nominal first
        for r in todo:
            n = next(x for x in ROMAN if x not in used.get(abbr, set()))
            r["numeral"] = n
            used.setdefault(abbr, set()).add(n)
    return rows


def load(path=OUT):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv):
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        return 1
    rows = build()
    # the numerals already given stand; only a grade new to a strain gets a number
    previous = {}
    if os.path.exists(OUT):
        for r in load(OUT):
            if r.get("numeral"):
                previous[(r["abbr"], "%.2f" % float(r["nominal"]))] = r["numeral"]
    number(rows, previous)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=COLS)
        wr.writeheader()
        wr.writerows(rows)
    strains = []
    for r in rows:
        if r["strain"] not in strains:
            strains.append(r["strain"])
    print("%s: %d grade row(s) over %d strain(s)" % (os.path.basename(OUT), len(rows), len(strains)))
    # the page's own grade count against the rows parsed off it
    from collections import Counter
    n = Counter(r["strain"] for r in rows)
    bad = [(s, n[s], next(r["grades_n"] for r in rows if r["strain"] == s)) for s in strains
           if str(n[s]) != next(r["grades_n"] for r in rows if r["strain"] == s)]
    print("  grade count agrees with the page on every strain" if not bad else "  DISAGREE: %s" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
