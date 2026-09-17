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
* **A retest round holds only the parameters that were retested.** Nothing is
  copied forward into the round. What the certificate of quality PRINTS for the
  parameters a retest did not cover is a separate rule (owner, 15.09.2026: the
  initial result, from the release certificate) and lives in build_coq_schedule.

Ties are release testing. Where two certificates carry the same parameter on the
same date, neither is "after" the other, so both are initial and neither creates a
retest — a laboratory splitting one day's work across two documents is not a
second testing period.

**A re-analysis certificate is never release testing.** Owner, 10.09.2026 (220-),
12.09.2026 (227-, "all of these results for potency are from retests") and
15.09.2026 (the sampling campaigns): Farmahem's 197-, 220- and 227- series are the
retest campaigns of Tranches 1, 2 and 3, sampled on dates the owner set. The
per-parameter rule alone put such a certificate in the RELEASE round wherever it
happened to be the parameter's first result on file — a batch whose only
mycotoxin result is its Tranche 2 certificate had no retest round at all, and
seven Tranche 1 lots whose register block holds nothing but the re-analysis had
none either. `rounds()` therefore places every campaign certificate in a round of
its own, one per campaign, after the rounds the rest of the record makes; the
release round may then be empty, and a consumer skips an empty round.
`REANALYSIS_SERIES` is the one list of those series; `build_coq_schedule.family()`
and `is_reanalysis()` there read it from here.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Post-release re-analysis series — the retest campaigns. 197- was the only one the
# desk knew; the owner ruled on 10.09.2026 that 220- is the same thing and on
# 12.09.2026 that the Tranche 3 227-K/26 potency certificates are retests too.
REANALYSIS_SERIES = ("197-", "220-", "227-")
_REAN_RX = re.compile(r"^\s*(%s)(\d{1,3})-[КKМM](?:[/-]\d\d)?\s*$"
                      % "|".join(re.escape(s) for s in REANALYSIS_SERIES))


# The IJZ-MB campaign delivery of 25/26.08.2026 — the owner's ruling of 10.09.2026, on the
# CoQ Register's note since: "the IJZ-MB delivery of 25/26.08.2026 (certificates of 31.08
# and 01.09.2026, 68 to 436 days after packaging) is one campaign sampling and every
# certificate in it is a retest document, for the post-SOP lots too".
#
# It is named by its certificates and not by a series, which is the exception to the rule
# `sampling_dates` states — a campaign is identified by its certificate series, never by a
# delivery list. This laboratory's codes are its own running numbers and carry no series,
# so there is nothing else to name it by. Nor is it a CAMPAIGN in `sampling_dates`: its
# certificates issue over TWO days, five and six days after the sampling, which the
# calendar's invariant for the three Farmahem campaigns (one issue day, two or three days
# after the last sampling day) does not admit. So it is exactly what the ruling says and
# no more: these certificates are RETEST documents, and none of them certifies a release
# certificate of quality.
#
# Frozen from intake_IJZMB_2026-09-16/reads_IJZMB.json on 16.09.2026; the 30 codes are the
# laboratory numbers on the pages, whose SHA-256 the split manifest records. Two more were
# added on 17.09.2026 — 534/1065/26 and 535/1066/26, the P050212 and P050222 pages of the same
# delivery (same letter 03-500/1 of 24.08.2026, requests 325 and 326/2026 beside this
# intake's 324/2026), which fell outside the 536-565 range the first intake was scoped to and
# came in through intake_IJZMB2_2026-09-17. They are the same campaign, so they are the same
# kind of document: retest, never release.
RETEST_ONLY = frozenset((
    "534/1065/26",
    "535/1066/26",
    "536/1067/26",
    "537/1068/26",
    "538/1069/26",
    "539/1070/26",
    "540/1071/26",
    "541/1072/26",
    "542/1073/26",
    "543/1074/26",
    "544/1075/26",
    "545/1076/26",
    "546/1077/26",
    "547/1078/26",
    "548/1079/26",
    "549/1080/26",
    "550/1081/26",
    "551/1082/26",
    "552/1083/26",
    "553/1084/26",
    "554/1085/26",
    "555/1086/26",
    "556/1087/26",
    "557/1088/26",
    "558/1089/26",
    "559/1090/26",
    "560/1091/26",
    "561/1092/26",
    "562/1093/26",
    "563/1094/26",
    "564/1095/26",
    "565/1096/26",
))


def is_retest_only(code):
    """True for a certificate the owner has ruled a retest document although its code
    carries no re-analysis series — the IJZ-MB delivery of 25/26.08.2026.

    >>> is_retest_only("548/1079/26"), is_retest_only("548-1079-26")
    (True, True)
    >>> is_retest_only("1157/2058/25"), is_retest_only(""), is_retest_only(None)
    (False, False, False)
    """
    c = re.sub(r"[\s\-/_.]+", "/", str(code or "").strip()).strip("/")
    return c in _RETEST_ONLY_KEYS


_RETEST_ONLY_KEYS = frozenset(re.sub(r"[\s\-/_.]+", "/", c).strip("/") for c in RETEST_ONLY)


# ---------------------------------------------------------------- experimental samples
# Owner's ruling, 16.09.2026, on the starred cultivation batches:
#
#   "The asterisk is probably some experiment and is generally not the result that will go
#    for the batch release official documentation. If both THC results are assigned with the
#    same P number production batch, that means it is the same batch, but two samples have
#    been sent for the parameter. You will NOT ignore the value and data with the asterisk —
#    you will include it in calculation statistics and all — but in the CoQ you will take the
#    other value and corresponding certificate."
#
# So a starred sample is NOT a second lot. It is a second SAMPLE of the same packaged lot,
# sent for a limited panel outside the release testing. Three consequences, and the third is
# the one this module enforces:
#
#   * its results are real and stay in the record, on the tracker and in every statistic;
#   * the lot is identified by its P number, not by the spelling of its cultivation batch;
#   * it never sources a certificate of quality — where a determination has both, the
#     certificate takes the unstarred certificate's value and cites its certificate.
#
# This is the third class of document that is real data and never certifies a release,
# beside the stability timepoints the register marks and RETEST_ONLY above.
#
# The list is explicit rather than derived because the mark is not in the release register:
# ППК26065 sits in a block labelled JD112501 with no star. The star is on the certificate's
# own page ("серија: JD112501*", read 16.09.2026) and in the eCoA scan's file name
# (110526_ППК26065_CNP_JD112501＊-P060212.pdf). Its unstarred pair ППК26063 carries the same
# lot P060212, the same sample description, the same delivery date of 21.04.2026 and the same
# DAB method — the batch number is the only difference between the two pages.
EXPERIMENTAL = (
    "ППК26065",          # JD112501＊ / P060212 — Total THC 13.93 %, loss on drying 6.38 %;
                         # the release arm is ППК26063, 19.64 % and 6.69 %
    "306/0550/26",       # JD112501＊ / P060212 — IJZ-MB microbiology of 28.04.2026, TAMC 1 × 10⁴;
                         # the release arm is 307/0551/26, TAMC 2,6 × 10³ (intake_IJZ0426_2026-09-16)
    "2365/2026",         # JD112501＊ / P060212 — IJZ contaminants of 30.04.2026, Pb 0.0109 mg/kg;
                         # the release arm is 2361/2026, Pb 0.022 mg/kg (intake_IJZ0426_2026-09-16)
)


def is_experimental(code):
    """True for a certificate of a starred sample: real data, never certifying a release.

    >>> is_experimental("ППК26065")
    True
    >>> is_experimental("ППК26063"), is_experimental(""), is_experimental(None)
    (False, False, False)
    """
    c = re.sub(r"[\s\-/_.]+", "/", str(code or "").strip()).strip("/")
    return c in _EXPERIMENTAL_KEYS


_EXPERIMENTAL_KEYS = frozenset(re.sub(r"[\s\-/_.]+", "/", c).strip("/") for c in EXPERIMENTAL)


def is_reanalysis(code):
    """True for a post-release re-analysis certificate — what a reissue rests on.

    The shape is Farmahem's: series, running number, К or М, year. An IPH
    microbiology number such as 197-0350-25 shares the prefix and is not one.

    >>> is_reanalysis("197-11-К/26"), is_reanalysis("ППК25174")
    (True, False)
    >>> is_reanalysis("220-16-K/26"), is_reanalysis("227-1-K-26"), is_reanalysis("197-0350-25")
    (True, True, False)
    >>> is_reanalysis(""), is_reanalysis(None)
    (False, False)
    """
    return bool(_REAN_RX.match(str(code or "")))


def series_of(code):
    """The campaign a re-analysis certificate belongs to, as its series prefix.

    >>> series_of("197-11-К/26"), series_of("220-32-М/26"), series_of("227-1-K-26")
    ('197', '220', '227')
    >>> series_of("ППК25174") is None
    True
    """
    m = _REAN_RX.match(str(code or ""))
    return m.group(1).rstrip("-") if m else None


def number_of(code):
    """The running number inside a re-analysis certificate code.

    >>> number_of("197-11-К/26"), number_of("220-3-М/26")
    (11, 3)
    >>> number_of("ППК25174") is None
    True
    """
    m = _REAN_RX.match(str(code or ""))
    return int(m.group(2)) if m else None


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
    rs = rounds(cells_by_param)
    release = dict(rs[0]) if rs else {}
    retests = {}
    for r in rs[1:]:
        for param, cells in r.items():
            retests.setdefault(param, []).extend(cells)
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
    Round 0 is the release round. A re-analysis certificate (`is_reanalysis`)
    never sits in it: each campaign's certificates form one round of their own,
    appended after the rounds the rest of the record makes, in the order of the
    campaigns' dates. A batch whose record holds nothing but a campaign therefore
    has an EMPTY release round — a fact, not a gap, and the consumer skips it.

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
    >>> k = {"date": "07.08.2026", "code": "197-1-К/26"}
    >>> m = {"date": "10.08.2026", "code": "197-1-М/26"}
    >>> r = rounds({"E": [{"date": "26.02.2025", "code": "ППК25050"}, k], "G": [k], "O": [m]})
    >>> len(r), sorted(r[0]), sorted(r[1])
    (2, ['E'], ['E', 'G', 'O'])
    >>> r = rounds({"O": [{"date": "11.09.2026", "code": "220-9-М/26"}]})
    >>> r[0], sorted(r[1])
    ({}, ['O'])
    """
    out = []
    campaigns = {}
    for param, cells in cells_by_param.items():
        own = [c for c in cells if not is_reanalysis(c.get("code", ""))]
        for c in cells:
            if is_reanalysis(c.get("code", "")):
                campaigns.setdefault(series_of(c["code"]), {}).setdefault(param, []).append(c)
        # A certificate of the IJZ-MB delivery of 25/26.08.2026 is a retest document by the
        # owner's ruling, whatever its position in the parameter's history: for a lot whose
        # block holds no earlier microbiology it would otherwise BE the release result and
        # date the release certificate after it — which is what put P060342's release CoQ on
        # 31.08.2026 in the first v34 build.
        forced = [c for c in own if is_retest_only(c.get("code", ""))]
        if forced:
            own = [c for c in own if not is_retest_only(c.get("code", ""))]
        rel, ret = split(own)
        ret = sorted(ret + forced, key=lambda c: key(c.get("date", "")))
        for i, group in enumerate([rel] + [[c] for c in ret]):
            if not group:
                continue
            while len(out) <= i:
                out.append({})
            out[i].setdefault(param, []).extend(group)
    if campaigns and not out:
        out.append({})            # the release round exists and is empty
    for s in sorted(campaigns, key=lambda s: key(last_date(campaigns[s]) or "")):
        out.append(campaigns[s])
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
