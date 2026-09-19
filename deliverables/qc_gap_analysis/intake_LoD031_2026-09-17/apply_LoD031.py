#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Farmahem 031-3-ГС/26 — the one loss-on-drying certificate the desk was missing.

    python3 deliverables/qc_gap_analysis/intake_LoD031_2026-09-17/apply_LoD031.py [--dry-run]

The Head of QC, 17.09.2026: every certificate of quality, for every production batch, must
print a loss-on-drying value and cite the certificate behind it — from the Center for Natural
Products or from Farmahem, and where both exist, Farmahem's.

Twenty-eight certificates printed nothing for #8. A sweep of the owner's Drive for every
loss-on-drying document on file found **one** that belongs to those fourteen lots and is in no
record of the desk: `031-3-ГС/26` of 12.02.2026, Wedding Cake `WED102501` / **P060102**, one of
the 44 scans `OI-42` enumerated on 16.09.2026. Its four siblings of the same delivery —
`031-1`, `031-2`, `031-4`, `031-5` — are all cited on certificates already; only this one was
left, and the two Wedding Cake certificates were the two printing nothing.

THE GATE. Two reads of the page, recorded in `reads_LoD031.json`, both taken on 17.09.2026
from separate renderings of the scan, agreeing on the result and its uncertainty. The SHA-256
of the scan as downloaded is recorded beside them.

THE ROW. Into the P060102 block, in the shape of the register's other Farmahem loss-on-drying
rows: column I, the report number in the register's own spelling, the date of issue and
`Farmahem`. `apply_lod_source.py` is what then puts it on the two certificates — it is the
rule, and this is only the document it needed.
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
READS = os.path.join(HERE, "reads_LoD031.json")
LAB = "Farmahem"
FAM = "Farmahem — loss on drying"


def reg_value(m):
    """The result in the spelling the register's other 031- rows carry: a comma and a %.

    >>> reg_value({"results": {"8": "6,8"}})
    '6,8 %'
    """
    return "%s %%" % str(m["results"]["8"]).strip()


def key(s):
    return str(s or "").strip().upper().replace("_", "").replace("-", "").replace("/", "")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--reads", default=READS)
    a = ap.parse_args(argv[1:])
    reads = json.load(open(a.reads, encoding="utf-8"))
    for code, m in sorted(reads.items()):
        if m["read_A"] != m["read_B"]:
            print("REFUSED %s: the two reads differ — %r vs %r" % (code, m["read_A"], m["read_B"]))
            return 1

    data = json.load(open(a.src, encoding="utf-8"))
    by = {}
    for b in data["reg"]:
        for k in {key(b.get("pn")), key(b.get("cb"))} - {""}:
            by.setdefault(k, b)

    added, skipped, missing = 0, 0, []
    for code in sorted(reads):
        m = reads[code]
        block = by.get(key(m["batch_canonical"])) or by.get(key(m.get("cultivation_batch")))
        if block is None:
            missing.append((code, m["batch_canonical"]))
            continue
        if any(nkey(c.get("code")) == nkey(code) for c in block["certs"]):
            skipped += 1
            continue
        block["certs"].append({"code": code, "date": m["date_of_issue"], "lab": LAB, "fam": FAM,
                               "stab": False, "vals": {"I": reg_value(m)}, "flags": {}})
        added += 1
        print("   %-13s %s  %-9s  I %s" % (code, m["date_of_issue"], m["batch_canonical"],
                                           reg_value(m)))
    print("certificates written into the register: %d   already there: %d" % (added, skipped))
    for code, lot in missing:
        print("   NO BLOCK for %s — %s not written" % (lot, code))
    if missing:
        return 1
    if not a.dry_run and added:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
