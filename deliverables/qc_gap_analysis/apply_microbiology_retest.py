#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A newer microbiology certificate is a retest — the reissue cites it, and moves to it.

    python3 deliverables/qc_gap_analysis/apply_microbiology_retest.py [--dry-run]

The Head of QC, 17.09.2026:

    "If the certificate for microbiological purity from the external laboratory is at a
     newer date, meaning we have retested that parameter, you will also have to adjust
     the dating, the date of issue of the certificate of quality accordingly."

Two instructions in one sentence, and the second is the one the desk did not have.

**The first** — a newer external microbiology certificate is a retest of #9 — the desk
already half-believed. `testing_series` has said since 10.09.2026 that the IJZ-MB delivery of
25/26.08.2026 is a campaign sampling and every certificate in it is a retest document, and
the intake of 16.09.2026 put twenty-nine of them into the register for exactly that reason.
But the carry of 15.09.2026 only ever fills an **empty** row: a retest certificate takes the
initial result for a determination the retest did not run. So the ten lots whose initial
round had no microbiology at all took the campaign's result, and the nineteen whose initial
round did have microbiology kept printing it — 2025 counts on a 2026 reissue, with the
campaign certificate for the same lot sitting in the register unprinted. The ruling settles
which of the two a reissue prints: **the campaign's.** It was a retest, and a retest
certificate states the retest.

**The second** — the date moves with the document — is the new rule, and it is the v35 date
rule read forwards. v35 says a certificate may cite only a document issued on or before its
own day; the desk had been applying it as a veto, refusing the newer document and leaving the
older one printed. The Head of QC says the other resolution is the right one: take the
document and move the certificate. So a reissue whose new microbiology postdates it is
re-dated by the standing issuance rule — `issuance_schedule.coq_issue`, five to ten days
after the last external certificate the page cites, held at LAG_DAYS = 7 — and a reissue that
already postdates its new microbiology keeps the date it has.

**A release certificate is not touched.** It states the round that released the lot, and the
campaign certificate is a retest document by the ruling of 10.09.2026 — so no release
certificate may rest on one, whatever its date. That is the same ruling, not an exception to
this one: where the newer document belongs to a retest, the retest certificate is where it
goes. Twenty-nine release certificates are in that position and every one of them has a
reissue that now carries the campaign result.

**#9.1 to #9.5 move together or not at all.** The Head of QC's rule of 16.09.2026 — a panel
determined on one sample prints whole — applies here as `unify_panel_source` applies it
elsewhere: a document that reports only part of the group never takes the group, because a
reader cannot then tell which sample the five lines describe.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import issuance_schedule as ISS            # the one place the issue date is computed
import result_vocabulary as RV             # the desk's one spelling per assertion
import testing_series as TS                # which documents never certify a release

SRC = os.path.join(HERE, "coq_artifact_data.json")
REGCSV = os.path.join(HERE, "coq_register_2026-09-10.csv")
GROUP = ("9.1", "9.2", "9.3", "9.4", "9.5")
COL_DET = {"J": "9.1", "K": "9.2", "L": "9.3", "M": "9.4", "N": "9.5"}
BLANK = ("", "—")
# "<10^2 >10" — an upper bound then a lower one with no word between them, as the in-house
# sheets write it. The controlled vocabulary reads the two spellings that carry a connector;
# this gives the third one so all three go down the same path.
_BARE_RANGE = re.compile(r"(<\s*10\S*)\s+(>\s*10\S*)")


def day(v):
    """A desk date as a date, or None.

    >>> day("31.08.2026").isoformat()
    '2026-08-31'
    >>> day("") is None
    True
    """
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def in_house(doc):
    """True for a citation that is not an external laboratory certificate.

    >>> in_house("iCoA-PP_26-101"), in_house("n/a (in-house)"), in_house("534/1065/26")
    (True, True, False)
    """
    s = str(doc or "").strip()
    return s.startswith("iCoA-") or s.lower().startswith(("n/a", "no-doc-code", "ngp-"))


def whole_panels(block):
    """Every document in a lot's block that determined the WHOLE microbiology group.

    Stability timepoints measure the lot ageing and never source a certificate; a starred
    sample's certificate is real data that never certifies (testing_series.is_experimental).
    """
    out = []
    for cert in (block.get("certs") or []):
        if cert.get("stab") or TS.is_experimental(cert.get("code")):
            continue
        d = day(cert.get("date"))
        if d is None:
            continue
        vals = {COL_DET[c]: v for c, v in (cert.get("vals") or {}).items()
                if c in COL_DET and str(v or "").strip() not in ("", "/", "—")}
        if len(vals) < len(GROUP):
            continue
        out.append((d, cert.get("code"), cert.get("lab"), vals))
    return out


def index(reg):
    """lot key -> the documents that determined the whole microbiology group."""
    out = {}
    for b in reg:
        panels = whole_panels(b)
        if not panels:
            continue
        for k in {str(b.get("pn") or "").strip(), str(b.get("cb") or "").strip()} - {""}:
            out.setdefault(k, []).extend(panels)
    return out


def printed(value, no):
    """A register value in the word the certificate prints."""
    raw = _BARE_RANGE.sub("\\1 и \\2", str(value or "").strip())
    return RV.bilingual(RV.canon(raw, no), no)


def last_external(c):
    """The latest external certificate the page cites, as a date, or None."""
    days = [day(r.get("dd")) for r in c["rows"]
            if str(r.get("res") or "—").strip() not in BLANK and not in_house(r.get("doc"))]
    days = [d for d in days if d]
    return max(days) if days else None


def apply(data):
    """Re-point every reissue's microbiology, and move the date where the document is newer."""
    have = index(data["reg"])
    moved, repointed = [], []
    for c in data["coqs"]:
        if not c.get("supersedes"):
            continue                       # a release certificate states the release round
        iss = day(c.get("issue"))
        if iss is None:
            continue
        pool = (have.get(str(c.get("pp") or "").strip())
                or have.get(str(c.get("cb") or "").strip()) or [])
        if not pool:
            continue
        d, code, lab, vals = max(pool)
        rows = {r["no"]: r for r in c["rows"] if r["no"] in GROUP}
        if len(rows) < len(GROUP):
            continue
        cited = [day(r.get("dd")) for r in rows.values() if str(r.get("doc") or "—") not in BLANK]
        cited = max([x for x in cited if x], default=None)
        if cited is not None and d <= cited:
            continue                       # nothing newer than what the page already prints
        words = {no: printed(vals[no], no) for no in GROUP}
        if any(str(w).strip() in BLANK for w in words.values()):
            continue                       # a value the controlled vocabulary cannot state
        was = (rows["9.1"].get("doc"), rows["9.1"].get("dd"))
        for no in GROUP:
            r = rows[no]
            r["res"], r["doc"] = words[no], code
            r["dd"], r["lab"], r["st"] = d.strftime("%d.%m.%Y"), lab or "—", "covered"
        repointed.append((c.get("regcode"), c.get("pp") or c.get("cb"), was, code,
                          d.strftime("%d.%m.%Y")))
        le = last_external(c)
        if le:
            c["last_external"] = le.strftime("%d.%m.%Y")
        # The date follows the document only where the document is the reason to move it:
        # the new microbiology is dated AFTER the certificate, so the certificate as it
        # stood could not have cited it. A reissue already dated after its new microbiology
        # keeps the date the register gave it — the owner set LAG_DAYS = 7 as the middle of
        # a range of 5 to 10, and a date the owner set inside that range is not a defect to
        # re-derive. That is why the nineteen Tranche 3 reissues of 21.09.2026, five days
        # after their own campaign's potency certificate, do not move.
        if d > iss and le:
            want = day(ISS.coq_issue(le.strftime("%d.%m.%Y"), c.get("icoa_issue") or None))
            if want and want > iss:
                c["issue"] = want.strftime("%d.%m.%Y")
                moved.append((c.get("regcode"), c.get("pp") or c.get("cb"),
                              iss.strftime("%d.%m.%Y"), c["issue"], code,
                              d.strftime("%d.%m.%Y")))
    return repointed, moved


def restamp_register(path, moved):
    """Carry a moved date into the desk's flat CoQ register, where the date is stated."""
    if not moved or not os.path.exists(path):
        return 0
    by = {m[0]: m[3] for m in moved}
    lines = open(path, encoding="utf-8").read().splitlines(True)
    n = 0
    for i, line in enumerate(lines):
        parts = line.rstrip("\r\n").split(",")
        if len(parts) > 6 and parts[4] in by:
            parts[5] = parts[6] = by[parts[4]]
            lines[i] = ",".join(parts) + "\n"
            n += 1
    if n:
        open(path, "w", encoding="utf-8").write("".join(lines))
    return n


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--register", default=REGCSV)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    repointed, moved = apply(data)
    print("reissues whose microbiology now cites the retest campaign: %d" % len(repointed))
    for code, lot, was, doc, dd in repointed:
        print("   %-16s %-14s #9.1–#9.5  %s of %s  ->  %s of %s"
              % (code, lot, was[0] or "—", was[1] or "—", doc, dd))
    print("certificates of quality re-dated to follow the document: %d" % len(moved))
    for code, lot, old, new, doc, dd in moved:
        print("   %-16s %-14s %s -> %s   (%s of %s, + %d days)"
              % (code, lot, old, new, doc, dd, ISS.LAG_DAYS))
    if not a.dry_run and repointed:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
        n = restamp_register(a.register, moved)
        if n:
            print("restamped in %s: %d row(s)" % (os.path.basename(a.register), n))
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
