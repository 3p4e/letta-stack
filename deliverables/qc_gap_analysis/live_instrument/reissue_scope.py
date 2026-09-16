#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The reissue scope: which 12-month reissues the desk can compile today, and why not the rest.

    python3 deliverables/qc_gap_analysis/live_instrument/reissue_scope.py

Written from the export (coq_artifact_data.json) after extract_coq_register.py has lifted
the CoQ Register into it: one row per reissue, the lot it is compiled under (the packaged
lot, else the cultivation batch), the register's code and date of issue, the initial
certificate it supersedes, and whether it is draftable — it is when the CoQ Register has
numbered it. A reissue the register has not numbered is listed with the reason, so the
scope is the whole series and not only the part that compiles.
"""
import csv
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
TRANCHE = {"197": "1", "220": "2", "227": "3"}
COLS = ["tranche", "batch_as_delivered", "p_lot", "strain_as_delivered", "coq_code",
        "issue_date", "supersedes", "supersedes_issued", "draftable", "reason"]


def rows(src):
    d = json.load(open(src, encoding="utf-8"))
    out = []
    for c in d["coqs"]:
        if not c["t"].startswith("additional"):
            continue
        code = c.get("regcode") or ""
        numbered = code.startswith("CoQ-PP_26-")
        # a code the register has allocated in advance (Tranche 3, owner 15.09.2026)
        # is not an issued one: Issuable reads "allocated", the date is the owner's
        # provisional one, and the certificate is compiled once the register says yes
        issuable = c.get("reg_issuable") == "yes"
        camp = c.get("icoa_campaign")
        sup = c.get("supersedes") or {}
        if numbered and not issuable:
            numbered = False
            reason = ("Tranche %s: code %s allocated on the CoQ Register (owner, 15.09.2026), planned %s provisionally — "
                      "compiled once the 227-М mycotoxin certificates exist" % (TRANCHE.get(camp, camp), code, c.get("issue") or "undated"))
        elif numbered:
            reason = ""
        elif not camp:
            reason = "no retest campaign sampling on file for this lot (iCoA Register: not numbered)"
        elif not c.get("icoa_code", "").startswith("iCoA-PP_26-"):
            reason = "Tranche %s: the campaign's internal certificate is not numbered on the iCoA Register" % TRANCHE.get(camp, camp)
        else:
            reason = ("Tranche %s: not yet numbered on the CoQ Register — the reissues are issued in tranche order after the "
                      "campaign's certificates are complete (%s)" % (TRANCHE.get(camp, camp), code or "— at issue —"))
        out.append({"tranche": TRANCHE.get(camp, "—"), "batch_as_delivered": c.get("cb", ""),
                    "p_lot": c.get("pp") or c.get("cb", ""), "strain_as_delivered": c.get("strain", ""),
                    "coq_code": code if numbered else (code or "— at issue —"),
                    "issue_date": c.get("issue", "") if numbered else "",
                    "supersedes": sup.get("code", ""), "supersedes_issued": sup.get("date", ""),
                    "draftable": "yes" if numbered else "no", "reason": reason})
    out.sort(key=lambda r: (r["tranche"], r["coq_code"] if r["draftable"] == "yes" else "~", r["p_lot"]))
    return out


def main(argv):
    src = argv[1] if len(argv) > 1 else os.path.join(GAP, "coq_artifact_data.json")
    out = argv[2] if len(argv) > 2 else os.path.join(GAP, "tracker", "coq_reissue_scope_2026-09-15.csv")
    rs = rows(src)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rs)
    n = sum(1 for r in rs if r["draftable"] == "yes")
    print("%s: %d reissues, %d draftable (numbered on the CoQ Register), %d not"
          % (out, len(rs), n, len(rs) - n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
