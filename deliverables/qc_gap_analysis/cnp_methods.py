#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which pharmacopoeial method each CNP certificate reports the cannabinoid assay and
loss on drying by — DAB or Ph. Eur. — read off the certificate's own method line.

    python3 deliverables/qc_gap_analysis/cnp_methods.py        # self-test + census, writes the CSV

Owner, 15.09.2026: CNP (UKIM Faculty of Pharmacy, Center for Natural Products) ran
the cannabinoid assay by the DAB monograph until it accredited the Ph. Eur.
Cannabis flos (3028) method, and the certificate of quality's method reference has
to say which one the cited certificate used; loss on drying is on the same
certificates and follows them.

What the certificates say (ingestion/ragflow/cache/all_cert_texts_2026-08-30.json,
the certificate text the corpus holds): every ППК certificate from ППК25050
(26.02.2025) to ППК26069 (11.05.2026) prints "Метод: … содржина на канабиноиди
(2.2.29) … губиток при сушење (2.2.32) според монографија на германската
фармакопеја (DAB*) — DAB, Deutsches Arzneibuch 2018"; every one from ППК26110
(30.06.2026) on prints "согласно монографијата (07/2024:3028) во Европската
фармакопеја (Ph. Eur. 11.0)", with identification (2.8.23) and foreign matter
(2.8.2) added to its scope. Nothing between 11.05 and 30.06.2026 is on file, so
the switch is dated by the certificates and not by an accreditation letter the
desk does not hold.

Output: cnp_methods_2026-09-15.csv — code, date, method (DAB | PhEur), the
certificate's method line as printed.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, "ingestion", "ragflow", "cache", "all_cert_texts_2026-08-30.json")
OUT = os.path.join(HERE, "cnp_methods_2026-09-15.csv")

# The method reference a certificate of quality prints for a determination the
# cited CNP certificate performed by the DAB monograph. The specification's own
# line (Ph. Eur. 2.2.29 / 2.2.32) stands for everything else.
DAB_METHOD = {
    "3": "HPLC — DAB 2018 monograph Cannabis flos, 2.2.29 (CNP, before its Ph. Eur. 3028 accreditation)",
    "4": "HPLC — DAB 2018 monograph Cannabis flos, 2.2.29 (CNP, before its Ph. Eur. 3028 accreditation)",
    "5": "HPLC — DAB 2018 monograph Cannabis flos, 2.2.29 · CBD + CBDA x 0.877 (CNP, before its Ph. Eur. 3028 accreditation)",
    "6": "HPLC — DAB 2018 monograph Cannabis flos, 2.2.29 · CBN + CBNA x 0.876 (CNP, before its Ph. Eur. 3028 accreditation)",
    "8": "DAB 2018 monograph Cannabis flos, 2.2.32 — loss on drying (CNP, before its Ph. Eur. 3028 accreditation)",
}


def classify(text):
    """DAB, PhEur or '' from a certificate's method line.

    >>> classify("Метод: HPLC … според монографија на германската фармакопеја (DAB*)")
    'DAB'
    >>> classify("согласно монографијата (07/2024:3028) во Европската фармакопеја (Ph. Eur. 11.0)")
    'PhEur'
    >>> classify("nothing about a pharmacopoeia")
    ''
    """
    if re.search(r"\bDAB\b|Deutsches Arzneibuch|германск", text, re.I):
        return "DAB"
    if re.search(r"3028|Ph\.? ?Eur|Европск", text, re.I):
        return "PhEur"
    return ""


def method_line(text):
    m = re.search(r"Метод:\s*(.{0,220}?)\s*Цел:", re.sub(r"\s+", " ", text))
    return m.group(1).strip() if m else ""


def build(cache=CACHE):
    rows = []
    for e in json.load(open(cache, encoding="utf-8")):
        m = e.get("meta") or {}
        if m.get("lab") != "CNP":
            continue
        line = method_line(e.get("text") or "")
        rows.append({"code": (m.get("cert_code") or "").strip(), "date": m.get("date_of_issue") or "",
                     "method": classify(line or e.get("text") or ""), "method_line": line})
    rows.sort(key=lambda r: (r["date"][6:] + r["date"][3:5] + r["date"][:2], r["code"]))
    return rows


_MAP = None


def method_of(code):
    """'DAB', 'PhEur' or '' for a CNP certificate code, from the written CSV.

    >>> method_of("ППК25052"), method_of("ППК26114"), method_of("197-1-К/26")
    ('DAB', 'PhEur', '')
    """
    global _MAP
    if _MAP is None:
        _MAP = {}
        if os.path.exists(OUT):
            with open(OUT, encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    _MAP[r["code"].strip()] = r["method"]
    return _MAP.get(str(code or "").strip().replace(" ", ""), "")


def main(argv):
    rows = build()
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=["code", "date", "method", "method_line"])
        wr.writeheader()
        wr.writerows(rows)
    global _MAP
    _MAP = None
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    from collections import Counter
    c = Counter(r["method"] for r in rows)
    print("%s: %d CNP certificate(s): %s" % (os.path.basename(OUT), len(rows), dict(c)))
    dab = [r for r in rows if r["method"] == "DAB"]
    ph = [r for r in rows if r["method"] == "PhEur"]
    if dab:
        print("  DAB   %s (%s) … %s (%s)" % (dab[0]["code"], dab[0]["date"], dab[-1]["code"], dab[-1]["date"]))
    if ph:
        print("  PhEur %s (%s) … %s (%s)" % (ph[0]["code"], ph[0]["date"], ph[-1]["code"], ph[-1]["date"]))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
