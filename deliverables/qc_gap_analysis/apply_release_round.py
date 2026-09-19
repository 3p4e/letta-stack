#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A release certificate states the release round — the FIRST result on file, not the latest.

    python3 deliverables/qc_gap_analysis/apply_release_round.py [--dry-run]

The Head of QC, 17.09.2026, on P050022:

    "at parameter 9 correct and check the parameters under 9 microbiology TAMC and BT, and
     parameter 11 — in the eCOA for heavy metals all parameters are ND and in the CoQ there
     is an actual value inserted."

Both are the same defect, and it is not a reading error: **the certificate is citing the
wrong document.** P050022 has two microbiology certificates and two contaminant reports —

| determination | release testing | retest |
| --- | --- | --- |
| #9.1–#9.5 | `471-0862-25` 22.05.2025 — TAMC 700, TYMC < 10, GNB < 10² и > 10 | `627/1128/25` 02.07.2025 — all < 10 |
| #10.2, #11, #12 | `2471/2025` 30.05.2025 — aflatoxins < 2, Pb/Cd/As/Hg all н.д., pesticides н.д. | `3176/2025` 26.06.2025 — As 0.047 |

— and the release certificate was printing the **retest** of each. That is why arsenic showed
0.047 where the eCoA the Head of QC was reading says N.D., and why TAMC read < 10 where the
release page says 700.

THE RULE. The owner's ruling of 10.09.2026 already settles it: "the first value of a parameter
obtained would be counted as an initial quality control testing, and every other point of
testing for any of the parameters from a batch will be considered as a retest." A release
certificate is the certificate of the release round, so it prints the **first** result on file
for each determination — not the latest one that happens to predate its issue date, which is
what the compilation had been taking.

The group moves whole (the rule of 16.09.2026: a panel determined on one sample prints whole),
and a campaign certificate — a re-analysis series or the IJZ-MB delivery — is never release
testing, so it is never a candidate here. A reissue is untouched: it states the retest, and
`apply_microbiology_retest.py` and the carry of 15.09.2026 settle what it prints.

The sweep finds exactly two certificates in this position out of the eighty-nine: CoQ-PP_26-007
(P050022) and CoQ-PP_26-010 (P050042). The Head of QC found one of them by eye.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV
import testing_series as TS

SRC = os.path.join(HERE, "coq_artifact_data.json")
COL_DET = {"E": "4", "G": "5", "H": "6", "I": "8", "J": "9.1", "K": "9.2", "L": "9.3",
           "M": "9.4", "N": "9.5", "O": "10.2", "P": "10.1", "Q": "10.3", "R": "11.1",
           "S": "11.2", "T": "11.3", "U": "11.4", "V": "12"}
# the determination groups that must move together
GROUPS = [("4",), ("5",), ("6",), ("8",), ("9.1", "9.2", "9.3", "9.4", "9.5"),
          ("10.1", "10.2", "10.3"), ("11.1", "11.2", "11.3", "11.4"), ("12",)]
BLANK = ("", "—")
_BARE_RANGE = re.compile(r"(<\s*10\S*)\s+(>\s*10\S*)")


def day(v):
    """A desk date as a date, or None.

    >>> day("22.05.2025").isoformat()
    '2025-05-22'
    >>> day("") is None
    True
    """
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def campaign(code):
    """A certificate of a retest campaign — never release testing.

    >>> campaign("197-4-К/26"), campaign("536/1067/26")
    (True, True)
    >>> campaign("471-0862-25"), campaign("2471/2025")
    (False, False)
    """
    return TS.is_reanalysis(code) or TS.is_retest_only(code)


def in_house(code, lab=""):
    """True for a company record rather than an external laboratory certificate.

    An in-house result reaches a certificate through the batch's internal certificate of
    analysis and never through the sheet's own label — the standing routing of 11.09.2026 —
    so an in-house row is not a candidate for this rule at all.

    >>> in_house("iCoA-PP_26-005"), in_house("n/a — Purely Plant in-house CoA (Batch X)")
    (True, True)
    >>> in_house("In-house GC cross-check NGP/QCG/SOP-024"), in_house("", "PP")
    (True, True)
    >>> in_house("471-0862-25", "IPH — Institute of Public Health")
    False
    """
    c, l = str(code or "").strip(), str(lab or "").strip()
    if c.startswith("iCoA-") or c.lower().startswith(("n/a", "no-doc-code", "ngp-", "in-house")):
        return True
    return l in ("PP", "NGP") or "in-house" in l.lower() or "Purely Plant" in l


def index(reg):
    """lot key -> [(date, code, lab, {determination: value})] for release-eligible documents."""
    out = {}
    for b in reg:
        rows = []
        for cert in (b.get("certs") or []):
            code = cert.get("code")
            if (cert.get("stab") or TS.is_experimental(code) or campaign(code)
                    or in_house(code, cert.get("lab"))):
                continue
            d = day(cert.get("date"))
            if d is None:
                continue
            vals = {COL_DET[c]: str(v).strip() for c, v in (cert.get("vals") or {}).items()
                    if c in COL_DET and str(v or "").strip() not in ("", "/", "—")}
            if vals:
                rows.append((d, code, cert.get("lab"), vals))
        if not rows:
            continue
        for k in {str(b.get("pn") or "").strip(), str(b.get("cb") or "").strip()} - {""}:
            out.setdefault(k, []).extend(rows)
    return out


def printed(value, no):
    return RV.bilingual(RV.canon(_BARE_RANGE.sub("\\1 и \\2", str(value or "").strip()), no), no)


def apply(data):
    """Point every release certificate's groups at the release round. Returns the changes."""
    have = index(data["reg"])
    changed = []
    for c in data["coqs"]:
        if c.get("supersedes"):
            continue                     # a reissue states the retest, not the release round
        iss = day(c.get("issue"))
        if iss is None:
            continue
        pool = (have.get(str(c.get("pp") or "").strip())
                or have.get(str(c.get("cb") or "").strip()) or [])
        if not pool:
            continue
        rows = {r["no"]: r for r in c["rows"]}
        for group in GROUPS:
            # the determinations of this group the certificate actually prints. The panel
            # rule is about what a reader sees: the printed part of a group must come from
            # one document. A determination printing "not tested" is not part of the panel
            # and does not stop the rest of it moving.
            live = [n for n in group if n in rows
                    and str(rows[n].get("res") or "\u2014").strip() not in BLANK
                    and "not tested" not in str(rows[n].get("res") or "").lower()]
            if not live:
                continue
            # the earliest document that determined all of it, on or before the day
            whole = [x for x in pool if x[0] <= iss and all(n in x[3] for n in live)]
            if not whole:
                continue
            d, code, lab, vals = min(whole)
            cited = max([day(rows[n].get("dd")) for n in live if day(rows[n].get("dd"))],
                        default=None)
            if cited is None or d >= cited:
                continue                 # already on the release document, or nothing earlier
            words = {n: printed(vals[n], n) for n in live}
            if any(str(w).strip() in BLANK for w in words.values()):
                continue
            was = (rows[live[0]].get("doc"), rows[live[0]].get("dd"))
            for n in live:
                r = rows[n]
                before = r.get("res")
                r["res"], r["doc"] = words[n], code
                r["dd"], r["lab"] = d.strftime("%d.%m.%Y"), lab or "—"
                r["st"] = "covered"
                changed.append((c.get("regcode"), c.get("pp") or c.get("cb"), n,
                                str(before), words[n], was[0] or "—", was[1] or "—",
                                code, d.strftime("%d.%m.%Y")))
    return changed


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    changed = apply(data)
    print("release rows re-pointed at the release round: %d" % len(changed))
    for r in changed:
        print("   %-16s %-13s #%-5s %-22s -> %-22s   %s of %s -> %s of %s"
              % (r[0], r[1], r[2], r[3][:22], r[4][:22], r[5], r[6], r[7], r[8]))
    if not a.dry_run and changed:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
