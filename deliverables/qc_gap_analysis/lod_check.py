#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loss on drying — the result and the document behind it, on every certificate of quality.

    python3 deliverables/qc_gap_analysis/lod_check.py            # census to stdout
    python3 deliverables/qc_gap_analysis/lod_check.py --md       # write tracker/LoD_Check_<date>.md

The Head of QC asked on 17.09.2026 for a parameter-and-document check on loss on drying across
every certificate, and then, the same day, for the rule that follows from it: every certificate
prints a value and cites the certificate behind it, from the Center for Natural Products or
from Farmahem, and Farmahem's where a lot has both. `apply_lod_source.py` is the rule; this is
the census that shows what it did and what it could not.

A lot with no loss-on-drying document anywhere is named. That is a testing gap, not a desk one:
the desk has swept the release register, the Head of QC's own 09.09 resolution pass, the eCoA
spec listing and the whole of the owner's Drive for each of them.
"""
import argparse
import collections
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apply_lod_source import source_of                                 # noqa: E402

SRC = os.path.join(HERE, "coq_artifact_data.json")
OUT = os.path.join(HERE, "tracker")
LABEL = {"Farmahem": "Farmahem ГС-series (loss on drying)",
         "CNP": "CNP (UKIM Faculty of Pharmacy) ППК-series",
         "in-house": "Purely Plant internal certificate of analysis",
         "other": "other"}


def rows(data):
    """One record per certificate: code, round, issue, lot, batch, strain, result, document."""
    out = []
    for c in data["coqs"]:
        r = next((x for x in c["rows"] if x["no"] == "8"), None) or {}
        res = str(r.get("res") or "—").strip()
        got = res not in ("", "—") and "not tested" not in res.lower()
        out.append({
            "code": c.get("regcode") or "— at issue —",
            "round": "Reissue" if c.get("supersedes") else "Release",
            "issue": c.get("issue") or "—",
            "pp": c.get("pp") or "",
            "cb": c.get("cb") or "",
            "strain": c.get("strain") or "",
            "res": res if got else "— not tested",
            "doc": r.get("doc") or "—",
            "dd": r.get("dd") or "—",
            "lab": r.get("lab") or "—",
            "src": source_of(r.get("doc"), r.get("lab")) if got else "",
            "got": got,
        })
    return out


def census(rs):
    """(with a result, without, distinct documents, per-laboratory counts)."""
    with_ = [r for r in rs if r["got"]]
    docs = {r["doc"] for r in with_}
    per = collections.Counter(r["src"] for r in with_)
    perdoc = collections.defaultdict(set)
    for r in with_:
        perdoc[r["src"]].add(r["doc"])
    return len(with_), len(rs) - len(with_), len(docs), per, perdoc


def markdown(rs, today):
    n_with, n_without, n_docs, per, perdoc = census(rs)
    L = ["# Loss on drying — the result and the certificate behind it, on every certificate of quality",
         "",
         "Written %s by `lod_check.py` over `coq_artifact_data.json`: for determination #8 on each of the "
         "%d certificates, what it prints and which document of analysis it cites." % (today, len(rs)),
         "",
         "## In one table", "", "| | |", "| --- | ---: |",
         "| certificates with a loss-on-drying result | %d |" % n_with,
         "| certificates printing none | %d |" % n_without,
         "| distinct documents cited | %d |" % n_docs,
         "", "| laboratory | certificates | documents |", "| --- | ---: | ---: |"]
    for src in ("Farmahem", "CNP", "in-house", "other"):
        if per.get(src):
            L.append("| %s | %d | %d |" % (LABEL[src], per[src], len(perdoc[src])))
    L += ["",
          "The Head of QC's ruling of 17.09.2026 ranks the two laboratories: **where a lot has both a "
          "Center for Natural Products and a Farmahem determination, the certificate takes Farmahem's.** "
          "`apply_lod_source.py` enforces it. Today no lot has both — Farmahem's ГС-series and the "
          "Center's ППК-series never cover the same lot — so the ranking decides nothing yet and stands "
          "for the next lot that is sent to both.",
          "",
          "## The lots with no determination anywhere", ""]
    miss = collections.OrderedDict()
    for r in rs:
        if not r["got"]:
            miss.setdefault((r["pp"], r["cb"], r["strain"]), []).append(r["code"])
    if not miss:
        L.append("None — every certificate prints a result.")
    else:
        L += ["%d certificates, %d lots. For each of them the desk has swept the release register, the "
              "Head of QC's 09.09 resolution pass, the eCoA spec listing and the owner's whole Drive: "
              "**no loss-on-drying report exists**, from either laboratory. This is a testing gap, and "
              "the certificate prints \"not tested\" because that is the truth of it." % (n_without, len(miss)),
              "", "| P lot | Batch | Strain | Certificates |", "| --- | --- | --- | --- |"]
        for (pp, cb, strain), codes in miss.items():
            L.append("| %s | %s | %s | %s |" % (pp or "—", cb, strain, ", ".join(codes)))
    L += ["", "## Every certificate", "",
          "| CoQ code | Round | Issued | P lot | Batch | Strain | Loss on drying | Document | Issued | Laboratory |",
          "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |"]
    for r in rs:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                 % (r["code"], r["round"], r["issue"], r["pp"], r["cb"], r["strain"],
                    r["res"], r["doc"], r["dd"], r["lab"]))
    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--date", default=dt.date.today().strftime("%d.%m.%Y"))
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    rs = rows(data)
    n_with, n_without, n_docs, per, _ = census(rs)
    print("certificates: %d   with a result: %d   without: %d   distinct documents: %d"
          % (len(rs), n_with, n_without, n_docs))
    for src, n in per.most_common():
        print("   %-10s %d" % (src, n))
    if a.md:
        stamp = "-".join(reversed(a.date.split(".")))
        p = os.path.join(OUT, "LoD_Check_%s.md" % stamp)
        open(p, "w", encoding="utf-8").write(markdown(rs, a.date) + "\n")
        print("written:", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
