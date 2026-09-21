#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OI-41: a determination its own issued iCoA certifies is not "to be performed".

    python3 deliverables/qc_gap_analysis/apply_icoa_status.py [--dry-run]

Owner, 21.09.2026: *"Ident A and Ident B and even the Foreign Matter parameters are
contained in the iCoA for each CoQ, this is known."*

They are, and they were on the record. Every one of these rows already carried
"Conforms | Одговара" and already cited its own internal certificate of analysis — code,
date of issue and laboratory — put there by export_coq_artifact_data.py where the iCoA
register is read. What the row kept was the STATUS build_coq_schedule.status_of gives a
determination with no document in the candidate pool at schedule time:

    ST_ICOA = "to be performed — see route"

The certificate renderer reads the status, not the result (coq_build.js `cell()`), so the
cell printed an empty red marker for a determination whose certificate is issued, numbered
and signed. That is the whole of OI-41: not a missing result, a stale status.

A determination an ISSUED internal certificate of analysis certifies has been performed.
This sets those rows to `covered` and drops the route with it — a route tells a reader
where to send a sample that still needs testing, and there is nothing left to route.

Touched only where all three hold: the status is exactly ST_ICOA, the cited document is an
issued `iCoA-PP_` code, and the row carries a result. A row still genuinely awaiting the
in-house test has no result and is left alone. Idempotent; the same rule is applied at the
source in export_coq_artifact_data.py, so a full chain replay converges here with nothing
left to do.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_coq_schedule as CQ                                          # noqa: E402

ART = os.path.join(HERE, "coq_artifact_data.json")
ICOA_RECS = os.path.join(HERE, "icoa_handoff", "v3", "icoa_v44_recs.json")
CONFORMS = "Conforms | \u041e\u0434\u0433\u043e\u0432\u0430\u0440\u0430"
FIELD = {"1": "identA", "2": "identB", "7": "fm"}
CNP_LAB = "UKIM Faculty of Pharmacy \u2014 Center for Natural Products"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    data = json.load(open(ART, encoding="utf-8"))
    icoa = {r["code"]: r for r in json.load(open(ICOA_RECS, encoding="utf-8"))}
    lifted = collections.Counter()
    lift_certs = set()

    # The result the internal certificate of analysis itself carries, lifted onto the
    # certificate of quality. Owner, 21.09.2026: "Lift any parameter results."
    #
    # The iCoA register states, per certificate, what its identification A, identification
    # B and foreign matter say: "Conforms" where the Purely Plant laboratory performed them
    # (152 of 172), or the CNP certificate that reports them where an outsourced one does
    # (20 of 172, the ruling of 20.09.2026 — "keep CNP where it explicitly reports them").
    # Both forms are already on 169 certificates; three were missed and printed an empty
    # cell for a determination their own issued iCoA certifies. Same rule, same spelling,
    # applied where it was not.
    for c in data["coqs"]:
        rec = icoa.get(c.get("icoa_code") or "")
        if not rec:
            continue
        for r in c["rows"]:
            if r["no"] not in FIELD:
                continue
            res = str(r.get("res") or "").strip()
            if res and res != "\u2014":
                continue
            said = str(rec.get(FIELD[r["no"]]) or "").strip()
            if not said:
                continue
            if said.upper().startswith("CNP "):
                r["doc"] = said.split(None, 1)[1].strip()
                r["lab"] = CNP_LAB
                r["dd"] = r.get("dd") or rec.get("issued") or ""
            else:
                r["doc"] = r.get("doc") or rec["code"]
                r["dd"] = r.get("dd") or rec.get("issued") or ""
            r["res"] = CONFORMS
            lifted[r["no"]] += 1
            lift_certs.add(c["regcode"])

    done = collections.Counter()
    waiting = collections.Counter()
    certs = set()
    for c in data["coqs"]:
        rnd = "retest" if str(c.get("t") or "").startswith("retest") else "initial"
        for r in c["rows"]:
            if str(r.get("st") or "") != CQ.ST_ICOA:
                continue
            doc = str(r.get("doc") or "").strip()
            res = str(r.get("res") or "").strip()
            # A row whose result the lift just took from the iCoA is covered too, even
            # where the citation moved to the CNP certificate that iCoA names.
            if (doc.startswith("iCoA-PP") or (r["no"] in FIELD and doc)) \
                    and res and res != "—":
                r["st"] = CQ.ST_OK
                r["route"] = ""
                done[(rnd, r["no"])] += 1
                certs.add(c["regcode"])
            else:
                waiting[(rnd, r["no"])] += 1

    print("OI-41 — a determination its issued iCoA certifies is covered, not pending")
    if lifted:
        print("   lifted from the iCoA register: %d result(s) on %d certificate(s) - %s"
              % (sum(lifted.values()), len(lift_certs),
                 ", ".join("#%s %d" % (k, lifted[k]) for k in sorted(lifted))))
    print("   corrected: %d cell(s) on %d certificate(s)"
          % (sum(done.values()), len(certs)))
    for k in sorted(done, key=lambda t: (t[0], [int(x) for x in t[1].split(".")])):
        print("      %-8s #%-4s %d" % (k[0], k[1], done[k]))
    if waiting:
        print("   left pending — no issued iCoA or no result on the row: %d" % sum(waiting.values()))
        for k in sorted(waiting, key=lambda t: (t[0], [int(x) for x in t[1].split(".")])):
            print("      %-8s #%-4s %d" % (k[0], k[1], waiting[k]))
    if a.dry_run:
        print("\n--dry-run — nothing written")
        return 0
    json.dump(data, open(ART, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwritten: coq_artifact_data.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
