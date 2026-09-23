#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every certificate against the Head of QC's attribution ruling of 23.09.2026.

    python3 deliverables/qc_gap_analysis/verify_attribution_2026-09-23.py
    python3 deliverables/qc_gap_analysis/verify_attribution_2026-09-23.py --md OUT.md

The ruling, as given:

* **Microbiological purity** is on every production batch, initial and retest, and it is
  always the Institute of Public Health.
* **Heavy metals** likewise the Institute of Public Health, and every CoQ — initial and
  retest — carries a value and a result.
* **Pesticides** are tested at the Institute of Public Health *exclusively*, and every
  single batch carries a result and a value.
* **Mycotoxins** on the initial certificate come from the Institute of Public Health and
  are the one instance of a single parameter; on the retest the panel is three parameters.
* **Cannabinoids** — the assay rows — are the Center for Natural Products on the initial
  and **Farmahem exclusively** on the retest.
* **Loss on drying** is almost exclusively the Center for Natural Products, except the
  lots Farmahem tested for it.
* **Identification C** is the Center for Natural Products on the initial and Farmahem on
  the retest.
* **Identification A and Identification B** are the in-house Purely Plant laboratory on
  every certificate, initial and retest; the retest certificate carries **foreign matter**
  on the same footing.
* **All results from the retest must be present.**

This reads and writes nothing. It reports, per rule, the certificates that diverge and —
for an absent cell — the status the register gives, because "carried from the initial
testing" is the ruling of 17.09.2026 working as intended and a bare dash is not.

Output contract: one finding per line as `[rule] what — detail`, a count, exit 1 on
findings, exit 2 when it cannot verify, 0 clean.
"""
import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "coq_artifact_data.json")
SCOPES = ("tracker/coq_reissue_scope_2026-09-15.csv", "tracker/coq_draft_scope_2026-09-10.csv")

IPH = "IPH — Institute of Public Health"
CNP = "UKIM Faculty of Pharmacy — Center for Natural Products"
FHM = "Farmahem"
PP = "Purely Plant GmbH (in-house)"
# the short forms three laboratories also appear under; one institution, one identity
ALIAS = {"IJZ": IPH, "CNP": CNP, "FHM": FHM}

EMPTY = {None, "", "—", "-", "N/A", "n/a"}
CARRIED = "carried from the initial"          # the ruling of 17.09.2026, not a gap
ABSENCE = ("not tested", "upon request", CARRIED, "to be performed", "in-house CoA only")

# rule -> (determinations, laboratory required on the initial, on the retest)
# None means the ruling does not fix the laboratory for that series.
RULES = collections.OrderedDict([
    ("micro",   (["9.1", "9.2", "9.3", "9.4", "9.5"], IPH, IPH)),
    ("metals",  (["11.1", "11.2", "11.3", "11.4"], IPH, IPH)),
    ("pest",    (["12"], IPH, IPH)),
    ("myco",    (["10.1", "10.2", "10.3"], IPH, None)),
    ("cann",    (["4", "5", "6"], CNP, FHM)),
    ("lod",     (["8"], None, None)),
    ("identC",  (["3"], CNP, FHM)),
    ("identAB", (["1", "2"], PP, PP)),
    ("fm",      (["7"], PP, PP)),
])
# the rules that also demand a value on every certificate of that series
MUST_HAVE = {"micro": ("initial", "retest"), "metals": ("initial", "retest"),
             "pest": ("initial", "retest")}
# how many of a group's determinations the ruling expects a certificate to state.
# Mycotoxins are the one panel whose width is part of the ruling: one parameter on the
# initial, three on the retest — so two empty mycotoxin cells on an initial certificate
# are the ruling working, not a gap, and only a panel of the wrong width is a finding.
WIDTH = {("myco", "initial"): 1, ("myco", "retest"): 3}
TITLE = {"micro": "microbiological purity #9.1-9.5", "metals": "heavy metals #11.1-11.4",
         "pest": "pesticide residues #12", "myco": "mycotoxins #10.1-10.3",
         "cann": "cannabinoid assays #4, #5, #6", "lod": "loss on drying #8",
         "identC": "Identification C #3", "identAB": "Identification A and B #1, #2",
         "fm": "foreign matter #7"}


def tranches():
    """P lot -> tranche number, from the desk's own scope files."""
    out = {}
    for rel in SCOPES:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                lot, t = row.get("p_lot"), row.get("tranche")
                if lot and lot not in out:
                    out[lot] = str(t or "").strip()
    return out


def series(c):
    return "initial" if str(c.get("t", "")).startswith("initial release") else "retest"


def absent(res):
    s = str(res or "").strip()
    return s in EMPTY or any(a in s.lower() for a in ABSENCE)


def carried(st, res):
    return CARRIED in (str(st or "") + " " + str(res or "")).lower()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--md", help="also write the report as markdown")
    a = ap.parse_args(argv)

    if not os.path.exists(a.data):
        print("cannot verify: %s is not there" % a.data)
        return 2
    d = json.load(open(a.data, encoding="utf-8"))
    coqs = d.get("coqs") or []
    if not coqs:
        print("cannot verify: the data layer holds no certificates")
        return 2
    TR = tranches()

    findings = []     # (rule, headline, detail)
    # rule -> series -> Counter of laboratory, and the certificates that diverge
    seen = collections.defaultdict(collections.Counter)
    wrong = collections.defaultdict(list)
    missing = collections.defaultdict(list)
    alias_rows = []
    panel = collections.Counter()

    for c in coqs:
        ser, code = series(c), str(c.get("regcode") or "?")
        lot = str(c.get("pp") or c.get("cb") or "?")
        tr = TR.get(lot, "")
        where = "%s %s %s%s" % (code, lot, ser, (" T" + tr) if tr else "")
        rows = {str(r.get("no")): r for r in c.get("rows") or []}
        n_myco = 0
        for rule, (dets, want_i, want_r) in RULES.items():
            want = want_i if ser == "initial" else want_r
            for det in dets:
                r = rows.get(det)
                if r is None:
                    missing[(rule, ser)].append((where, det, "no row at all"))
                    continue
                res, lab, st = r.get("res"), str(r.get("lab") or ""), r.get("st")
                if lab in ALIAS:
                    alias_rows.append((where, det, lab))
                lab = ALIAS.get(lab, lab)
                if absent(res) or lab in EMPTY:
                    kind = "carried from the initial testing" if carried(st, res) else str(res or "—")
                    missing[(rule, ser)].append((where, det, kind))
                    continue
                if rule == "myco":
                    n_myco += 1
                seen[(rule, ser)][lab] += 1
                if want and lab != want:
                    wrong[(rule, ser)].append((where, det, lab, str(res)[:18]))
        panel[(ser, n_myco)] += 1

    # ---- the report
    print("THE ATTRIBUTION RULING OF 23.09.2026, AGAINST %d CERTIFICATES" % len(coqs))
    n = collections.Counter(series(c) for c in coqs)
    print("  %d initial release, %d retest" % (n["initial"], n["retest"]))
    print()
    for rule, (dets, want_i, want_r) in RULES.items():
        print("-- %s" % TITLE[rule])
        for ser, want in (("initial", want_i), ("retest", want_r)):
            got = seen[(rule, ser)]
            wl = "requires %s" % want if want else "laboratory not fixed by the ruling"
            print("   %-7s %-4d stated  |  %s" % (ser, sum(got.values()), wl))
            for k, v in got.most_common():
                mark = "  <-- not what the ruling says" if want and k != want else ""
                print("           %5d  %s%s" % (v, k, mark))
            for kind, bucket, label in (("w", wrong, "wrong laboratory"),
                                        ("m", missing, "no value")):
                items = bucket[(rule, ser)]
                if not items:
                    continue
                if kind == "m":
                    byk = collections.Counter(x[2] for x in items)
                    for k, v in byk.most_common():
                        must = ser in MUST_HAVE.get(rule, ())
                        fixed = (rule, ser) in WIDTH
                        note = ("  <-- the ruling requires a value" if must else
                                "  <-- the ruling states %d of these" % WIDTH[(rule, ser)]
                                if fixed else "")
                        print("           %5d  %s: %s%s" % (v, label, k, note))
                        # a panel whose width the ruling fixes is checked by width alone,
                        # below; the cells it leaves empty are not a gap
                        if fixed:
                            continue
                        findings.append((rule, "%s on the %s: %s" % (label, ser, k),
                                         ", ".join(sorted({x[0].split()[0] for x in items
                                                           if x[2] == k}))))
                else:
                    byl = collections.Counter(x[2] for x in items)
                    for k, v in byl.most_common():
                        print("           %5d  %s: %s" % (v, label, k))
                        findings.append((rule, "%s on the %s: %s where the ruling says %s"
                                         % (label, ser, k, want_i if ser == "initial" else want_r),
                                         ", ".join(sorted({x[0].split()[0] for x in items
                                                           if x[2] == k}))))
        print()

    print("-- the mycotoxin panel width")
    for (ser, k), v in sorted(panel.items()):
        want = 1 if ser == "initial" else 3
        mark = "" if k == want else "  <-- the ruling says %d" % want
        print("   %-7s %d parameter(s) stated on %3d certificate(s)%s" % (ser, k, v, mark))
        if k != want:
            findings.append(("myco", "the %s panel states %d parameter(s), the ruling says %d"
                             % (ser, k, want), "%d certificates" % v))
    print()
    print("-- one canonical name per institution")
    if alias_rows:
        byl = collections.Counter(x[2] for x in alias_rows)
        for k, v in byl.most_common():
            print("   %5d row(s) carry the short form %s (canonically %s)" % (v, k, ALIAS[k]))
            findings.append(("naming", "the short form %s appears on %d row(s)" % (k, v),
                             "canonically %s" % ALIAS[k]))
    else:
        print("   clean — every row names its institution in full")
    print()

    print("FINDINGS: %d" % len(findings))
    for rule, head, detail in findings:
        print("[%s] %s — %s" % (rule, head, detail[:300]))

    if a.md:
        with open(a.md, "w", encoding="utf-8") as fh:
            fh.write("# The attribution ruling of 23.09.2026\n\n")
            fh.write("%d certificates: %d initial release, %d retest. "
                     "%d finding(s).\n\n" % (len(coqs), n["initial"], n["retest"], len(findings)))
            fh.write("| rule | finding | certificates |\n| --- | --- | --- |\n")
            for rule, head, detail in findings:
                fh.write("| %s | %s | %s |\n" % (rule, head, detail[:400]))
        print("\nwrote %s" % a.md)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
