#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three register cells the page disagrees with, read on 17.09.2026.

    python3 deliverables/qc_gap_analysis/intake_release_round_2026-09-17/apply_release_reads.py [--dry-run]

The Head of QC asked on 17.09.2026 for P050022's #9 (TAMC and the bile-tolerant count) and #11
(heavy metals) to be checked against the eCoAs. Both release documents were read at full
resolution, twice, and `reads_release_round.json` records them. They confirm the register on
every determination but three cells:

* `471-0862-25` (22.05.2025) — the register's TYMC cell reads a bare `10`; **the page prints
  `< 10 CFU/g`.**
* `2471/2025` (30.05.2025) — the register's row carries **no aflatoxin column at all**, while
  the page reports Вкупни афлатоксини **`< 2` µg/kg** against a maximum of 4.
* `2471/2025` — the register's pesticide cell reads `< LOQ`; **the page prints `н.д.` against
  every residue on the list**, and declares conformity with Ph. Eur. 2.8.13.

Nothing else moved. The heavy metals on 2471/2025 are `н.д.` for lead, mercury, arsenic and
cadmium, which is exactly what the Head of QC described — "in the eCOA for heavy metals all
parameters are ND" — and the register already held them that way; what was wrong was which
document the certificate cited, and that is `apply_release_round.py`.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(GAP, "tracker"))
from tracker_data import nkey                                          # noqa: E402

SRC = os.path.join(GAP, "coq_artifact_data.json")
READS = os.path.join(HERE, "reads_release_round.json")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--reads", default=READS)
    a = ap.parse_args(argv[1:])
    reads = json.load(open(a.reads, encoding="utf-8"))
    data = json.load(open(a.src, encoding="utf-8"))
    n, skipped, missing = 0, 0, []
    for code, m in sorted(reads.items()):
        fixes = m.get("register_correction") or {}
        if not fixes:
            continue
        rows = [c for b in data["reg"] for c in (b.get("certs") or [])
                if nkey(c.get("code")) == nkey(code)]
        if not rows:
            missing.append(code)
            continue
        for cert in rows:
            vals = cert.setdefault("vals", {})
            for col, (was, now) in sorted(fixes.items()):
                have = vals.get(col)
                if have == now:
                    skipped += 1
                    continue
                if was is not None and have != was:
                    print("   %s %s: register holds %r, the read expected %r — NOT changed"
                          % (code, col, have, was))
                    continue
                vals[col] = now
                n += 1
                print("   %-13s %s  %r -> %r" % (code, col, have, now))
    print("register cells corrected from the page: %d   already right: %d" % (n, skipped))
    for code in missing:
        print("   NO ROW for %s" % code)
    if missing:
        return 1
    if not a.dry_run and n:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
