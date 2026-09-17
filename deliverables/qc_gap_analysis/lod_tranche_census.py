#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loss on drying by tranche: who has a Farmahem page, who has only a CNP one, who has neither.

    python3 deliverables/qc_gap_analysis/lod_tranche_census.py            # to stdout
    python3 deliverables/qc_gap_analysis/lod_tranche_census.py --md       # write the report

The Head of QC, 17.09.2026: "check from the T1 and T2 tranches and even T3 for CNP eCoAs — I
need to know how many CoQs have a Farmahem eCoA for LoD testing, and what batches from T1 and
T2 don't have a Farmahem LoD eCoA, and also how many of them have a CNP eCoA with LoD testing
inside, and at the end what batches do not have either and don't have LoD tested."

The ranking is the same day's ruling, which `apply_lod_source.py` holds: **Farmahem first, then
the Center for Natural Products, then the in-house sheet.** This is the census of what that
ranking had to work with, per tranche, for the release certificate and the reissue alike.

A batch is counted once; its two certificates cite the same document unless one of them is
dated before it exists.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apply_lod_source import source_of, day                            # noqa: E402
import testing_series as TS                                            # noqa: E402

SRC = os.path.join(HERE, "coq_artifact_data.json")
SCOPES = ("tracker/coq_reissue_scope_2026-09-15.csv", "tracker/coq_draft_scope_2026-09-10.csv")


def tranches():
    """Tranche by P lot — the reissue scope first, the same bridge the build uses."""
    out = {}
    for name in SCOPES:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                lot = (r.get("p_lot") or r.get("P lot") or r.get("lot") or "").strip()
                tr = (r.get("tranche") or r.get("Tranche") or "").strip()
                if lot and tr:
                    out.setdefault(lot, tr)
    return out


def lod_documents(block):
    """Every loss-on-drying document in a lot's block: source -> [(date, code)]."""
    out = collections.defaultdict(list)
    for cert in (block.get("certs") or []):
        if cert.get("stab") or TS.is_experimental(cert.get("code")):
            continue
        v = (cert.get("vals") or {}).get("I")
        if not v or str(v).strip() in ("", "/", "—"):
            continue
        d = day(cert.get("date"))
        if d is None:
            continue
        out[source_of(cert.get("code"), cert.get("lab"))].append((d, cert.get("code"), str(v).strip()))
    return out


def survey(data):
    """One record per batch: tranche, lot, batch, strain, what it has, what its CoQs cite.

    The register block is not the whole record for this determination. Fourteen lots print a
    loss-on-drying result whose document never became a register row — it reached the
    certificate through the Head of QC's 09.09 resolution pass instead (`OI-42` counts those
    scans). So the documents a lot HAS are the register's rows **and** the documents its own
    certificates cite: anything less would report a lot as untested while its certificate
    prints a figure.
    """
    tr = tranches()
    have = {}
    for b in data["reg"]:
        docs = lod_documents(b)
        for k in {str(b.get("pn") or "").strip(), str(b.get("cb") or "").strip()} - {""}:
            for src, v in docs.items():
                have.setdefault(k, {}).setdefault(src, []).extend(v)
    for c in data["coqs"]:
        row8 = next((x for x in c["rows"] if x["no"] == "8"), {}) or {}
        res, code = str(row8.get("res") or "").strip(), str(row8.get("doc") or "").strip()
        d = day(row8.get("dd"))
        if not code or code == "\u2014" or d is None:
            continue
        if res in ("", "\u2014") or "not tested" in res.lower():
            continue
        src = source_of(code, row8.get("lab"))
        for k in {str(c.get("pp") or "").strip(), str(c.get("cb") or "").strip()} - {""}:
            pool = have.setdefault(k, {}).setdefault(src, [])
            if not any(x[1] == code for x in pool):
                pool.append((d, code, res))
    seen, rows = {}, []
    for c in data["coqs"]:
        pp, cb = str(c.get("pp") or "").strip(), str(c.get("cb") or "").strip()
        key = pp or cb
        r = seen.get(key)
        if r is None:
            docs = have.get(pp) or have.get(cb) or {}
            r = seen[key] = {
                "tranche": tr.get(pp) or tr.get(cb) or "—",
                "pp": pp, "cb": cb, "strain": c.get("strain") or "",
                "farmahem": sorted(docs.get("Farmahem") or []),
                "cnp": sorted(docs.get("CNP") or []),
                "inhouse": sorted(docs.get("in-house") or []),
                "certs": [],
            }
            rows.append(r)
        row8 = next((x for x in c["rows"] if x["no"] == "8"), {}) or {}
        res = str(row8.get("res") or "—").strip()
        got = res not in ("", "—") and "not tested" not in res.lower()
        r["certs"].append({
            "code": c.get("regcode") or "— at issue —",
            "round": "reissue" if c.get("supersedes") else "release",
            "issue": c.get("issue") or "—",
            "res": res if got else "— not tested",
            "doc": row8.get("doc") or "—",
            "dd": row8.get("dd") or "—",
            "src": source_of(row8.get("doc"), row8.get("lab")) if got else "none",
        })
    return rows


def classify(r):
    if r["farmahem"]:
        return "Farmahem"
    if r["cnp"]:
        return "CNP only"
    if r["inhouse"]:
        return "in-house only"
    return "none"


def markdown(rows, today):
    by = collections.defaultdict(list)
    for r in rows:
        by[r["tranche"]].append(r)
    order = ([t for t in ("1", "2", "3") if t in by]
             + sorted(t for t in by if t not in ("1", "2", "3")))
    tot = collections.Counter()
    per = {}
    for t in order:
        per[t] = collections.Counter(classify(r) for r in by[t])
        tot.update(per[t])
    fh = [t for t in order if per[t]["Farmahem"]]
    both = [r for r in rows if r["farmahem"] and r["cnp"]]

    L = ["# Loss on drying by tranche — Farmahem, the Center, or neither",
         "",
         "Written %s by `lod_tranche_census.py`. One row per production batch, with the document "
         "each of its two certificates cites for #8 — so this is both the census the Head of QC "
         "asked for and the check on every citation." % today,
         "",
         "A lot's documents are the release register's rows **and** the documents its own "
         "certificates cite: fourteen lots print a loss-on-drying figure whose page never became a "
         "register row, reaching the certificate through the Head of QC's 09.09 resolution pass "
         "instead (`OI-42` counts those scans). Counting only the register would report a lot as "
         "untested while its certificate prints a figure.",
         "",
         "The ranking is the Head of QC's ruling of 17.09.2026, which `apply_lod_source.py` holds: "
         "**Farmahem's ГС report first, then the Center for Natural Products' ППК page, then the "
         "in-house sheet.**",
         "", "## The count", "",
         "| tranche | batches | Farmahem ГС | CNP ППК only | in-house only | nothing at all |",
         "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for t in order:
        c = per[t]
        L.append("| %s | %d | %d | %d | %d | %d |"
                 % ("Tranche " + t if t in ("1", "2", "3") else "no tranche", len(by[t]),
                    c["Farmahem"], c["CNP only"], c["in-house only"], c["none"]))
    L.append("| **all** | **%d** | **%d** | **%d** | **%d** | **%d** |"
             % (len(rows), tot["Farmahem"], tot["CNP only"], tot["in-house only"], tot["none"]))
    L += ["",
          "**%d of the %d batches have a Farmahem ГС page** — the ruling's first choice — spread "
          "over %s. **%d have only a Center for Natural Products ППК page**, where loss on drying "
          "sits on the potency certificate rather than a report of its own. **%d have only the "
          "in-house cross-check** (P050192 and P050202), which is neither of the two laboratories "
          "the ruling names and is the only record those two lots have. **%d have nothing at all** "
          "and print \"not tested\" — `OI-53`."
          % (tot["Farmahem"], len(rows),
             ", ".join("Tranche " + t if t in ("1", "2", "3") else "no tranche" for t in fh) or "no tranche",
             tot["CNP only"], tot["in-house only"], tot["none"]),
          "",
          ("**No lot in the set has both**, so the ranking never has to choose today; it stands for "
           "the next lot sent to both." if not both else
           "**%d lot(s) have both**, and the ruling gives each of them Farmahem's figure: %s."
           % (len(both), ", ".join(r["pp"] or r["cb"] for r in both))),
          ""]
    for t in order:
        name = "Tranche " + t if t in ("1", "2", "3") else "Belonging to no tranche"
        L += ["## %s" % name, ""]
        for label, want in (
                ("Farmahem ГС — the ruling's first choice", "Farmahem"),
                ("CNP ППК only — no Farmahem page for this lot", "CNP only"),
                ("In-house only — neither laboratory has a page", "in-house only"),
                ("Nothing at all — loss on drying was never determined", "none")):
            got = [r for r in by[t] if classify(r) == want]
            if not got:
                continue
            L += ["### %s — %d batch(es)" % (label, len(got)), "",
                  "| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
            for r in sorted(got, key=lambda x: (x["pp"], x["cb"])):
                on_file = "; ".join(
                    "%s · %s" % (code, d.strftime("%d.%m.%Y"))
                    for key in ("farmahem", "cnp", "inhouse")
                    for d, code, _v in r[key]) or "— nothing —"
                cells = []
                for want_round in ("release", "reissue"):
                    c = next((x for x in r["certs"] if x["round"] == want_round), None)
                    if c is None:
                        cells += ["—", "—"]
                    else:
                        cells += [c["code"], "%s · %s = %s" % (c["doc"], c["dd"], c["res"])
                                  if c["doc"] not in ("—", "") else "— not tested"]
                L.append("| %s | %s | %s | %s | %s | %s | %s | %s |"
                         % (r["pp"] or "—", r["cb"], r["strain"], on_file, *cells))
            L.append("")
    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--date", default=dt.date.today().strftime("%d.%m.%Y"))
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    rows = survey(data)
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r["tranche"]][classify(r)] += 1
    print("%-12s %7s %10s %10s %13s %9s" % ("tranche", "batches", "Farmahem", "CNP only", "in-house", "none"))
    for t in sorted(by):
        c = by[t]
        print("%-12s %7d %10d %10d %13d %9d"
              % (t, sum(c.values()), c["Farmahem"], c["CNP only"], c["in-house only"], c["none"]))
    if a.md:
        stamp = "-".join(reversed(a.date.split(".")))
        p = os.path.join(HERE, "tracker", "LoD_By_Tranche_%s.md" % stamp)
        open(p, "w", encoding="utf-8").write(markdown(rows, a.date) + "\n")
        print("written:", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
