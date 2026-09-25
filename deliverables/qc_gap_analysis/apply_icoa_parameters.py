#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#1, #2 and #7 cite the internal certificate of analysis the master already assigns them.

    python3 deliverables/qc_gap_analysis/apply_icoa_parameters.py [--dry-run]

Identification A, identification B and foreign matter are determined in house. The desk
issues an internal certificate of analysis for exactly that, and the master workbook's
**iCoA Register** sheet has carried the assignment all along — one row per internal
certificate, with the code, the issue date, the basis date, the batch it belongs to and
its own verdict in the columns `#1 Ident. A`, `#2 Ident. B` and `#7 Foreign matter`.

122 certificates already print those three from their iCoA. The rest printed a red [ — ]
under "to be performed — see route" — not because the desk had no result, but because
nothing had ever carried the sheet's assignment across into the certificate rows.

This does that, and nothing else. The verdict is the sheet's, never this script's: a row
whose `#1 Ident. A` says `Conforms` prints Conforms and cites the iCoA; a row that names
an external certificate instead (`CNP ППК26111`) cites that certificate and the laboratory
that issued it, which is the treatment OI-27 already describes. A row the sheet leaves
blank stays blank.

The date rule of v35 still holds: a certificate may cite a document issued on or before
its own day and no other.
"""
import argparse, datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import result_vocabulary as RV
SRC = os.path.join(HERE, "coq_artifact_data.json")
def newest_master(folder=None):
    """The highest-numbered CoQ Analysis Master on disk.

    Pinning a version here goes stale the moment the workbook is rebuilt, and a script
    reading v40 while the desk ships v41 reads a record that no longer exists.
    """
    import glob, re as _re
    folder = folder or os.path.join(HERE, "tracker")
    found = []
    for path in glob.glob(os.path.join(folder, "CoQ_Analysis_Master_v*.xlsx")):
        m = _re.search(r"_v(\d+)\.xlsx$", path)
        if m:
            found.append((int(m.group(1)), path))
    return max(found)[1] if found else os.path.join(folder, "CoQ_Analysis_Master_v40.xlsx")


BOOK = newest_master()
SHEET = "iCoA Register"
PARAMS = ("1", "2", "7")
COLS = {"1": "#1 Ident. A", "2": "#2 Ident. B", "7": "#7 Foreign matter"}
INHOUSE = "Purely Plant GmbH (in-house)"
BLANK = ("", "—", "-", "n/a", "none")
_EXT = re.compile(r"^(?:CNP|IPH|IJZ|FHM|Farmahem)\s+(\S+)", re.I)


def day(v):
    """A desk date as a date, or None.

    >>> day("03.06.2026").isoformat()
    '2026-06-03'
    >>> day("") is None
    True
    """
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def icoa_index(path=None):
    """iCoA code -> {'1','2','7'} exactly as the master's iCoA Register sheet states them."""
    import openpyxl
    wb = openpyxl.load_workbook(path or BOOK, read_only=True, data_only=True)
    rows = list(wb[SHEET].iter_rows(values_only=True))
    wb.close()
    hd = [str(x or "").strip() for x in rows[0]]
    ic = hd.index("iCoA code")
    col = {n: hd.index(COLS[n]) for n in PARAMS}
    out = {}
    for r in rows[1:]:
        code = str(r[ic] or "").strip()
        if code:
            out[code] = {n: str(r[col[n]] or "").strip() for n in PARAMS}
    return out


def external(reg, lot, code):
    """(date, laboratory) for a certificate the register holds, preferring this lot's block.

    The iCoA Register sometimes assigns one CNP certificate to more than one packaged lot
    of the same cultivation batch — ППК26111 covers P060362, P060412 and P060422, three
    JD012603 sub-lots — while the release register files the document under a single
    block. The lot's own block is asked first; where it has nothing, the document is taken
    from wherever the register does hold it, because a certificate has one issue date and
    one laboratory wherever it is filed. Which lots it covers is the master's assignment,
    and that is what this script is here to carry across.
    """
    fallback = (None, None)
    for b in reg:
        for c in (b.get("certs") or []):
            if str(c.get("code") or "").strip() != code:
                continue
            if lot and lot in {str(b.get("pn") or "").strip(), str(b.get("cb") or "").strip()}:
                return c.get("date"), c.get("lab")
            if fallback == (None, None):
                fallback = (c.get("date"), c.get("lab"))
    return fallback


def apply(data, index):
    """Fill every empty #1/#2/#7 the iCoA Register assigns. Returns the rows changed."""
    changed, held = [], []
    for c in data["coqs"]:
        iss = day(c.get("issue"))
        code = str(c.get("icoa_code") or "").strip()
        entry = index.get(code)
        if iss is None or not entry:
            continue
        lot = str(c.get("pp") or c.get("cb") or "").strip()
        for r in c["rows"]:
            if r["no"] not in PARAMS or str(r.get("res") or "—").strip() not in ("", "—"):
                continue
            said = entry[r["no"]]
            if said.lower() in BLANK:
                continue
            m = _EXT.match(said)
            if m:
                doc = m.group(1)
                dd, lab = external(data["reg"], lot, doc)
                verdict = "Conforms"
            else:
                doc, dd, lab, verdict = code, c.get("icoa_issue"), INHOUSE, said
            d = day(dd)
            if d is None or not lab:
                held.append((c.get("regcode") or c.get("n"), r["no"], said, "no date on file"))
                continue
            if d > iss:                       # v35 — never a document issued after the page
                held.append((c.get("regcode") or c.get("n"), r["no"], doc, "issued after the certificate"))
                continue
            val = RV.bilingual(RV.canon(verdict, r["no"]), r["no"])
            if str(val).strip() in ("", "—"):
                held.append((c.get("regcode") or c.get("n"), r["no"], said, "off the controlled vocabulary"))
                continue
            r["res"], r["doc"], r["dd"], r["lab"] = val, doc, d.strftime("%d.%m.%Y"), lab
            changed.append((c.get("regcode") or c.get("n"), lot, r["no"], doc, r["dd"]))
    return changed, held


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--book", default=BOOK)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    changed, held = apply(data, icoa_index(a.book))
    print("#1/#2/#7 rows that now cite their internal certificate: %d" % len(changed))
    for row in changed[:8]:
        print("   %-16s %-11s #%-2s %-16s of %s" % row)
    if len(changed) > 8:
        print("   … and %d more" % (len(changed) - 8))
    for row in held:
        print("   HELD %-16s #%-2s %-18s %s" % row)
    if not a.dry_run and changed:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
