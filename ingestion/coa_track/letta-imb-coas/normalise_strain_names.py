#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Settle the cultivar spellings the certificates disagree about.

reconcile_master_table.py deliberately left these alone: it collapsed spacing-only
variants and stopped there, on the grounds that choosing between genuinely different
spellings is the owner's call rather than a script's. The owner has now made that call,
so this applies it.

Cap Junky is one cultivar under three spellings, and the certificates drifted over time:

    Cup Junky    CJ1024, CJ052501/1, CJ052501/2, CJ072501      earliest
    Cap Junkie   CJ062501/1, CJ062501/2                        middle
    Cap Junky    CJ082501/1, CJ082501/2, CJ092501              most recent

The name is a breeder credit — Capulator crossed with Seed Junky Genetics — so "Cap" and
"Junky" are both load-bearing. "Cap Junkie" gets the first half right, "Cup Junky" the
second. Only "Cap Junky" is the cultivar's actual name, and it is what the most recent
certificates print, which suggests the laboratories were corrected at some point.

The control sheets say "Cap Junkie" throughout — all nine batches in the Tranches Overview
and both List of COAs sheets. Those are the owner's files and are not edited here; they
need the same correction on their side, and until then the cross-check will report the
difference rather than hide it.

This changes the Strain column only. It is identity, not a transcribed measurement — the
same class of edit reconcile_master_table.py already makes — so no Parameter, Acceptance
Criterion, Result, Certificate Code, Issue Date, Issuing Institution or Drive link moves.
What each certificate physically prints is unchanged and still recoverable from the
document itself.
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

CANONICAL = {
    "cup junky": "Cap Junky",
    "cap junkie": "Cap Junky",
    "capjunkie": "Cap Junky",
    "cup junkie": "Cap Junky",
    "cap junky": "Cap Junky",
}


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    changed = Counter()
    batches = {}
    for r in rows:
        s = (r["Strain"] or "").strip()
        want = CANONICAL.get(s.lower().rstrip("*").strip())
        if want and want != s:
            changed[s] += 1
            batches.setdefault(s, set()).add((r["Cultivation Batch"] or "").strip())
            r["Strain"] = want

    if not changed:
        print("nothing to change — already canonical")
        return 0

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print("rows restrained to the cultivar's own name: %d" % sum(changed.values()))
    for old, n in sorted(changed.items(), key=lambda kv: -kv[1]):
        print("   %-12s -> Cap Junky   %3d rows   %s"
              % (old, n, ", ".join(sorted(batches[old]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
