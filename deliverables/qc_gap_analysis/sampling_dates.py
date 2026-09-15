#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""When each retest campaign was sampled, and when its internal certificates issue.

    python3 deliverables/qc_gap_analysis/sampling_dates.py     # self-test + the calendar

The owner's rulings of 15.09.2026, which give the retest rounds the dates the
record did not hold:

* The QP's retest campaign was sampled in **three campaigns**, one per delivery
  tranche. The internal certificate of analysis for identification A,
  identification B and foreign matter is tested — start and end — **on the day the
  batch was sampled**, and the campaign's internal certificates are all **issued on
  one day, two or three days after the campaign's last sampling day**.
* **Tranche 1** was sampled in the week 25.07.2026 falls in, from Tuesday to
  Friday, "almost evenly but not so": 21.07 to 24.07.2026, split 6 / 5 / 5 / 5.
  Farmahem received the cannabinoid samples on Monday 27.07.2026 and the
  mycotoxin samples on 29.07.2026 (the 197-series certificates print the date of
  receipt), so the sampling precedes the receipt as it must.
* **Tranches 2 and 3** were sampled "a couple of days before the date of admission
  of the sample" at Farmahem — the date of receipt every 220- and 227-series
  certificate prints: Monday 17.08.2026 and Monday 24.08.2026. Three days of the
  week before each receipt, Wednesday to Friday, so that the sample leaves the
  site for the laboratory after the last sampling day: 12–14.08.2026 (11 / 11 /
  10) and 19–21.08.2026 (10 / 10 / 10).
* Within a campaign the batches take the days **in the order of the laboratory's
  certificate numbers** — 197-1 … 197-6 on the first day, 197-7 … 197-11 on the
  second, and so on — because that running number is a fact the certificate
  carries and the laboratory assigned it in the order the samples were logged. A
  batch's К and М certificates share one number, so a batch has one sampling day.

A campaign is identified by its certificate series (`testing_series.series_of`),
never by a delivery list: the tranche lists are delivery groupings and the
laboratory tested batches that are on none of them.
"""
import datetime
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import testing_series as TS                                          # noqa: E402

CAMPAIGNS = OrderedDict((
    ("197", {"tranche": 1,
             "days": ("21.07.2026", "22.07.2026", "23.07.2026", "24.07.2026"),
             "split": (6, 5, 5, 5), "issued": "27.07.2026",
             "received": "27.07.2026 (cannabinoids), 29.07.2026 (mycotoxins)",
             "certificates": 21}),
    ("220", {"tranche": 2,
             "days": ("12.08.2026", "13.08.2026", "14.08.2026"),
             "split": (11, 11, 10), "issued": "17.08.2026",
             "received": "17.08.2026", "certificates": 32}),
    ("227", {"tranche": 3,
             "days": ("19.08.2026", "20.08.2026", "21.08.2026"),
             "split": (10, 10, 10), "issued": "24.08.2026",
             "received": "24.08.2026", "certificates": 30}),
))


def _d(s):
    return datetime.datetime.strptime(s, "%d.%m.%Y").date()


def _check():
    """The calendar is internally consistent, or nothing here may be used."""
    for series, c in CAMPAIGNS.items():
        assert len(c["days"]) == len(c["split"]), series
        assert sum(c["split"]) == c["certificates"], series
        days = [_d(x) for x in c["days"]]
        assert days == sorted(days) and all(x.weekday() < 5 for x in days), series
        gap = (_d(c["issued"]) - days[-1]).days
        assert 2 <= gap <= 3, (series, gap)
        assert _d(c["issued"]).weekday() < 5, series


_check()


def sampling_day(code):
    """The day the batch behind this re-analysis certificate was sampled.

    >>> sampling_day("197-1-К/26"), sampling_day("197-6-К/26"), sampling_day("197-7-М/26")
    ('21.07.2026', '21.07.2026', '22.07.2026')
    >>> sampling_day("197-21-М/26"), sampling_day("220-11-М/26"), sampling_day("220-12-М/26")
    ('24.07.2026', '12.08.2026', '13.08.2026')
    >>> sampling_day("220-32-М/26"), sampling_day("227-10-K/26"), sampling_day("227-30-K/26")
    ('14.08.2026', '19.08.2026', '21.08.2026')
    >>> sampling_day("220-33-М/26") is None, sampling_day("ППК25174") is None
    (True, True)
    """
    series, n = TS.series_of(code), TS.number_of(code)
    if series not in CAMPAIGNS or not n:
        return None
    c = CAMPAIGNS[series]
    upto = 0
    for day, count in zip(c["days"], c["split"]):
        upto += count
        if n <= upto:
            return day
    return None            # a certificate beyond the campaign's count: a new fact, not a guess


def icoa_issue_day(series):
    """When the campaign's internal certificates are issued — one day for all.

    >>> icoa_issue_day("197"), icoa_issue_day("227"), icoa_issue_day("051")
    ('27.07.2026', '24.08.2026', None)
    """
    c = CAMPAIGNS.get(series)
    return c["issued"] if c else None


def label(series):
    """The campaign as a sheet names it.

    >>> label("197"), label("220")
    ('Tranche 1 (sampled 21–24.07.2026)', 'Tranche 2 (sampled 12–14.08.2026)')
    >>> label("x") is None
    True
    """
    c = CAMPAIGNS.get(series)
    if not c:
        return None
    a, b = c["days"][0], c["days"][-1]
    return "Tranche %d (sampled %s–%s)" % (c["tranche"], a[:2], b)


def campaign_of(round_):
    """The campaign a testing round belongs to, from the certificates in it.

    >>> campaign_of({"E": [{"code": "197-3-К/26"}], "O": [{"code": "197-3-М/26"}]})
    '197'
    >>> campaign_of({"E": [{"code": "ППК26059"}]}) is None
    True
    """
    found = {TS.series_of(c.get("code", "")) for cells in (round_ or {}).values() for c in cells}
    found.discard(None)
    return min(found) if found else None


def retest_dates(round_):
    """(sampled, issued, series) for a campaign round; (None, None, None) otherwise.

    The sampling day comes from the round's own certificate numbers; where the
    round's certificates would name two days, the earlier is the sampling and the
    caller may flag the difference.

    >>> retest_dates({"E": [{"code": "197-11-К/26"}], "O": [{"code": "197-11-М/26"}]})
    ('22.07.2026', '27.07.2026', '197')
    >>> retest_dates({"O": [{"code": "220-32-М/26"}]})
    ('14.08.2026', '17.08.2026', '220')
    >>> retest_dates({"E": [{"code": "ППК26059"}]})
    (None, None, None)
    """
    series = campaign_of(round_)
    if not series:
        return None, None, None
    days = sorted({sampling_day(c["code"]) for cells in round_.values() for c in cells
                   if TS.series_of(c.get("code", "")) == series and sampling_day(c["code"])},
                  key=TS.key)
    return (days[0] if days else None), icoa_issue_day(series), series


def calendar():
    """Every certificate number of every campaign with its sampling day."""
    out = []
    for series, c in CAMPAIGNS.items():
        n = 0
        for day, count in zip(c["days"], c["split"]):
            out.append((series, day, ["%s-%d" % (series, n + i + 1) for i in range(count)]))
            n += count
    return out


def main(argv):
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        return 1
    for series, c in CAMPAIGNS.items():
        print("%s — %s: received by Farmahem %s; internal certificates issued %s"
              % (series, label(series), c["received"], c["issued"]))
        for s, day, codes in calendar():
            if s == series:
                print("    %s  %s (%s)  %s … %s" % (day, _d(day).strftime("%A"), len(codes), codes[0], codes[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
