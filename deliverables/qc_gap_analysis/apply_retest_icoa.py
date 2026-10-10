#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A retest certificate cites the RETEST internal certificate of analysis for #1, #2 and #7.

    python3 deliverables/qc_gap_analysis/apply_retest_icoa.py [--dry-run]

The Head of QC, 17.09.2026, on the reissues: the initial certificate cites the in-house
iCoA issued at packaging, and the retest certificate cites **the internal certificate of
analysis for parameters 1, 2 and 7 on the re-sampling for retesting** — that is the
correct one. Identification A, identification B and foreign matter are determined again
on the retest sample, and the retest iCoA the register already numbers for every reissue
(`icoa_code` on the certificate; `retest N` in the iCoA register) is the document that
certifies them.

Before this, 40 reissues cited only the initial iCoA for the three and 11 cited it for
some — the 15.09 carry, applied to determinations that are in fact repeated. 24 already
cited the retest iCoA and are untouched, and 8 that cite an external CNP certificate the
master assigns for those lots keep it: that is the treatment OI-27 describes.

## What is written, and from where

For every reissue, each of #1/#2/#7 that cites a different in-house iCoA than the
certificate's own retest `icoa_code` is re-pointed to that code:

* the **date** is the retest iCoA's issue date, from `icoa_register_2026-09-10.csv` —
  the register the certificates' own numbering follows;
* the **verdict** is the master workbook's, read from its **iCoA Register** sheet by
  **lot and series**, never by code: that sheet's codes sit +1/+2 off the certificates'
  numbering (two inserted rows), and a join by code would read the wrong lot's verdict.
  Where the sheet leaves the verdict blank, the row is held and named;
* the **laboratory** is Purely Plant (in-house), and the status is the desk's `covered`
  — the carry note no longer applies to a determination that was repeated.

The date rule of v35 holds: a certificate may cite a document issued on or before its
own day and no other; a later-dated iCoA holds the row and is named.
"""
import argparse, csv, datetime as dt, io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV
SRC = os.path.join(HERE, "coq_artifact_data.json")
CSV = os.path.join(HERE, "icoa_register_2026-09-10.csv")
PARAMS = ("1", "2", "7")
COLS = {"1": "#1 Ident. A", "2": "#2 Ident. B", "7": "#7 Foreign matter"}
INHOUSE = "Purely Plant GmbH (in-house)"
BLANK = ("", "—", "-", "n/a", "none")
_EXT = re.compile(r"^(?:CNP|IPH|IJZ|FHM|Farmahem)\s+(\S+)", re.I)


def day(v):
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", str(v or ""))
    return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def newest_master():
    import glob
    found = [(int(m.group(1)), p) for p in glob.glob(os.path.join(HERE, "tracker", "CoQ_Analysis_Master_v*.xlsx"))
             for m in [re.search(r"_v(\d+)\.xlsx$", p)] if m]
    return max(found)[1]


def nk(s):
    return re.sub(r"[\s\-/_.]+", "", str(s or "")).upper()


def verdicts_by_lot_series():
    """The master's #1/#2/#7 verdicts keyed by (lot, series) — the join that survives the
    sheet's numbering offset."""
    import openpyxl
    wb = openpyxl.load_workbook(newest_master(), read_only=True, data_only=True)
    rows = list(wb["iCoA Register"].iter_rows(values_only=True)); wb.close()
    at = {x: i for i, x in enumerate(rows[0]) if x}
    out = {}
    for r in rows[1:]:
        if not r[0]:
            continue
        lot = str(r[at["P Batch"]] or "").strip(); cu = str(r[at["CU Batch"]] or "").strip()
        ser = str(r[at["Series"]] or "").strip()
        v = {p: str(r[at[COLS[p]]] or "").strip() for p in PARAMS}
        for key in (nk(lot), nk(cu)):
            if key and not key.startswith("N/A"):
                out.setdefault((key, ser), v)
    return out


def retest_series(t):
    m = re.search(r"retest\s*(\d)", t or "", re.I)
    return "retest %s" % m.group(1) if m else None


def apply(data, dry=False):
    reg = {r["code"]: r for r in csv.DictReader(io.open(CSV, encoding="utf-8"))}
    verdict = verdicts_by_lot_series()
    changed, held, kept = [], [], 0
    for c in data["coqs"]:
        if "additional testing" not in (c.get("t") or ""):
            continue
        code = str(c.get("icoa_code") or "").strip()
        entry = reg.get(code)
        iss = day(c.get("issue"))
        if not entry or iss is None:
            held.append((c.get("regcode"), "*", code, "retest iCoA not in the register")); continue
        ser = entry.get("round") or ""
        lotkey = nk(c.get("pp") or c.get("cb"))
        v = verdict.get((lotkey, ser)) or verdict.get((nk(c.get("cb")), ser)) or {}
        dd = day(entry.get("issued"))
        for r in c["rows"]:
            if r["no"] not in PARAMS:
                continue
            doc = str(r.get("doc") or "").strip()
            if doc == code:
                kept += 1; continue                        # already the retest iCoA
            if doc and not doc.startswith("iCoA"):
                kept += 1; continue                        # an external certificate the master assigns
            said = v.get(r["no"], "")
            if said.lower() in BLANK:
                held.append((c.get("regcode"), r["no"], code, "master has no verdict for this lot/series")); continue
            if _EXT.match(said):
                held.append((c.get("regcode"), r["no"], code, "master names an external certificate: " + said)); continue
            if dd is None:
                held.append((c.get("regcode"), r["no"], code, "retest iCoA has no issue date")); continue
            if dd > iss:
                held.append((c.get("regcode"), r["no"], code, "iCoA issued %s, after the certificate" % dd)); continue
            val = RV.bilingual(RV.canon(said, r["no"]), r["no"])
            if str(val).strip() in ("", "—"):
                held.append((c.get("regcode"), r["no"], code, "verdict off the controlled vocabulary: " + said)); continue
            before = (r.get("doc"), r.get("dd"))
            if not dry:
                r["res"], r["doc"], r["dd"], r["lab"], r["st"] = val, code, dd.strftime("%d.%m.%Y"), INHOUSE, "covered"
            changed.append((c.get("regcode"), c.get("pp") or c.get("cb"), r["no"], before[0], "->", code, dd.strftime("%d.%m.%Y")))
    return changed, held, kept


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])
    data = json.load(io.open(SRC, encoding="utf-8"))
    changed, held, kept = apply(data, dry=a.dry_run)
    certs = {x[0] for x in changed}
    print("re-pointed %d cells on %d reissues to their retest iCoA; %d cells already right; %d held"
          % (len(changed), len(certs), kept, len(held)))
    for x in changed[:6]: print("   ", x)
    for x in held[:8]: print("  HELD", x)
    if not a.dry_run:
        with io.open(SRC, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", os.path.relpath(SRC))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
