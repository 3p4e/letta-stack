#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace GP082501/2's microbiology placeholder with the number the report prints.

Five rows carried the certificate code "Microbiology report (Dec 2025)" and the issue date
"Issued Dec 2025". That was an honest placeholder — the earlier pass could not find a
"Лабораториски број" anchor in the file — but it is not a reference, and a CoQ cannot cite
it. Re-reading the file with the search anchored to the labels a laboratory actually prints
found it on the first line of the report:

    Лабораториски бр: 1227/2193/25
    Дата на прием: 01.12.2025 год.
    Серија: GP082501/2      Примерок: Сув цвет од медицински канабис – Grape Pie, 36 g
    ...
    Дата: 05.12.2025 година

The five results were already transcribed correctly against that report; only the citation
was missing. One result is restored to the report's exact wording:

    На жолчка толерантни грам-негативни бактерии | - ≤ 10² CFU/g | < 10¹ и > 10³ CFU/g

The register had written that as "< 10 and > 10^3". The document says "< 10¹ и > 10³", and
that is what goes in. It is worth saying plainly that this result contradicts itself — a
count cannot be both below 10¹ and above 10³ — and the knowledgebase already carries an
errata notice flagging it as a defect in the scanned eCoA. Resolving it is the laboratory's
business, not the register's; the row records what the paper says and the contradiction
stays visible.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "exports", "master_coa_table.tsv")

FIELDS = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter",
          "Acceptance Criterion", "Result", "Certificate Code", "Issue Date",
          "Issuing Institution", "Drive File Link"]

OLD_CODE = "Microbiology report (Dec 2025)"
NEW_CODE = "1227/2193/25"
NEW_DATE = "05.12.2025"

BILE = "Microbiology — Bile-tolerant gram-negative bacteria"
BILE_RESULT = "<10¹ and >10³ CFU/g"


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    n = fixed_result = 0
    for r in rows:
        if (r["Certificate Code"] or "").strip() != OLD_CODE:
            continue
        r["Certificate Code"] = NEW_CODE
        r["Issue Date"] = NEW_DATE
        n += 1
        if (r["Parameter"] or "").strip() == BILE:
            r["Result"] = BILE_RESULT
            fixed_result += 1

    if not n:
        print("no placeholder rows found — already fixed?")
        return 0

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print("rows recited to %s (issued %s): %d" % (NEW_CODE, NEW_DATE, n))
    print("bile-tolerant result restored to the report's wording: %d" % fixed_result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
