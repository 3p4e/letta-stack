#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The register's codes reach the certificates that were printing "— at issue —".

    python3 deliverables/qc_gap_analysis/apply_register_codes.py [--dry-run]

The Head of QC, 18.09.2026: "assign codes if they're missing."

Seven certificates carried no number — CC042601 and FB042601, release and reissue, and
P160012, P160022 and P160032 — because the batch list holds no packaging date for those
lots, so the register could not date the certificates and had withheld their numbers with
the date. The ruling separates the two: the number is assigned now, in series order after
the last allocated code; the date still follows the packaging date once the list carries it.

The numbers are the REGISTER'S. build_tracker_v8.py computes them (Issuable "ruled"),
extract_coq_register.py lifts them into coq_register_2026-09-10.csv, and this script
places what that file says on coq_artifact_data.json — the same route every numbered
certificate took. Nothing is minted here: a certificate that the register still does not
number is left as it stands, and a certificate that already carries a number is never
renumbered.

A reissue names the release certificate it supersedes by the register's code, so the two
reissues take their release certificate's new code on that line as well.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "ingestion", "common"))
ART = os.path.join(HERE, "coq_artifact_data.json")
REG = os.path.join(HERE, "coq_register_2026-09-10.csv")
NO_NUMBER = "— at issue —"


def batch_key(name):
    try:
        import batch_id
        return batch_id.batch_key(name)
    except Exception:
        return re.sub(r"[\s＊*]", "", str(name or "")).upper()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    reg = {}
    with open(REG, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r.get("key"):
                continue
            pre, sfx = r["key"].rsplit("|", 1)
            for name in (pre, r.get("cu_batch", ""), r.get("p_batch", "")):
                name = (name or "").strip()
                if name and not name.startswith(("N/A", "—")):
                    reg.setdefault((batch_key(name), sfx), r)

    data = json.load(open(ART, encoding="utf-8"))
    numbered, still, taken = [], [], set()
    for c in data["coqs"]:
        if str(c.get("regcode") or "").startswith("CoQ-PP_26-"):
            taken.add(c["regcode"])
    for c in data["coqs"]:
        if str(c.get("regcode") or "").startswith("CoQ-PP_26-"):
            continue
        sfxs = ("R", "R2", "R3", "R4", "R5") if str(c.get("t") or "").startswith("retest") else ("I",)
        row = None
        for sfx in sfxs:
            for name in (c.get("pp"), c.get("cb")):
                if name and (batch_key(name), sfx) in reg:
                    row = reg[(batch_key(name), sfx)]
                    break
            if row:
                break
        code = (row or {}).get("coq_code", "").strip()
        if not code.startswith("CoQ-PP_26-"):
            still.append((c.get("pp") or c.get("cb"), c.get("t"), (row or {}).get("issuable", "no row")))
            continue
        if code in taken:
            raise SystemExit("%s is already carried by another certificate — the register has moved" % code)
        taken.add(code)
        c["regcode"] = code
        c["reg_issuable"] = (row.get("issuable") or "").strip()
        numbered.append((code, c.get("pp") or c.get("cb"), c.get("t"), c.get("issue")))

    # a reissue names the release certificate it supersedes by the register's code
    initial = {}
    for c in data["coqs"]:
        if not str(c.get("t") or "").startswith("retest"):
            for name in (c.get("pp"), c.get("cb")):
                if name:
                    initial.setdefault(batch_key(name), c)
    relinked = 0
    for c in data["coqs"]:
        if not str(c.get("t") or "").startswith("retest"):
            continue
        sup = c.get("supersedes") or {}
        if str(sup.get("code", "")).startswith("CoQ-PP_26-"):
            continue
        i = next((initial[batch_key(n)] for n in (c.get("pp"), c.get("cb")) if n and batch_key(n) in initial), None)
        if i and str(i.get("regcode") or "").startswith("CoQ-PP_26-"):
            c["supersedes"] = {"code": i["regcode"], "date": i.get("issue", ""), "issued": True}
            relinked += 1

    print("numbered by the register: %d" % len(numbered))
    for n in numbered:
        print("   %-16s %-10s %-32s issue %s" % n)
    print("reissues now naming their release certificate: %d" % relinked)
    if still:
        print("still without a number: %d" % len(still))
        for s in still:
            print("   %-10s %-32s (%s)" % s)
    if a.dry_run:
        print("\n--dry-run — nothing written")
        return 0
    json.dump(data, open(ART, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwritten: %s" % os.path.relpath(ART, os.path.dirname(HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
