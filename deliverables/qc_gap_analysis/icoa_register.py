#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The standing register of Purely Plant's internal certificates of analysis.

    python3 deliverables/qc_gap_analysis/icoa_register.py          # self-test + census
    python3 deliverables/qc_gap_analysis/icoa_register.py --csv    # write the register

The owner's rulings of 10.09.2026:

* **The register encompasses every internal certificate that exists or ever
  will** — not only the ones the drafted lots happen to need.
* **In-house results are never referenced on a certificate of quality.** They are
  carried on an internal certificate of analysis, which must state the status of
  the method used. So wherever the desk's only source for a determination is an
  in-house record, the certificate of quality cites the internal certificate and
  the in-house record sits behind it.
* **Identification A, Identification B and foreign matter go on one internal
  certificate per testing round**, tested start = end = the packaging date for the
  release round and the round's sampling date for a retest.
* **One certificate for all the missing parameters** — "let's make it one
  certificate of analysis for all of the missing parameters that Purely Plant
  needs to issue" — so a round has exactly one internal certificate, whatever it
  has to cover.
* **Document codes follow the order of issuing.**

## What one certificate covers

Two things, and nothing else:

1. **Identification A, Identification B and foreign matter**, always. The owner
   states these are performed in house on the packaging date (release) or the
   sampling date (retest), on every batch.
2. **Any determination whose only result in that round is an in-house record.**

A determination with no result at all is covered by nothing. An internal
certificate can only certify what was tested, and inventing coverage for an
untested parameter is the failure this folder exists to prevent.

## The codes

`iCoA-PP_26-nnn`, the form the 09.09 pass already cites, numbered **in the order
the certificates are issued** — by issue date, then by the testing date within a
shared issue date, then by batch. The backlog shares one issue date (03.06.2026,
the specification SOP), so within it the order is the order the batches were
packaged, which is how the certificate-of-quality series is numbered too.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import testing_series as TS                                          # noqa: E402
import issuance_schedule as ISS                                      # noqa: E402

OUT = os.path.join(HERE, "icoa_register_2026-09-10.csv")
DATA = os.path.join(HERE, "coq_artifact_data.json")

# Always on the internal certificate: identity by appearance, identity by
# microscopy, and foreign matter.
ALWAYS = ("1", "2", "7")
IN_HOUSE = "Purely Plant"
PREFIX = "iCoA-PP_26-"


def is_in_house(lab):
    """Is this laboratory Purely Plant's own?

    >>> is_in_house("Purely Plant GmbH (in-house)")
    True
    >>> is_in_house("IPH — Institute of Public Health")
    False
    >>> is_in_house("")
    False
    """
    return (lab or "").strip().startswith(IN_HOUSE)


def det_key(no):
    """Determination numbers sort as numbers, not as strings.

    >>> sorted(["10.1", "2", "9.5", "1"], key=det_key)
    ['1', '2', '9.5', '10.1']
    """
    parts = []
    for piece in str(no).split("."):
        parts.append((0, int(piece)) if piece.isdigit() else (1, 0))
    return parts


def scope(round_, col2det=None):
    """What the internal certificate for this round has to cover.

    The three the owner names, plus any determination whose only result in this
    round came from Purely Plant's own laboratory. The register keys its results
    by the workbook COLUMN a determination sits in, not by the determination
    number the certificate prints, so `col2det` maps one to the other.

    >>> scope({"E": [{"lab": "IPH"}], "H": [{"lab": "Purely Plant GmbH (in-house)"}]},
    ...       {"E": ["4"], "H": ["8"]})
    ['1', '2', '7', '8']
    >>> scope({})
    ['1', '2', '7']
    >>> scope({"J": [{"lab": "Purely Plant GmbH"}, {"lab": "IPH"}]}, {"J": ["9.1"]})
    ['1', '2', '7']
    """
    col2det = col2det or {}
    out = set(ALWAYS)
    for col, cells in (round_ or {}).items():
        if cells and all(is_in_house(c.get("lab")) for c in cells):
            out.update(col2det.get(col, []))
    return sorted(out, key=det_key)


def code(seq):
    """A document code from its position in the issue order.

    >>> code(1), code(42), code(158)
    ('iCoA-PP_26-001', 'iCoA-PP_26-042', 'iCoA-PP_26-158')
    """
    return "%s%03d" % (PREFIX, seq)


COLS = ["code", "batch", "p_lot", "strain", "round", "tested_from", "tested_to",
        "issued", "parameters", "covers_in_house", "note"]


_BI = None


def _bi():
    """Batch identity — the single definition, imported the way the schedule does."""
    global _BI
    if _BI is None:
        import importlib.util
        root = os.path.dirname(os.path.dirname(HERE))
        spec = importlib.util.spec_from_file_location(
            "batch_id", os.path.join(root, "ingestion", "common", "batch_id.py"))
        _BI = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_BI)
    return _BI


def build(path=DATA):
    """Every internal certificate, in the order they are issued."""
    data = json.load(open(path, encoding="utf-8"))
    # the register keys a result by the workbook column; the certificate prints a
    # determination number. One column can carry more than one printed line.
    col2det = {}
    for det in data.get("dets", []):
        if det.get("col"):
            col2det.setdefault(det["col"], []).append(det["no"])
    # Keyed through the single batch-identity definition, never by string: the
    # register spells a batch one way and the release record another, and matching
    # raw found the packaging date for 29 of 80 batches instead of 39. The other
    # 51 fell back to the round's last external date, which put 25 internal
    # certificates' testing date on 10.08.2026 — the re-analysis date — when the
    # ruling says the packaging date.
    # `Batch Dates` in the workbook carries the packaging window for every batch —
    # 87 of them, including those with no P number — where the release record
    # holds a date only for the 48 lots that have a P number. The owner's ruling
    # of 11.09.2026 takes the FIRST day of that window, so the release record is
    # the fallback and not the source.
    packed = {}
    dates_csv = os.path.join(HERE, "batch_dates_2026-09-10.csv")
    if os.path.exists(dates_csv):
        with open(dates_csv, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                frm = (row.get("packaging_from") or "").strip()
                if not frm:
                    continue
                # Owner, 11.09.2026: take the FIRST packaging date. `Batch Dates`
                # carries a window and 26 batches were packaged over more than one
                # day; the internal certificate is dated on the day the packaging
                # started, and its testing start and end are that one date.
                win = (frm, frm)
                # the sheet keys a batch by its cultivation number and carries the
                # P number beside it; the register keys some entries by one and
                # some by the other, so both are indexed — the same reason the CoQ
                # register lookup indexes both
                for name in (row.get("batch"), row.get("p_batch")):
                    name = (name or "").strip()
                    if name and not name.startswith(("N/A", "\u2014")):
                        packed.setdefault(_bi().batch_key(name), win)
    for c in data["coqs"]:
        if c["t"] == "initial release" and c.get("pk"):
            packed.setdefault(_bi().batch_key(c["cb"]), (c["pk"], c["pk"]))
    rows = []
    for entry in data.get("reg", []):
        by = TS.by_parameter(entry)
        if not by:
            continue
        for i, round_ in enumerate(TS.rounds(by)):
            last = TS.last_date(round_)
            if not last:
                continue
            # The release round is tested on the packaging date and a retest on
            # its own sampling date. A batch with no packaging date on file was
            # never packaged as a production batch, and the desk will not put an
            # unrelated laboratory's date in its place: the certificate has no
            # testing date until someone supplies one.
            if i == 0:
                frm, to = packed.get(_bi().batch_key(entry["cb"]), ("", ""))
            else:
                frm = to = last
            tested = frm
            params = scope(round_, col2det)
            extra = [p for p in params if p not in ALWAYS]
            rows.append({
                "note": "" if tested else "no packaging date on file — testing date not stated",
                "batch": entry["cb"], "p_lot": entry.get("pn") or "",
                "strain": entry.get("strain") or "",
                "round": "initial release" if i == 0 else ("retest %d" % i),
                "tested_from": frm, "tested_to": to,
                "issued": ISS.icoa_issue(tested) or "",
                "parameters": " ".join(params),
                "covers_in_house": " ".join(extra),
            })
    # the order of issuing: the issue date, then when the work was done, then the
    # batch, so a shared issue date orders by packaging as the CoQ series does
    rows.sort(key=lambda r: (ISS.parse(r["issued"]) or ISS.parse("31.12.2099"),
                             ISS.parse(r["tested_from"]) or ISS.parse("31.12.2099"),
                             r["batch"]))
    # A code in an issue-ordered series says the certificate was issued. A
    # certificate with no testing date cannot be, so it is listed with its note
    # and takes no number — the series stays a series of issued documents.
    n = 0
    for r in rows:
        if r["issued"]:
            n += 1
            r["code"] = code(n)
        else:
            r["code"] = ""
    return rows


def by_batch_round(path=DATA, _cache={}):
    """The register keyed the way a compiler needs it: (batch key, round) -> row."""
    if path not in _cache:
        bi = _bi()
        out = {}
        for r in build(path):
            kind = "initial release" if r["round"] == "initial release" else "additional"
            out.setdefault((bi.batch_key(r["batch"]), kind), r)
        _cache[path] = out
    return _cache[path]


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
        print("%s: %d internal certificate(s)" % (os.path.basename(OUT), len(rows)))
    from collections import Counter
    print("  %d certificates over %d batches" % (len(rows), len({r["batch"] for r in rows})))
    for k, v in sorted(Counter(r["round"] for r in rows).items()):
        print("      %-18s %3d" % (k, v))
    issued = Counter(r["issued"] for r in rows)
    print("  issued on %s: %d; on %d later date(s): %d"
          % (ISS.ICOA_FLOOR, issued.get(ISS.ICOA_FLOOR, 0),
             len(issued) - (1 if ISS.ICOA_FLOOR in issued else 0),
             sum(v for k, v in issued.items() if k != ISS.ICOA_FLOOR)))
    extra = [r for r in rows if r["covers_in_house"]]
    print("  carrying an in-house determination beyond identity and foreign matter: %d"
          % len(extra))
    for r in extra[:6]:
        print("      %s  %-12s %s" % (r["code"], r["batch"], r["covers_in_house"]))
    numbered = [r for r in rows if r["code"]]
    pending = [r for r in rows if not r["code"]]
    if numbered:
        print("  numbered %s .. %s" % (numbered[0]["code"], numbered[-1]["code"]))
    if pending:
        print("  %d awaiting a packaging date, unnumbered: %s"
              % (len(pending), ", ".join(r["batch"] for r in pending)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
