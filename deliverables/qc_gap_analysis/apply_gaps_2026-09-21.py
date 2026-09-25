#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The seven pages of 21.09.2026 reach the certificates that print nothing for them.

    python3 deliverables/qc_gap_analysis/apply_gaps_2026-09-21.py [--dry-run]

Owner, 21.09.2026: *"assign everything that's needed … in full, and I will decide if I
will issue them or not"*, and *"empty results should not be included"*.

After the intakes of 16.09 and 18.09 were registered on the tracker, six microbiological
panels and one cannabinoid report were the whole of what was left: seven documents on
file, in the owner's eCoA_DATABASE, that no desk record had ever read. Each one stands
behind a determination a certificate of quality prints empty.

    409/0792/26  IJZ-MB  P160012              #9.1-9.5
    411/0794/26  IJZ-MB  P160022              #9.1-9.5
    410/0793/26  IJZ-MB  P160032              #9.1-9.5
    130/0227/26  IJZ-MB  P060192  SJ112501    #9.1-9.5
    402/0785/26  IJZ-MB  P060482  JD022601    #9.1-9.5
    433/0847/26  IJZ-MB  P060452  FB032601    #9.1-9.5
    031-3-К/26   FHM     P060102  WED102501   #3, #4, #5, #6

Every value passed the two-read gate in intake_gaps_2026-09-21/: two vendors' models read
each rendered page without seeing each other's answer, and only what both wrote is taken.
Three disagreements were settled by a third read of the page by the desk, recorded with
the region it was cut from (reads_C.json) — and the fuller read was right again, which is
the fifth instance of the OI-36 class.

Nothing already printed is overwritten. A cell that carries a figure is compared with the
new reading and reported; the company's own signed record is not rewritten here.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV                                           # noqa: E402

ART = os.path.join(HERE, "coq_artifact_data.json")
GATE = os.path.join(HERE, "intake_gaps_2026-09-21", "two_read_result.json")

# the gate's parameter key -> the determination on the certificate
DET = {"tamc": "9.1", "tymc": "9.2", "bile_tolerant_gram_negative": "9.3",
       "salmonella": "9.4", "escherichia_coli": "9.5",
       "total_thc": "4", "total_cbd": "5", "total_cbn": "6"}
IPH = "IPH — Institute of Public Health"
FHM = "Farmahem"
LABS = {"IJZ-MB": (IPH, "IJZ-MB microbiology"), "FHM": (FHM, "Farmahem — cannabinoids")}
# The lot each scan certifies, from the scan's own file name — read once, named here, so
# the join is a statement rather than a regular expression run at a distance.
LOT = {"409-0792-26_P160012.pdf": ("P160012", "", "IJZ-MB"),
       "411-0794-26_P160022.pdf": ("P160022", "", "IJZ-MB"),
       "410-0793-26_P160032.pdf": ("P160032", "", "IJZ-MB"),
       "130-0227-26_SJ112501.pdf": ("P060192", "SJ112501", "IJZ-MB"),
       "402-0785-26_JD022601.pdf": ("P060482", "JD022601", "IJZ-MB"),
       "433-0847-26_FB032601.pdf": ("P060452", "FB032601", "IJZ-MB"),
       "031-3-K-26_WED102501.pdf": ("P060102", "WED102501", "FHM")}
# Identification C on a Farmahem cannabinoid report is the desk's standing spelling, the
# one its three sibling reports 031-2, 031-4 and 031-5-К/26 already carry.
IDENT_C = "identity by the HPLC cannabinoid profile on this certificate"


def dot(v):
    """The desk prints a decimal point; the laboratory prints a comma."""
    return re.sub(r"(?<=\d),(?=\d)", ".", str(v or "").strip())


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    gate = json.load(open(GATE, encoding="utf-8"))
    if gate["held"]:
        raise SystemExit("the gate holds %d field(s) — nothing is applied until a person "
                         "rules on them" % len(gate["held"]))
    data = json.load(open(ART, encoding="utf-8"))

    by_lot = collections.defaultdict(list)
    for c in data["coqs"]:
        rnd = "retest" if str(c.get("t") or "").startswith("retest") else "initial"
        for k in (c.get("pp"), c.get("cb")):
            if k:
                by_lot[str(k).strip()].append((rnd, c))
    for v in by_lot.values():
        v.sort(key=lambda t: t[0] != "initial")

    applied, agreed, differ, nolot = [], [], [], []
    for scan, doc in sorted(gate["documents"].items()):
        p, cu, labkey = LOT[scan]
        lab, fam = LABS[labkey]
        certs = by_lot.get(p) or by_lot.get(cu) or []
        if not certs:
            nolot.append((doc["doc_code"], p, cu)); continue
        take = {}
        for prm in doc["parameters"]:
            no = DET.get(prm["parameter"])
            if no:
                take[no] = RV.canon(dot(prm["result"]), no)
        if labkey == "FHM":
            take["3"] = IDENT_C          # the report identifies the profile it quantifies
        initial = next((c for r, c in certs if r == "initial"), None)
        for rnd, c in certs:
            for r in c["rows"]:
                no = str(r.get("no"))
                if no not in take:
                    continue
                have = str(r.get("res") or "").strip()
                st = str(r.get("st") or "")
                if have and have != "—" and "not tested" not in st \
                        and "to be performed" not in st:
                    same = str(r.get("doc") or "").strip() == str(doc["doc_code"]).strip()
                    if same and dot(have) != dot(take[no]):
                        differ.append((c["regcode"], no, have, take[no], doc["doc_code"]))
                    elif same:
                        agreed.append((c["regcode"], no, have, doc["doc_code"]))
                    continue
                r["res"] = take[no]
                r["doc"] = doc["doc_code"]
                r["dd"] = doc["issue_date"]
                r["lab"] = lab
                r["fam"] = fam
                r["route"] = ""
                r["st"] = ("covered" if rnd == "initial" else
                           "carried from the initial testing (%s) — covered"
                           % ((initial or {}).get("regcode") or "the batch's initial CoQ"))
                applied.append((c["regcode"], no, take[no], doc["doc_code"]))

    print("documents through the two-read gate: %d" % len(gate["documents"]))
    print("cells filled: %d on %d certificate(s)"
          % (len(applied), len({x[0] for x in applied})))
    got = collections.Counter(x[1] for x in applied)
    for no in sorted(got, key=lambda s: [int(y) for y in s.split(".")]):
        print("   #%-5s %d" % (no, got[no]))
    print("already printed, and the new reading agrees: %d" % len(agreed))
    print("already printed, and the new reading DIFFERS: %d" % len(differ))
    for d in differ[:20]:
        print("   %-16s #%-5s printed %-18s read %-18s (%s)" % d)
    for n in nolot:
        print("no certificate for the lot: %s  %s / %s" % n)
    if a.dry_run:
        print("\n--dry-run — nothing written")
        return 0
    json.dump(data, open(ART, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwritten: coq_artifact_data.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
