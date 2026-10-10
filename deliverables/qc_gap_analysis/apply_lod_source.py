#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loss on drying: every certificate cites one, and Farmahem wins where both laboratories have one.

    python3 deliverables/qc_gap_analysis/apply_lod_source.py [--dry-run] [--report]

The Head of QC, 17.09.2026:

    "For all certificates of quality documents for all production batches you have to cite
     parameter value for drying and also cite the corresponding certificate, and in this case
     for this parameter it is either Center for Natural Products or Farmahem laboratory, and
     in cases where you have both you will choose the value from Farmahem."

Three things, and the desk had none of them written down:

1. **#8 is never left blank while a document exists.** A certificate that prints "not tested"
   with a loss-on-drying report for its own lot on file is a desk failure, not a testing gap.
2. **Two laboratories determine it and no others** — the Center for Natural Products (the
   `ППК` series, on the potency page) and Farmahem (the `ГС` series, its own one-parameter
   report). A census of all 172 certificates confirms it: no third laboratory appears anywhere.
3. **Farmahem outranks the Center where a lot has both.** That is a ranking of sources, not of
   dates, so it is written as one, and it is why this module exists rather than a carry rule.

WHAT THIS CHANGES, AND WHAT IT DELIBERATELY DOES NOT. It fills a blank #8 from a document the
lot has, and it moves a citation from the Center to Farmahem, or from the in-house sheet to
either of them. It does **not** move a citation from one document of the same laboratory to a
later one — that is the question `OI-52` puts to the Head of QC (does the ruling of 17.09.2026
on the microbiological certificate reach loss on drying too?), and it is not answered here.

A release certificate still refuses a retest document — the ruling of 10.09.2026 — and no
certificate cites a document issued after its own day (v35). Both guards hold here as
everywhere else.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import testing_series as TS

SRC = os.path.join(HERE, "coq_artifact_data.json")
NOT_TESTED = ("", "—")
# the laboratories that determine loss on drying, best first. The order IS the ruling.
RANK = ("Farmahem", "CNP", "in-house")


def day(v):
    """A desk date as a date, or None.

    >>> day("12.02.2026").isoformat()
    '2026-02-12'
    >>> day("") is None
    True
    """
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def source_of(code, lab=""):
    """Which laboratory a loss-on-drying citation belongs to.

    Farmahem writes its own one-parameter report, numbered `NNN-n-ГС/YY`; the Center for
    Natural Products puts the figure on the potency page, numbered `ППКnnnnn`. An in-house
    sheet carries the internal certificate's number, or none at all.

    >>> source_of("031-3-ГС/26"), source_of("051-1-GS/26")
    ('Farmahem', 'Farmahem')
    >>> source_of("ППК25174"), source_of("PP CoA #027 / ППК25370")
    ('CNP', 'CNP')
    >>> source_of("iCoA-PP_26-023"), source_of("In-house GC cross-check NGP/QCG/SOP-024")
    ('in-house', 'in-house')
    >>> source_of("", "Farmahem")
    'Farmahem'
    """
    c, l = str(code or "").strip(), str(lab or "").strip()
    if c.startswith("iCoA-") or c.lower().startswith(("n/a", "no-doc-code", "ngp-", "in-house")):
        return "in-house"
    if "ГС" in c or re.search(r"-GS/", c, re.I) or l in ("Farmahem", "FHM"):
        return "Farmahem"
    if "ППК" in c or "PP CoA" in c or "Natural Products" in l or l == "CNP":
        return "CNP"
    if "in-house" in l.lower() or "Purely Plant" in l:
        return "in-house"
    return "other"


def candidates(block):
    """Every loss-on-drying document in a lot's block: (source, date, code, lab, value).

    A stability timepoint measures the lot ageing and never sources a certificate; a starred
    sample's certificate is real data that never certifies.
    """
    out = []
    for cert in (block.get("certs") or []):
        if cert.get("stab") or TS.is_experimental(cert.get("code")):
            continue
        v = (cert.get("vals") or {}).get("I")
        if not v or str(v).strip() in ("", "/", "—"):
            continue
        d = day(cert.get("date"))
        if d is None:
            continue
        out.append((source_of(cert.get("code"), cert.get("lab")), d, cert.get("code"),
                    cert.get("lab"), str(v).strip()))
    return out


def index(reg):
    out = {}
    for b in reg:
        c = candidates(b)
        if not c:
            continue
        for k in {str(b.get("pn") or "").strip(), str(b.get("cb") or "").strip()} - {""}:
            out.setdefault(k, []).extend(c)
    return out


def best(pool, issue, release):
    """The document the ruling picks: the highest-ranked laboratory, then its latest page.

    `release` refuses a retest document (the ruling of 10.09.2026); every certificate refuses
    a document issued after its own day (v35).
    """
    live = [x for x in pool if x[1] <= issue]
    if release:
        live = [x for x in live if not TS.is_retest_only(x[2])]
    for want in RANK:
        same = [x for x in live if x[0] == want]
        if same:
            return max(same, key=lambda x: x[1])
    return None


def outranks(a, b):
    """True where laboratory `a` is the one the ruling prefers over `b`.

    >>> outranks("Farmahem", "CNP"), outranks("CNP", "Farmahem")
    (True, False)
    >>> outranks("CNP", "in-house"), outranks("Farmahem", "other")
    (True, True)
    >>> outranks("CNP", "CNP")
    False
    """
    ra = RANK.index(a) if a in RANK else len(RANK)
    rb = RANK.index(b) if b in RANK else len(RANK)
    return ra < rb


def apply(data):
    """Returns (filled, promoted, no_document, undated) — what changed and what could not."""
    have = index(data["reg"])
    filled, promoted, nodoc, undated = [], [], [], []
    for c in data["coqs"]:
        row = next((r for r in c["rows"] if r["no"] == "8"), None)
        if row is None:
            continue
        was_res = str(row.get("res") or "\u2014").strip()
        blank = was_res in NOT_TESTED or "not tested" in was_res.lower()
        iss = day(c.get("issue"))
        if iss is None:
            # a certificate whose issue date is not yet a day (the two lots still "at issue")
            # cannot be held against the date rule, so nothing is written to it — and it is
            # named rather than skipped in silence.
            if blank:
                undated.append((c.get("regcode"), c.get("pp") or c.get("cb"),
                                str(c.get("issue") or "\u2014")))
            continue
        pool = (have.get(str(c.get("pp") or "").strip())
                or have.get(str(c.get("cb") or "").strip()) or [])
        pick = best(pool, iss, not c.get("supersedes"))
        if pick is None:
            if blank:
                nodoc.append((c.get("regcode"), c.get("pp") or c.get("cb"), c.get("strain")))
            continue
        src, d, code, lab, val = pick
        if not blank and not outranks(src, source_of(row.get("doc"), row.get("lab"))):
            continue                      # already on the best laboratory the lot has
        record = (c.get("regcode"), c.get("pp") or c.get("cb"), was_res if not blank else "\u2014",
                  row.get("doc") or "\u2014", val, code, d.strftime("%d.%m.%Y"), src)
        row["res"], row["doc"] = val, code
        row["dd"], row["lab"] = d.strftime("%d.%m.%Y"), lab or src
        row["fam"] = "Farmahem \u2014 loss on drying" if src == "Farmahem" else row.get("fam") or ""
        row["st"] = "covered"
        (filled if blank else promoted).append(record)
    return filled, promoted, nodoc, undated


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    filled, promoted, nodoc, undated = apply(data)
    print("blank #8 filled from a document the lot has: %d" % len(filled))
    for r in filled:
        print("   %-16s %-13s  ->  %s %s of %s (%s)" % (r[0], r[1], r[4], r[5], r[6], r[7]))
    print("citations moved to the laboratory the ruling prefers: %d" % len(promoted))
    for r in promoted:
        print("   %-16s %-13s  %s %s  ->  %s %s of %s (%s)"
              % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
    print("certificates with no loss-on-drying document anywhere: %d" % len(nodoc))
    for r in nodoc:
        print("   %-16s %-13s %s" % r)
    print("certificates with no issue date yet, so nothing written: %d" % len(undated))
    for r in undated:
        print("   %-16s %-13s issue %s" % r)
    if not a.dry_run and (filled or promoted):
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
