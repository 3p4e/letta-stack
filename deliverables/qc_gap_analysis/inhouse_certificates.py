#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The company's own certificates of analysis, read from the page text the desk already holds.

    python3 deliverables/qc_gap_analysis/inhouse_certificates.py        # self-test + census

**Why this exists.** 117 certificates of quality over 83 lots print `to be performed
(in house)` for determination #1 Identification A (appearance), #2 Identification B
(microscopy) and #7 Foreign matter — the three the Purely Plant laboratory performs on every
batch. OI-41 records it as a missing RECORD: the desk cites the internal certificate for
those rows and has no result to print. The record was not missing. It has been in this
repository since 30.08.2026, in `ingestion/ragflow/cache/all_cert_texts_2026-08-30.json`:
**41 pages of the company's own QCCoA 001 / QCCoA 001v02 forms and Reports of Analysis**,
each printing a parameter table with Appearance, Identification, Loss on drying, Foreign
matter and the assay. Nothing on the desk had ever read them.

**The gate, and why it is stronger here than a second reading of the same page.** Every
intake on this desk writes nothing on one read. The second read for these pages is not
another pass over the same image: it is *a different laboratory's certificate, already in
the release register*. Each in-house page prints its own loss on drying and Total THC, and
for 39 of the 41 one of those numbers matches — to the digit — a value the register already
holds for the same lot from the CNP ППК-series or a Farmahem certificate:

    BG1024   in-house 5.73 % / 21.80 %   register ППК25050  5.73 % / 21.80 %
    P060052  in-house 6.77 % / 16.93 %   register ППК26005  6.77 % / 16.93 %

A page whose numbers an independent laboratory confirms is a page that was read correctly and
filed under the right lot. `corroboration()` computes that agreement per page and
`results()` **refuses every page it cannot corroborate**, so the two that no external
certificate confirms — GG1024, whose 13.34 % meets a 15.51 % that the ruling of 07.09.2026
assigns to the different lot GG1024_01, and P050272, whose cached text is half the length of
its siblings and yields no table at all — supply nothing and stay on OI-41.

**What it does not say.** No page of the 41 mentions microscopy — searched, not assumed — so
**#2 Identification B cannot be printed from these documents at all** and OI-41's #2 stays
open on every lot. The module returns #1, #3 and #7, and the measured values the certificate
carries (#4, #5, #6, #8) for a caller that wants them; it never invents #2.

**What the value means.** The in-house form prints `Confirms` where the certificate of
quality prints `Conforms | Одговара`; `result_vocabulary` owns that spelling and is applied
by the caller, not here — this module returns what the page prints.

The standing rule is untouched: an in-house result is never *referenced* on a certificate of
quality. The row cites the internal certificate of analysis (iCoA-PP_26-nnn) that carries it,
which is what the desk already does; this only supplies the result that was missing.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, "ingestion", "ragflow", "cache", "all_cert_texts_2026-08-30.json")
EXPORT = os.path.join(HERE, "coq_artifact_data.json")
sys.path.insert(0, os.path.join(ROOT, "ingestion", "common"))
from batch_id import batch_key                                    # noqa: E402

# the in-house forms, by the name the cache gives their scan
_IN_HOUSE = re.compile(r"QCCoA|NO-DOC-CODE", re.I)

# parameter row -> determination. The form's own wording, lower-cased, matched at the start
# of the cell after its leading dash. "Identification" on this form is the HPLC retention
# time, which is determination #3 — NOT #2, which is the microscopic identification and
# appears on no page of the 41.
_ROWS = [
    (r"^appearance", "1"),
    (r"^identification", "3"),
    (r"^foreign matter", "7"),
    (r"tetrahydrocannabinol", "4"),
    (r"^total cannabidiol", "5"),
    (r"^cannabinol", "6"),
    (r"^loss on drying", "8"),
]
# the two the corroboration rests on: printed on the in-house page AND on an external
# certificate of the same lot, so an independent laboratory confirms them
_CHECK = {"8": "I", "4": "E"}
_TOL = 0.0101          # a printed percentage agrees to its last digit


def _cells(text):
    """Every markdown table row of the page as a list of cells."""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.count("|") >= 4:
            c = [x.strip() for x in s.strip("|").split("|")]
            if len(c) >= 3 and not set(c[0]) <= set("- "):
                yield c


def _num(s):
    """The number a printed result carries, or None.

    >>> _num("6.77%"), _num("21,80 %"), _num("Confirms"), _num("")
    (6.77, 21.8, None, None)
    """
    m = re.search(r"(\d+[.,]\d+)", str(s or ""))
    return float(m.group(1).replace(",", ".")) if m else None


def pages():
    """Every in-house certificate the cache holds, parsed. One record per page."""
    with open(CACHE, encoding="utf-8") as fh:
        cache = json.load(fh)
    out = []
    for e in cache:
        name = e.get("name") or ""
        if not _IN_HOUSE.search(name):
            continue
        t = e.get("text") or ""
        g = lambda p: (re.search(p, t).group(1).strip() if re.search(p, t) else "")
        rec = {
            "file": name,
            "batch": g(r"Batch No:\s*([^\s|]+)"),
            "cert_no": g(r"Certificate number:\s*(\d+)"),
            "strain": g(r"Variety/Strain:\s*(.+)"),
            "manufactured": g(r"Manufacturing date:\s*(.+)"),
            "retest": g(r"Retest date:\s*(.+)"),
            "results": {},
            # searched, not assumed: the microscopic identification is on no page
            "microscopy": bool(re.search(r"microscop", t, re.I)),
        }
        for c in _cells(t):
            label = c[0].lstrip("-* ").strip().lower()
            value = c[2].strip() if len(c) > 2 else ""
            if not value or value.startswith("|"):
                continue
            for pat, no in _ROWS:
                if re.search(pat, label) and no not in rec["results"]:
                    rec["results"][no] = value
                    break
        if rec["batch"]:
            out.append(rec)
    return out


def _register_numbers():
    """{batch key: {determination: [(code, value)]}} — what the release register holds."""
    try:
        with open(EXPORT, encoding="utf-8") as fh:
            d = json.load(fh)
    except OSError:
        return {}
    out = {}
    for b in d.get("reg", []):
        for name in filter(None, (b.get("pn"), b.get("cb"))):
            k = batch_key(name)
            for c in b.get("certs", []):
                if c.get("stab"):
                    continue
                for no, col in _CHECK.items():
                    v = _num((c.get("vals") or {}).get(col))
                    if v is not None:
                        out.setdefault(k, {}).setdefault(no, []).append((c.get("code"), v))
    return out


def corroboration(rec, reg=None):
    """Which external certificates confirm this page's own numbers, and which do not.

    Returns (agreeing, differing, compared) — each a list of (determination, code, external
    value, page value).

    **A page is corroborated when SOME external certificate of its lot agrees, not when all
    of them do.** A lot is assayed more than once: the release testing, then a Farmahem
    197-, 220- or 227-series retest months later, on a second sample of a lot that has been
    ageing. Those later numbers differ from the release value by design — that is what the
    supersession sweep exists to report — so requiring every certificate to agree would
    reject 38 of 41 pages for being correct. What matters is whether the page's own numbers
    are confirmed by an independent laboratory at the round the page belongs to; a page
    confirmed by none is the one nothing may be written from.
    """
    reg = _register_numbers() if reg is None else reg
    holds = reg.get(batch_key(rec["batch"]), {})
    agree, against, compared = [], [], []
    for no, ext in holds.items():
        mine = _num(rec["results"].get(no))
        if mine is None:
            continue
        for code, v in ext:
            compared.append((no, code, v, mine))
            (agree if abs(v - mine) <= _TOL else against).append((no, code, v, mine))
    return agree, against, compared


def results(batch=None, dets=("1", "3", "7")):
    """The determinations a corroborated in-house certificate states, keyed by batch.

    With `batch`, the record for that batch alone (or {}). Every value is the page's own
    wording; a page that no external certificate confirms returns nothing at all.
    """
    reg = _register_numbers()
    out = {}
    for rec in pages():
        agree, against, compared = corroboration(rec, reg)
        if not agree:
            continue                       # confirmed by no external certificate: not a record
        vals = {no: v for no, v in rec["results"].items() if no in dets}
        if not vals:
            continue
        out[batch_key(rec["batch"])] = {
            "values": vals, "cert_no": rec["cert_no"], "file": rec["file"],
            "batch_printed": rec["batch"], "strain": rec["strain"],
            "corroborated_by": sorted({c for _, c, _, _ in agree}),
        }
    if batch is not None:
        return out.get(batch_key(batch), {})
    return out


def _census():
    reg = _register_numbers()
    ps = pages()
    ok, bad, alone, micro = [], [], [], 0
    for r in ps:
        a, x, c = corroboration(r, reg)
        micro += bool(r["microscopy"])
        (ok if a else (bad if x else alone)).append((r, a, x, c))
    print("in-house certificates in the page-text cache: %d" % len(ps))
    print("  print appearance, identification and foreign matter: %d"
          % sum(1 for r in ps if all(n in r["results"] for n in ("1", "3", "7"))))
    print("  mention a microscopic identification (#2):        %d" % micro)
    print("  corroborated by an external certificate:          %d" % len(ok))
    print("  confirmed by NO external certificate:             %d" % len(bad))
    print("  nothing external to compare:                      %d" % len(alone))
    for r, a, x, c in bad:
        print("    UNCONFIRMED  %-14s %s" % (r["batch"], "; ".join(
            "#%s page %s vs %s %s" % (no, mine, code, v) for no, code, v, mine in x)))
    for r, a, x, c in alone:
        print("    ALONE        %-14s %s" % (r["batch"], r["file"]))
    res = results()
    print("  usable records: %d lots" % len(res))
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(_census() if not f else 1)
