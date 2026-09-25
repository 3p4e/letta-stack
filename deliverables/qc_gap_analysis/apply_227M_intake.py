#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Tranche 3 mycotoxin re-analysis, into the release register.

    python3 deliverables/qc_gap_analysis/apply_227M_intake.py [--dry-run]

Thirty Farmahem reports, `227-1-М/26` … `227-30-М/26`, issued 16.09.2026 — received
24.08.2026, analysed 15.09.2026. They are the documents thirty Tranche 3 certificates have
been waiting on: #10.1 and #10.3 print "awaiting the mycotoxin re-analysis — Farmahem" on
every one of them.

`intake_227M_2026-09-16/reads.json` is the read. These are digitally generated PDFs rather
than scans, so the code, the sample number, the internal FLŽS number, the strain, the
packaged lot and all five analytes come off the page verbatim with no OCR in the path —
and **each page prints its own P lot**, so the batch mapping is verified per certificate
rather than carried across from the paired cannabinoid certificate.

**Twenty-six are written. Four are not.** `227-13`, `227-18`, `227-20` and `227-30` carry
no text layer at all — Drive returns two empty pages, twice asked. A certificate of quality
does not print a result from a page nobody could read, so those four stay empty and are
named in `reads.json` under `_held`.

Every certificate written prints ND for Aflatoxin B1, B2, G1, G2 and Ochratoxin A, so:

  * **P** (#10.1, Aflatoxin B1) — ND, as the page states it;
  * **Q** (#10.3, Ochratoxin A) — ND, as the page states it;
  * **O** (#10.2, total aflatoxins) — ND. The page prints no Σ row; it is written only
    because B1, B2, G1 and G2 are each ND, which is how the 197-М/26 and 220-М/26 rows
    the register already carries were read.

Writing is additive and folded on `tracker_data.nkey`: a value the register already holds
is never rewritten, and a code is matched however the page spelled it.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tracker"))
from tracker_data import nkey                                          # noqa: E402
SRC = os.path.join(HERE, "coq_artifact_data.json")
READS = os.path.join(HERE, "intake_227M_2026-09-16", "reads.json")
LAB = "Farmahem"
FAM = "Farmahem re-analysis — mycotoxins"
DATE = "16.09.2026"
VALS = {"O": "ND", "P": "ND", "Q": "ND"}


def key(s):
    return str(s or "").strip().upper().replace("_", "").replace("-", "").replace("/", "")


def apply(data, reads):
    by = {}
    for b in data["reg"]:
        for k in {key(b.get("pn")), key(b.get("cb"))} - {""}:
            by.setdefault(k, b)
    added, gained, missing = 0, 0, []
    for c in reads["certs"]:
        block = next((by[key(x)] for x in (c.get("p"), c.get("cb")) if key(x) in by), None)
        if block is None:
            missing.append((c["code"], c.get("p") or c.get("cb")))
            continue
        have = [x for x in block["certs"] if nkey(x.get("code")) == nkey(c["code"])]
        if have:
            new = {k: v for k, v in VALS.items() if k not in (have[0].get("vals") or {})}
            if new:
                have[0].setdefault("vals", {}).update(new)
                gained += len(new)
            continue
        block["certs"].append({"code": c["code"], "date": DATE, "lab": LAB, "fam": FAM,
                               "stab": False, "vals": dict(VALS), "flags": {}})
        added += 1
    return added, gained, missing


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    reads = json.load(open(READS, encoding="utf-8"))
    data = json.load(open(a.src, encoding="utf-8"))
    added, gained, missing = apply(data, reads)
    print("certificates read: %d   written: %d   columns added to one already there: %d"
          % (len(reads["certs"]), added, gained))
    for row in reads["_held"]:
        print("   HELD %-14s %-12s %s" % (row["code"], row.get("cb"), row["why"][:62]))
    for code, lot in missing:
        print("   NO BLOCK %-14s %s" % (code, lot))
    if not a.dry_run and (added or gained):
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
