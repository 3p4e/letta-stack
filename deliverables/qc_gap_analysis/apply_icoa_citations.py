#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-resolve every certificate of quality's internal-certificate citation.

    python3 apply_icoa_citations.py [--dry-run]

A certificate of quality cites an internal certificate of analysis for determinations
#1, #2 and #7. Those citations were written into `coq_artifact_data.json` as frozen
strings. The internal series is numbered by ORDER OF ISSUING (`icoa_register.build()`),
so inserting or de-duplicating a row renumbers everything after it - OI-26 recorded
exactly that on 11.09.2026: "de-duplicating shifted every code from 045 onward, so any
code quoted before 11.09.2026 is stale." Nothing re-resolved the citations afterwards,
so 69 of the 75 citations on the rendered fleet pointed at another lot's certificate,
43 of them off by one and 16 by two. The QA Manager found it from the other end: lot
P060412's internal certificate was cited by CoQ-PP_26-073, which certifies P060342.

The repair is to stop quoting a number and start resolving one. For each certificate:

    lot   = its P lot, falling back to its cultivation batch
    round = initial release, or a retest - from the certificate's own type
    then  = the register row for that lot and round

and the pick is CORROBORATED, not assumed: the certificate already carries the internal
certificate's testing date in `icoa_tested`, so the register row whose `tested_from`
matches is the one taken. 165 of 172 resolve on that date; 7 more are the only candidate
their lot and round admit. None is resolved by position, which is what drifted.

A certificate cites its internal certificate TWICE: once as the certificate's own
`icoa_code`, and once per determination in the Section 03 source column (`rows[].doc`).
Only the second one prints, so both are repaired here, by the same rule the export
applies (`export_coq_artifact_data.py`): a determination the certificate's own round
covers cites that round's certificate, and a determination CARRIED from the release
round cites the RELEASE round's certificate — never the retest's, and never an in-house
record. A row already resting on an outsourced certificate is not touched.

`verify_icoa_citations.py` is the standing check that this cannot come back.
"""
import argparse
import collections
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_coq_schedule as CQ  # noqa: E402
import icoa_register  # noqa: E402

DATA = os.path.join(HERE, "coq_artifact_data.json")
PROSE = re.compile(r"^N/A|^—|not recorded|not assigned|^$", re.I)


def clean(v):
    """A batch field may carry prose rather than a code; that is not a key."""
    s = str(v or "").strip()
    return "" if PROSE.match(s) else s


def index(reg):
    """Register rows by every key a certificate might name them under."""
    idx = collections.defaultdict(list)
    for r in reg:
        for k in {clean(r.get("p_lot")), clean(r.get("batch"))}:
            if k:
                idx[k].append(r)
    return idx


def resolve(cert, idx):
    """-> (register row, how) or (None, why). Never falls back to a position."""
    want_initial = str(cert.get("t") or "").startswith("initial release")
    cands = []
    for key in (clean(cert.get("pp")), clean(cert.get("cb"))):
        if key and key in idx:
            cands = [r for r in idx[key] if ("initial" in r["round"]) == want_initial]
            if cands:
                break
    if not cands:
        return None, "no row for this lot and round"
    tested = str(cert.get("icoa_tested") or "").strip()
    exact = [r for r in cands if tested and r.get("tested_from") == tested]
    if len(exact) == 1:
        return exact[0], "date"
    if len(cands) == 1:
        return cands[0], "only candidate"
    return None, "%d candidates, %d match the testing date" % (len(cands), len(exact))


def initial_row(cert, idx):
    """The lot's release-round row — what a CARRIED determination must cite."""
    for key in (clean(cert.get("pp")), clean(cert.get("cb"))):
        if key and key in idx:
            rows = [r for r in idx[key] if "initial" in r["round"]]
            if rows:
                return rows[0]
    return None


def repoint_rows(cert, own, rel):
    """Re-point this certificate's Section 03 citations. -> (repointed, already right).

    Only a citation that already names an internal certificate is considered: a row
    resting on an outsourced certificate is the laboratory's document, not the desk's,
    and nothing here may move it.
    """
    own_cov = set(own["parameters"].split())
    rel_cov = set(rel["parameters"].split()) if rel else set()
    moved = kept = 0
    for rr in cert.get("rows", []):
        doc = str(rr.get("doc") or "").strip()
        if not doc.startswith("iCoA-PP_"):
            continue
        carried = str(rr.get("st") or "").startswith(CQ.ST_CARRIED)
        if carried and rel and rr["no"] in rel_cov:
            want = rel
        elif rr["no"] in own_cov:
            want = own
        else:
            raise ValueError("%s row #%s: %s is cited but neither round covers it"
                             % (cert.get("regcode"), rr["no"], doc))
        if doc == want["code"]:
            kept += 1
            continue
        rr["doc"], rr["dd"] = want["code"], want["issued"]
        moved += 1
    return moved, kept


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    idx = index(icoa_register.build())
    with open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)

    how = collections.Counter()
    changed, failed = [], []
    moved = kept = 0
    for c in data["coqs"]:
        row, why = resolve(c, idx)
        if row is None:
            failed.append((c.get("regcode"), clean(c.get("pp")), why))
            continue
        how[why] += 1
        old = str(c.get("icoa_code") or "")
        if row["code"] != old:
            changed.append((c.get("regcode"), clean(c.get("pp")) or clean(c.get("cb")),
                            old, row["code"], why))
            if not a.dry_run:
                c["icoa_code"] = row["code"]
        # the printed half: Section 03's per-determination source column
        rel = initial_row(c, idx) if not str(c.get("t") or "").startswith("initial release") else None
        m, k = repoint_rows(copy.deepcopy(c) if a.dry_run else c, row, rel)
        moved += m
        kept += k

    print("certificates of quality: %d" % len(data["coqs"]))
    for k, v in sorted(how.items()):
        print("   resolved by %-16s %d" % (k, v))
    print("   certificate citations rewritten  %d" % len(changed))
    print("   certificate citations correct    %d" % (sum(how.values()) - len(changed)))
    print("   Section 03 rows re-pointed       %d" % moved)
    print("   Section 03 rows already correct  %d" % kept)
    if failed:
        print("\nUNRESOLVED - nothing written for these:")
        for f in failed:
            print("   %-16s %-10s %s" % f)
        return 1
    for row in changed[:10]:
        print("   %-16s %-9s %-16s -> %-16s (%s)" % row)
    if len(changed) > 10:
        print("   ... and %d more" % (len(changed) - 10))
    if a.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print("\nwrote %s" % os.path.relpath(DATA, HERE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
