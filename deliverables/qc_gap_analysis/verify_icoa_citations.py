#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""No certificate of quality may cite another lot's internal certificate.

    python3 verify_icoa_citations.py [--html]

The internal series is numbered by ORDER OF ISSUING, so any insertion or
de-duplication in `icoa_register.build()` renumbers every code after it. A citation
written into `coq_artifact_data.json` as a frozen string therefore goes stale silently
— nothing about the document looks wrong, the number is simply somebody else's. That
is how 69 of 75 rendered citations came to point at another lot, and how lot P060412's
internal certificate came to be cited by CoQ-PP_26-073, which certifies P060342. The
QA Manager found it by reading two certificates side by side; this file is so that
nobody has to do that again.

Three things are checked, and any one of them failing is a defect:

  1. the certificate's own `icoa_code` names a register row of the certificate's LOT
     and ROUND — its P lot or its cultivation batch, release against retest;
  2. every Section 03 citation (`rows[].doc`) that names an internal certificate names
     one of the SAME LOT — either the certificate's own round, or, for a determination
     carried forward, the lot's release round;
  3. with `--html`, the same holds of every `iCoA-PP_...` string that actually reaches
     a rendered page under `design_handoff/out/`, which is the only text a reader sees.

Exit 0 and nothing printed is the pass. `apply_icoa_citations.py` is the repair.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_coq_schedule as CQ  # noqa: E402
import icoa_register  # noqa: E402

DATA = os.path.join(HERE, "coq_artifact_data.json")
OUT = os.path.join(HERE, "design_handoff", "out")
CODE = re.compile(r"iCoA-PP_\d{2}-\d{3}")
PROSE = re.compile(r"^N/A|^—|not recorded|not assigned|^$", re.I)


def clean(v):
    s = str(v or "").strip()
    return "" if PROSE.match(s) else s


def lots_of(row):
    """Every name this register row is legitimately known by."""
    return {clean(row.get("p_lot")), clean(row.get("batch"))} - {""}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true",
                    help="also read every rendered document under design_handoff/out")
    a = ap.parse_args(argv[1:])

    reg = icoa_register.build()
    by_code = {r["code"]: r for r in reg}
    bad = []

    with open(DATA, encoding="utf-8") as fh:
        certs = json.load(fh)["coqs"]

    sys.path.insert(0, os.path.join(HERE, "tracker"))
    from check_certificate_claims import frozen_lots
    frozen = frozen_lots()
    kept = []
    for c in certs:
        # a withdrawn number has no internal certificate (Head of QC, 26–27.09.2026)
        if c.get("withdrawn"):
            continue
        names = {clean(c.get("pp")), clean(c.get("cb"))} - {""}
        initial = str(c.get("t") or "").startswith("initial release")

        own = by_code.get(str(c.get("icoa_code") or "").strip())
        cited = any(str(r.get("doc") or "") == str(c.get("icoa_code") or "") for r in c.get("rows", []))
        if own is None and not cited:
            pass        # no row cites it: there is no internal certificate (CNP tested 1, 2, 7)
        elif own is None:
            bad.append((c.get("regcode"), "icoa_code", c.get("icoa_code"),
                        "no such row in the register"))
        else:
            if not (names & lots_of(own)):
                bad.append((c.get("regcode"), "icoa_code", own["code"],
                            "belongs to %s" % " / ".join(sorted(lots_of(own)))))
            if ("initial" in own["round"]) != initial:
                bad.append((c.get("regcode"), "icoa_code", own["code"],
                            "is the %s round, the certificate is %s"
                            % (own["round"], c.get("t"))))

        for rr in c.get("rows", []):
            doc = str(rr.get("doc") or "").strip()
            if not CODE.fullmatch(doc):
                continue
            row = by_code.get(doc)
            if row is None:
                bad.append((c.get("regcode"), "row #%s" % rr["no"], doc,
                            "no such row in the register"))
                continue
            if not (names & lots_of(row)):
                bad.append((c.get("regcode"), "row #%s" % rr["no"], doc,
                            "belongs to %s" % " / ".join(sorted(lots_of(row)))))
                continue
            carried = str(rr.get("st") or "").startswith(CQ.ST_CARRIED)
            if not initial and not carried and "initial" in row["round"]:
                bad.append((c.get("regcode"), "row #%s" % rr["no"], doc,
                            "is the release round, and this determination was retested"))

    read = len(certs)
    if a.html:
        for p in sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True)):
            m = re.match(r"(CoQ-PP_\d{2}-\d+)_([^_]+)_", os.path.basename(p))
            if not m:
                continue
            read += 1
            code, lot = m.group(1), m.group(2)
            with open(p, encoding="utf-8") as fh:
                page = fh.read()
            for ic in sorted(set(CODE.findall(page))):
                row = by_code.get(ic)
                if row is None:
                    bad.append((code, "rendered", ic, "no such row in the register"))
                elif lot not in lots_of(row):
                    bad.append((code, "rendered", ic,
                                "belongs to %s" % " / ".join(sorted(lots_of(row)))))

    # Tranches 1 and 2 are issued and with the customer (Head of QC, 26.09.2026): what their records
    # say is reported, never repaired — the approved scans are what was sent.
    reg_by = {c.get("regcode"): c for c in certs}
    sent = [x for x in bad if reg_by.get(x[0]) and frozen(reg_by[x[0]])]
    bad = [x for x in bad if x not in sent]
    if sent:
        print("%d citation(s) on issued Tranche 1/2 records (not touched; with the Head of QC):" % len(sent))
        for x in sent:
            print("   %-16s %-10s %-16s %s" % x)
    if bad:
        print("%d citation(s) name another lot's internal certificate:" % len(bad))
        for x in bad:
            print("   %-16s %-10s %-16s %s" % x)
        print("\nrepair: python3 apply_icoa_citations.py — it does not refuse Tranches 1 and 2; "
              "tracker/check_frozen_records.py will fail if it changes one")
        return 1
    print("%d record(s) read - every internal-certificate citation names its own lot"
          % read)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
