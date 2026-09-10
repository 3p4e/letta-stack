#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which testing is the release testing, and which is a retest.

    python3 deliverables/qc_gap_analysis/testing_series.py     # self-test + census

Owner's ruling, 10.09.2026:

    "the first value of a parameter obtained would be counted as an initial
     quality control testing, and every other point of testing for any of the
     parameters from a batch will be considered as a retest."

That is a rule about **dates**, not about document codes, and it replaces the one
the desk had been using. The desk read the series a certificate's number belongs
to — 197- and 220- meant post-release, everything else meant release — which is a
proxy, and a proxy fails wherever the numbering does. This reads the record
instead: per batch, **per parameter**, the earliest result on file is the release
result and every later one belongs to a retest.

Two things follow that the desk could not say before:

* **A batch has a retest only if some parameter was actually tested twice.** The
  owner's own description — "comes a moment when production batches do not have a
  retest, and the only record is the initial testing record" — is not a rule that
  has to be written down anywhere. It falls out of the data.
* **A retest certificate carries only the parameters that were retested.** Nothing
  is copied forward from the release testing to fill it out.

Ties are release testing. Where two certificates carry the same parameter on the
same date, neither is "after" the other, so both are initial and neither creates a
retest — a laboratory splitting one day's work across two documents is not a
second testing period.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def key(date):
    """A DD.MM.YYYY date as a sortable string; anything unreadable sorts last.

    >>> key("04.03.2025") < key("07.08.2026")
    True
    >>> key("") == key("not a date") == "99999999"
    True
    """
    m = re.match(r"^\s*(\d{2})\.(\d{2})\.(\d{4})\s*$", date or "")
    return (m.group(3) + m.group(2) + m.group(1)) if m else "99999999"


def split(cells):
    """One parameter's results, split into (release, retests).

    ``cells`` is a list of records carrying at least ``date``. The earliest date
    is the release testing; everything later is a retest, in date order. Records
    with no readable date cannot be placed in time and are returned as retests
    only if something else is earlier — never as the release result.

    >>> a = {"date": "07.08.2026", "code": "197-2-K/26"}
    >>> b = {"date": "04.03.2025", "code": "PPK25012"}
    >>> rel, re_ = split([a, b])
    >>> [r["code"] for r in rel], [r["code"] for r in re_]
    (['PPK25012'], ['197-2-K/26'])
    >>> rel, re_ = split([{"date": "01.02.2026", "code": "x"},
    ...                   {"date": "01.02.2026", "code": "y"}])
    >>> [r["code"] for r in rel], re_
    (['x', 'y'], [])
    >>> split([])
    ([], [])
    >>> rel, re_ = split([{"date": "", "code": "undated"}])
    >>> [r["code"] for r in rel], re_
    (['undated'], [])
    """
    if not cells:
        return [], []
    ordered = sorted(cells, key=lambda c: key(c.get("date", "")))
    first = key(ordered[0].get("date", ""))
    release = [c for c in ordered if key(c.get("date", "")) == first]
    return release, [c for c in ordered if key(c.get("date", "")) != first]


def batch(cells_by_param):
    """A whole batch: {parameter: [records]} -> (release, retests), same shape.

    >>> rel, ret = batch({"4": [{"date": "04.03.2025"}, {"date": "07.08.2026"}],
    ...                   "8": [{"date": "05.03.2025"}]})
    >>> sorted(rel), sorted(ret)
    (['4', '8'], ['4'])
    >>> [c["date"] for c in ret["4"]]
    ['07.08.2026']
    """
    release, retests = {}, {}
    for param, cells in cells_by_param.items():
        rel, ret = split(cells)
        if rel:
            release[param] = rel
        if ret:
            retests[param] = ret
    return release, retests


def has_retest(cells_by_param):
    """Was any parameter of this batch tested more than once?

    >>> has_retest({"4": [{"date": "04.03.2025"}, {"date": "07.08.2026"}]})
    True
    >>> has_retest({"4": [{"date": "04.03.2025"}], "8": [{"date": "05.03.2025"}]})
    False
    >>> has_retest({})
    False
    """
    return bool(batch(cells_by_param)[1])


def periods(cells_by_param):
    """The distinct testing dates of a batch, earliest first — its testing periods.

    >>> periods({"4": [{"date": "07.08.2026"}, {"date": "04.03.2025"}],
    ...          "8": [{"date": "04.03.2025"}]})
    ['04.03.2025', '07.08.2026']
    """
    seen = {}
    for cells in cells_by_param.values():
        for c in cells:
            d = (c.get("date") or "").strip()
            if d:
                seen[d] = key(d)
    return [d for d, _ in sorted(seen.items(), key=lambda kv: kv[1])]


def rounds(cells_by_param):
    """Every result placed in a testing ROUND — 0 is release, 1 the first retest.

    A testing period is not a single date. One release campaign has the
    cannabinoids certified on one day, microbiology on another and the metals on a
    third, and reading each distinct date as its own period would give a batch six
    certificates of quality where it has one. The owner's rule is per parameter:
    the first result a parameter has is release testing and its second is a
    retest, so a result's round is its **position in its own parameter's history**,
    not its position in the batch's calendar.

    Returns a list of rounds, each ``{parameter: [records]}``, earliest first.

    >>> r = rounds({"4": [{"date": "07.08.2026"}, {"date": "04.03.2025"}],
    ...             "8": [{"date": "05.03.2025"}],
    ...             "9": [{"date": "06.03.2025"}, {"date": "08.08.2026"}]})
    >>> len(r)
    2
    >>> sorted(r[0]), sorted(r[1])
    (['4', '8', '9'], ['4', '9'])
    >>> [c["date"] for c in r[1]["4"]]
    ['07.08.2026']
    >>> rounds({})
    []
    """
    out = []
    for param, cells in cells_by_param.items():
        rel, ret = split(cells)
        for i, group in enumerate([rel] + [[c] for c in ret]):
            if not group:
                continue
            while len(out) <= i:
                out.append({})
            out[i].setdefault(param, []).extend(group)
    return out


def last_date(round_):
    """The latest date in one round — what a certificate of quality waits for.

    >>> last_date({"4": [{"date": "04.03.2025"}], "9": [{"date": "06.03.2025"}]})
    '06.03.2025'
    >>> last_date({}) is None
    True
    """
    dates = [(c.get("date") or "").strip() for cells in round_.values() for c in cells]
    dates = [d for d in dates if key(d) != "99999999"]
    return max(dates, key=key) if dates else None


def by_parameter(entry):
    """A register batch as {parameter: [records]} — every certificate on file.

    The rule has to see the WHOLE pool for a batch, not the pool the old rule
    already split: an initial-release certificate carries only what that rule
    called release testing, so reading it back would find every batch tested once
    and no retest anywhere. `reg` in `coq_artifact_data.json` is the undivided
    record — every certificate, every parameter it reports, and its date.
    """
    out = {}
    for cert in entry.get("certs", []):
        for param in cert.get("vals", {}):
            out.setdefault(param, []).append(
                {"date": cert.get("date", ""), "code": cert.get("code", ""),
                 "lab": cert.get("lab", ""), "value": cert["vals"][param]})
    return out


def _census():
    """Every batch the desk holds, classified by this rule."""
    import json
    path = os.path.join(HERE, "coq_artifact_data.json")
    data = json.load(open(path, encoding="utf-8"))
    out = {"retest": 0, "release only": 0, "no dated record": 0}
    for entry in data.get("reg", []):
        by = by_parameter(entry)
        if not by:
            out["no dated record"] += 1
        elif has_retest(by):
            out["retest"] += 1
        else:
            out["release only"] += 1
    return out


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if not fail:
        for k, v in sorted(_census().items()):
            print("  %-16s %3d" % (k, v))
    sys.exit(1 if fail else 0)
