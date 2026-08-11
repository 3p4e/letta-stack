#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restore the Certificate Code column to what the certificates actually print.

Seven distinct code cells carried editorial matter rather than a transcription. Four of
them appended a *guess* to a number that the certificate prints plainly, which is the one
thing the register is never allowed to do — it invents a correction and then presents it
as if it came off the paper. Each was pulled back from the ingested document text before
being touched here:

  НИК22155   HPA1024_01  "Број на главна контролна книга: НИК22155 Скопје, 24.06.2025 год."
  ППК21554   OPM1024_02  "Број на главна контролна книга: ППК21554"
  ППК52211   MB0824_05   "Број на главна контролна книга: ППК52211"
  ППК52557   OPM052501   "Број на главна контролна книга: ППК52557"

Those are the numbers on the documents. Whether the lab mistyped its own control-book
number is the lab's business and the owner's call; the register's job is to say what the
paper says. The suffixes are dropped and the numbers stand as printed.

A fifth cell carried an apology — OPM1024_01's microbiology rows were filed under the
chemistry report number 2156/2025 with a note that the microbiology reference had not been
captured. It had been: the same file prints "Лабораториски број: 407/0745/25, Дата на
прием: 29.04.2025". The rows move to their own report number.

The last two carried a sub-lot descriptor inside the code cell — "230/0393/26 (Trimiran
cvet)" and "231/0394/26 (Racno trimiran cvet)". Both descriptors are already carried by
the Parameter column on every one of those rows, so the code cell keeps only the code.

Nothing else moves. No Parameter, Acceptance Criterion, Result, Issue Date, Issuing
Institution or Drive link is touched.
"""
import csv
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "exports", "master_coa_table.tsv")

FIELDS = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter",
          "Acceptance Criterion", "Result", "Certificate Code", "Issue Date",
          "Issuing Institution", "Drive File Link"]

# old cell -> the number the document prints
RESTORE = {
    "НИК22155 (likely OCR misread of ППК25xxx)": "НИК22155",
    "ППК21554 (likely OCR misread of ППК25xxx)": "ППК21554",
    "ППК52211 (likely OCR misread of ППК25211)": "ППК52211",
    "ППК52557 (likely OCR misread)": "ППК52557",
    "2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR text)":
        "407/0745/25",
    "230/0393/26 (Trimiran cvet)": "230/0393/26",
    "231/0394/26 (Racno trimiran cvet)": "231/0394/26",
}


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    changed = Counter()
    for r in rows:
        code = (r["Certificate Code"] or "").strip()
        if code in RESTORE:
            r["Certificate Code"] = RESTORE[code]
            changed[code] += 1

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print("rows rewritten: %d of %d" % (sum(changed.values()), len(rows)))
    for old, n in sorted(changed.items(), key=lambda kv: -kv[1]):
        print("   %-3d  %-70s -> %s" % (n, old, RESTORE[old]))
    missing = [k for k in RESTORE if k not in changed]
    for k in missing:
        print("   NOT FOUND (already clean?): %s" % k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
