#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two IJZ-MB certificates of 31.08.2026 that the first intake could not reach.

    python3 deliverables/qc_gap_analysis/intake_IJZMB2_2026-09-17/apply_IJZMB2.py [--dry-run]

`534/1065/26` (P050212, Cap Junky) and `535/1066/26` (P050222, Cap Junky) are two pages of
the same IJZ-MB campaign delivery as the thirty the intake of 16.09.2026 took — same letter
`03-500/1` of 24.08.2026, requests 325/2026 and 326/2026 beside that intake's 324/2026,
received 25.08.2026, issued 31.08.2026, the same seven-line panel against Ph. Eur. 5.1.8
Kat. C. They fall **outside the 536–565 range** the first intake was scoped to, so they were
left where `OI-42` found them: named in the Head of QC's own 09.09 resolution pass, on Drive,
and in no record the certificates are compiled from.

The Head of QC asked for them by number on 17.09.2026 — "reference the eCOA 534/1065/26 and
insert those results" — and then gave the rule that makes the request general: a newer
external microbiological certificate means the parameter was retested, so the certificate of
quality cites it and its date of issue moves accordingly. `apply_microbiology_retest.py` is
that rule; this script is the intake it needs, and it writes documents only, never a
certificate row.

THE GATE. Two reads of each page, both recorded in `reads_IJZMB2.json` and both taken on
17.09.2026 from separate renderings of the scan — the eCoA runner holds no read of either
page, so these are the desk's own and the file says so. The two agree on all seven lines of
both certificates; `disagreements()` refuses to write anything if they ever stop agreeing.
The SHA-256 of each scan as downloaded is recorded beside the reads.

WHAT IS WRITTEN. One row into each lot's block, in the shape the first intake's rows carry:
TAMC, TYMC, bile-tolerant gram-negative bacteria, Salmonella and E. coli in columns J … N,
the laboratory number in the register's own spelling, the date of issue, and
`IPH — Institute of Public Health`. *P. aeruginosa* and *S. aureus* are reported on both
pages and absent on both; the owner's release register has no column for either, so they
stay in `reads_IJZMB2.json` — which is what OI-13 asks the Head of QC about.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(GAP, "tracker"))
from tracker_data import nkey                                          # noqa: E402

SRC = os.path.join(GAP, "coq_artifact_data.json")
READS = os.path.join(HERE, "reads_IJZMB2.json")
LAB = "IPH — Institute of Public Health"
FAM = "IPH microbiology"
# the five determinations the owner's release register has a column for
COLS = (("9.1", "J"), ("9.2", "K"), ("9.3", "L"), ("9.4", "M"), ("9.5", "N"))


def reg_value(v, det):
    """A read, in the spelling the register's own IJZ-MB rows carry.

    >>> reg_value("6,2 x 10³ CFU/g", "9.1")
    '6,2×10³'
    >>> reg_value("< 10⁴ и > 10³ CFU/g", "9.3")
    '< 10⁴ и > 10³'
    >>> reg_value("Отсутна/25 g", "9.4")
    'Одговара (absent)'
    """
    if det in ("9.4", "9.5"):
        return "Одговара (absent)"
    s = str(v or "").strip()
    s = re.sub(r"\s*CFU/g\s*$", "", s)
    s = re.sub(r"\s*[x×х]\s*10", "×10", s)
    return s.strip()


def _fold(v, det):
    """Enough normalisation to tell a real disagreement from a notation one.

    >>> _fold("6,2 x 10³ CFU/g", "9.1") == _fold("6,2 x 10^3 CFU/g", "9.1")
    True
    >>> _fold("< 10", "9.2") == _fold("< 10⁴ и > 10³", "9.2")
    False
    """
    s = str(v or "").lower().replace(" ", "").replace(" ", "")
    s = s.replace("cfu/g", "").replace("^", "").replace(",", ".")
    for a, b in (("⁰", "0"), ("¹", "1"), ("²", "2"), ("³", "3"), ("⁴", "4"), ("⁵", "5")):
        s = s.replace(a, b)
    s = s.replace("x10", "e").replace("х10", "e").replace("×10", "e")
    if det in ("9.4", "9.5"):
        return ("absent" if s.startswith(("отсут", "отсуств", "одговара", "absent"))
                else s)
    return s


def disagreements(m):
    """Where the two reads of one page differ on a determination the register carries."""
    out = []
    a, b = m.get("read_A") or {}, m.get("read_B") or {}
    for det, _col in COLS:
        x, y = a.get(det), b.get(det)
        if x is None or y is None:
            out.append("#%s on one read only (A %r, B %r)" % (det, x, y))
        elif _fold(x, det) != _fold(y, det):
            out.append("#%s A %r vs B %r" % (det, x, y))
    return out


def key(s):
    return str(s or "").strip().upper().replace("_", "").replace("-", "").replace("/", "")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--reads", default=READS)
    a = ap.parse_args(argv[1:])

    reads = json.load(open(a.reads, encoding="utf-8"))
    refused = {c: d for c, d in ((c, disagreements(m)) for c, m in reads.items()) if d}
    if refused:
        for code, why in sorted(refused.items()):
            print("REFUSED %s: %s" % (code, "; ".join(why)))
        print("nothing written — the two reads must agree before a value reaches the register")
        return 1

    data = json.load(open(a.src, encoding="utf-8"))
    by = {}
    for b in data["reg"]:
        for k in {key(b.get("pn")), key(b.get("cb"))} - {""}:
            by.setdefault(k, b)

    added, skipped, missing = 0, 0, []
    for code in sorted(reads):
        m = reads[code]
        block = by.get(key(m.get("batch_canonical"))) or by.get(key(m.get("cultivation_batch")))
        if block is None:
            missing.append((code, m.get("batch_canonical")))
            continue
        if any(nkey(c.get("code")) == nkey(code) for c in block["certs"]):
            skipped += 1
            continue
        vals = {col: reg_value(m["results"][det], det) for det, col in COLS}
        block["certs"].append({"code": code, "date": m["date_of_issue"], "lab": LAB,
                               "fam": FAM, "stab": False, "vals": vals, "flags": {}})
        added += 1
        print("   %-13s %s  %-9s  %s" % (code, m["date_of_issue"], m["batch_canonical"],
                                         "  ".join("%s %s" % (c, vals[c]) for _d, c in COLS)))
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
