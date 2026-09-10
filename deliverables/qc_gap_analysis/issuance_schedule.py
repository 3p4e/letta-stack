#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""When every certificate of quality and every internal CoA is issued.

    python3 deliverables/qc_gap_analysis/issuance_schedule.py          # self-test + census
    python3 deliverables/qc_gap_analysis/issuance_schedule.py --csv    # write the register

The owner's rulings of 10.09.2026, in the order they were given, and what each one
means for a date on a document:

1. **The specification SOP took effect on 01.06.2026.** Nothing controlled by it
   can be dated before it existed, which is what the two floors below are for.
2. **The first result a parameter has is release testing; every later one is a
   retest** — `testing_series.py`. A batch therefore has as many certificates of
   quality as it has testing periods, and a batch tested once has exactly one.
3. **Identification A, Identification B and foreign matter go on ONE internal
   certificate of analysis per testing period**, tested start = end = the
   packaging date for the release period and the sampling date for a retest.
4. **A certificate of quality is issued 5–10 days after the last external
   certificate it cites.** The owner put it as a question rather than a rule —
   "how can a certificate of quality be dated earlier than the last certificate of
   analysis obtained for that batch" — and it holds for release and retest alike.
5. **Everything whose date would fall before the SOP is issued together**: the
   internal certificates on 03.06.2026 and the certificates of quality on
   06.06.2026.

`LAG_DAYS` is 7 because the owner gave a range and a register cannot hold a range;
it is the middle of 5–10 and it is one constant to change.
"""
import csv
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import testing_series as TS                                          # noqa: E402

SOP_SPEC_APPROVED = "01.06.2026"
ICOA_FLOOR = "03.06.2026"          # no internal CoA is dated before the SOP
COQ_BLANKET = "06.06.2026"         # the backlog is issued together, after them
LAG_DAYS = 7                       # the owner's "5 to 10 days", as one number
OUT = os.path.join(HERE, "issuance_schedule_2026-09-10.csv")


def parse(d):
    """DD.MM.YYYY to a date, or None.

    >>> parse("04.03.2025").isoformat()
    '2025-03-04'
    >>> parse("nonsense") is None
    True
    """
    try:
        return datetime.datetime.strptime((d or "").strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def fmt(d):
    """A date back to the one spelling every Purely Plant document uses.

    >>> fmt(datetime.date(2026, 6, 6))
    '06.06.2026'
    """
    return d.strftime("%d.%m.%Y")


def plus(d, days=LAG_DAYS):
    """The lag the owner set, applied to a date.

    >>> plus(parse("30.06.2026"))
    datetime.date(2026, 7, 7)
    """
    return d + datetime.timedelta(days=days)


def icoa_issue(tested):
    """When the internal CoA for a testing period is issued.

    Tested on the packaging (or sampling) date, issued then — unless that is
    before the SOP that governs it, in which case it joins the backlog issued
    together on 03.06.2026.

    >>> icoa_issue("04.03.2025")
    '03.06.2026'
    >>> icoa_issue("14.07.2026")
    '14.07.2026'
    >>> icoa_issue("") is None
    True
    """
    d = parse(tested)
    if d is None:
        return None
    return fmt(max(d, parse(ICOA_FLOOR)))


def coq_issue(last_external, icoa=None):
    """When a certificate of quality is issued.

    Five to ten days after the last external certificate it cites — never before
    it, and never before the internal certificate it references. Anything that
    would land before the SOP is issued with the backlog on 06.06.2026.

    >>> coq_issue("04.03.2025")
    '06.06.2026'
    >>> coq_issue("30.06.2026")
    '07.07.2026'
    >>> coq_issue("26.08.2026")
    '02.09.2026'
    >>> coq_issue("28.05.2026", icoa="03.06.2026")
    '06.06.2026'
    >>> coq_issue("") is None
    True
    """
    d = parse(last_external)
    if d is None:
        return None
    out = plus(d)
    if out < parse(COQ_BLANKET):
        out = parse(COQ_BLANKET)
    ic = parse(icoa or "")
    if ic and out < ic:
        out = plus(ic)
    return fmt(out)


def schedule(entry, packaging=""):
    """Every certificate a batch needs, in order — one row per testing period.

    Each row is ``{period, kind, tested, icoa_issue, last_external, coq_issue,
    parameters}``: ``kind`` is "initial release" for the first testing period and
    "retest" for each later one, ``tested`` is what the internal CoA carries as
    its start and end of testing, and ``parameters`` is what that period actually
    covers.
    """
    by = TS.by_parameter(entry)
    if not by:
        return []
    rows = []
    for i, round_ in enumerate(TS.rounds(by)):
        last = TS.last_date(round_)
        if not last:
            continue
        params = sorted(round_)
        # the internal CoA is tested on the packaging date for the release round
        # and on the round's own sampling date for a retest
        tested = (packaging or last) if i == 0 else last
        ic = icoa_issue(tested)
        rows.append({
            "period": last,
            "kind": "initial release" if i == 0 else ("retest %d" % i),
            "tested": tested,
            "icoa_issue": ic or "",
            "last_external": last,
            "coq_issue": coq_issue(last, ic) or "",
            "parameters": " ".join(params),
        })
    return rows


COLS = ["batch", "p_lot", "strain", "period", "kind", "tested", "icoa_issue",
        "last_external", "coq_issue", "parameters"]


def build(path=None):
    """The whole register, batch by batch."""
    data = json.load(open(path or os.path.join(HERE, "coq_artifact_data.json"),
                          encoding="utf-8"))
    packed = {}
    for c in data["coqs"]:
        if c["t"] == "initial release" and c.get("pk"):
            packed[c["cb"]] = c["pk"]
    out = []
    for entry in data.get("reg", []):
        for row in schedule(entry, packed.get(entry["cb"], "")):
            row.update({"batch": entry["cb"], "p_lot": entry.get("pn") or "",
                        "strain": entry.get("strain") or ""})
            out.append(row)
    return out


def main(argv):
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        return 1
    rows = build()
    if "--csv" in argv:
        with open(OUT, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
            wr.writeheader()
            wr.writerows(rows)
        print("%s: %d certificate(s)" % (os.path.basename(OUT), len(rows)))
    from collections import Counter
    kinds = Counter(r["kind"] for r in rows)
    print("  %d batches -> %d certificates of quality" % (
        len({r["batch"] for r in rows}), len(rows)))
    for k, v in sorted(kinds.items()):
        print("      %-16s %3d" % (k, v))
    print("  issued on the blanket date %s: %d" % (
        COQ_BLANKET, sum(1 for r in rows if r["coq_issue"] == COQ_BLANKET)))
    print("  issued chronologically after it: %d" % sum(
        1 for r in rows if r["coq_issue"] and r["coq_issue"] != COQ_BLANKET))
    print("  internal CoAs on %s: %d; later: %d" % (
        ICOA_FLOOR, sum(1 for r in rows if r["icoa_issue"] == ICOA_FLOOR),
        sum(1 for r in rows if r["icoa_issue"] and r["icoa_issue"] != ICOA_FLOOR)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
