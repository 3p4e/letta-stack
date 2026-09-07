#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The delivery tranches, as the owner's "Tranches Overview" sheet lists them.

Three deliveries — 31.07.2026, 14.08.2026 and 28.08.2026 — of 21, 29 and 28 cultivation
batches. This is the population a CoQ has to exist for: product that has left the site.
The sheet is the customer-facing declaration, so it carries the batch as ImB knows it, the
potency bracket it was sold under and the declared per-batch potency; it does not carry P
lots, and its batch codes drop the asterisk the Head of QC's own list writes.

Kept verbatim in tranches_raw_2026-09-07.csv, per-row totals reconciled against the sheet's
own ВКУПНО lines (1,480.66 / 2,747.87 / 2,705.73 kg). Nothing here is corrected: where the
sheet and the desk disagree, the disagreement is the finding.
"""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "tranches_raw_2026-09-07.csv")


def bracket(text):
    """(low, high) of a printed potency bracket. '≥ 25%' has no printed upper bound."""
    t = str(text).replace("≥", ">=").replace("–", "-").replace("%", "").strip()
    if t.startswith(">="):
        return float(t[2:]), None
    lo, hi = t.split("-")
    return float(lo), float(hi)


def in_bracket(pct, text):
    lo, hi = bracket(text)
    return lo <= float(pct) and (hi is None or float(pct) <= hi)


def load(path=None):
    rows = []
    for r in csv.DictReader(open(path or DEFAULT, encoding="utf-8-sig")):
        r["tranche"] = int(r["tranche"])
        r["thc_pct"] = float(r["thc_pct"])
        r["volume_kg"] = float(r["volume_kg"])
        rows.append(r)
    return rows


if __name__ == "__main__":
    import collections
    rows = load()
    n = collections.Counter(r["tranche"] for r in rows)
    kg = collections.defaultdict(float)
    for r in rows:
        kg[r["tranche"]] += r["volume_kg"]
    for t in sorted(n):
        print(f"tranche {t}: {n[t]} batches, {kg[t]:,.2f} kg")
    bad = [r for r in rows if not in_bracket(r["thc_pct"], r["thc_bracket"])]
    print(f"declared potency outside its own printed bracket: {len(bad)}")
