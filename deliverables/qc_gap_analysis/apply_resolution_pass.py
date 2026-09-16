#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Head of QC's own reading pass of 09.09.2026, taken into the release register.

    python3 deliverables/qc_gap_analysis/apply_resolution_pass.py [--dry-run]

`cell_resolution_2026-09-09.tsv` is the Head of QC's pass over 50 lots and twelve
determination groups: for each, the document to cite, its issue date, its laboratory, and
**what the document prints** — every value the page carries, in determination order,
separated by semicolons.

A microbiological purity report determines five parameters on one sample. It is not
possible for a batch to have a result for one of them and nothing for the other four, and
a certificate that prints two and leaves three blank is not a defensible page. That is the
Head of QC's objection of 16.09.2026 and it is correct. The desk had been reading the
scans one parameter at a time while this file — its own, since 09.09 — carried all five.

So the pass is the source, and the scan is the cross-check rather than the other way
round. Three groups are taken:

  * **#9** — five values, 9.1 … 9.5, in order. 49 of the 50 rows carry exactly five.
  * **#11** — four values, 11.1 … 11.4. The order is not assumed: the pass writes
    `752-2025` as `0,01; 0,016; 0,014; 0,005` and the register has carried that certificate
    as R 0.01, S 0.016, T 0.014, U 0.005 since long before this script, so the pass's order
    is the register's order, confirmed against data the desk already held.
  * **#12** — one determination over a whole panel: written N.D. only when every line of
    the panel is, which is how the register's own pesticide rows already read.

**#10 is not taken.** Its rows carry one, three or five values depending on what the
laboratory printed, and a mapping that is not certain is not a mapping. The M-series
covers those determinations anyway.

A row whose value list is not the length its group requires is held and named, never
guessed at. Writing is additive: a value the register already carries is never rewritten.
"""
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tracker"))
from tracker_data import nkey                                          # noqa: E402
SRC = os.path.join(HERE, "coq_artifact_data.json")
PASS = os.path.join(HERE, "cell_resolution_2026-09-09.tsv")
GROUPS = {
    "9 Microbiological purity": (["J", "K", "L", "M", "N"], "IPH microbiology"),
    "11 Heavy metals": (["R", "S", "T", "U"], "IPH mycotoxins, metals, pesticides"),
}
PEST = "12 Pesticide residues"
LAB = {
    "IJZ-MB": "IPH — Institute of Public Health",
    "IJZ": "IPH — Institute of Public Health",
    "IPH": "IPH — Institute of Public Health",
    "CNP": "UKIM Faculty of Pharmacy — Center for Natural Products",
    "FHM": "Farmahem",
    "PP": "Purely Plant GmbH (in-house)",
}
_ND = re.compile(r"^\s*(?:н\.?\s*д\.?|n\.?\s*d\.?|ND)\b", re.I)
_UNIT = re.compile(r"\s*(?:CFU/g|mg/[Kk]g(?:\(l\))?|µg/kg|%)\s*", re.I)
# "< 10³ и 10²" — the pass drops the second bound's sign where the page prints it. The
# other spellings the desk reads all carry it, so it is restored rather than a fourth
# spelling admitted.
_HALF = re.compile(r"(и)\s*(?!>)(10[⁰¹²³⁴⁵⁶⁷⁸⁹])")


def clean(v):
    """One printed value as the register spells it, or '' if the page said nothing.

    >>> clean("3,1 x 10⁴ CFU/g CFU/g")
    '3.1×10⁴'
    >>> clean("н.д. mg/kg(l)")
    'N.D.'
    >>> clean("0,016 mg/kg(l)")
    '0.016'
    >>> clean("< 10³ и 10² CFU/g")
    '< 10³ и > 10²'
    >>> clean("Одговара")
    'Одговара'
    >>> clean("—")
    ''
    """
    v = _UNIT.sub(" ", str(v or "")).strip()
    if not v or v in ("—", "-"):
        return ""
    if _ND.match(v):
        return "N.D."
    v = _HALF.sub(r"\1 > \2", v)
    v = re.sub(r"(\d),(\d)", r"\1.\2", v)          # the pass writes a decimal comma
    v = re.sub(r"\s*x\s*10", "×10", v)        # 3.1 x 10^4 -> 3.1×10^4
    return re.sub(r"\s{2,}", " ", v).strip()


def parts(s):
    return [p.strip() for p in str(s or "").split(";") if p.strip()]


def key(s):
    return str(s or "").strip().upper().replace("_", "").replace("-", "").replace("/", "")


def rows_to_certs(path=None):
    """(lot key, code, date, laboratory, {column: value}) for every row the pass can place."""
    out, held = [], []
    for r in csv.DictReader(open(path or PASS, encoding="utf-8"), delimiter="\t"):
        group = (r.get("Determination") or "").strip()
        code = (r.get("Document to cite") or "").strip()
        date = (r.get("Issued") or "").strip()
        lab = LAB.get((r.get("Laboratory") or "").strip())
        lot = [x for x in ((r.get("P lot") or "").strip(), (r.get("Batch") or "").strip())
               if x and x not in ("\u2014", "-")]
        printed = parts(r.get("What the document prints"))
        if group not in GROUPS and group != PEST:
            continue
        if not code or code in ("—", "-") or not date or date in ("—", "-") or not lab or not lot:
            continue
        if group == PEST:
            vals = {clean(p) for p in printed} - {""}
            if not vals:
                continue
            if len(vals) > 1:
                held.append(("/".join(lot), code, group, "the panel does not read the same on every line"))
                continue
            v = vals.pop()
            # A whole panel below the method's limit of quantification is one determination
            # to the certificate. The pass writes that three ways — every line not detected,
            # every line below a stated bound, and the summary the reader wrote over a page
            # that prints the bound once — and all three say the same thing.
            if v.startswith("\u2264 LOQ") or v.startswith("< LOQ"):
                v = "< LOQ"
            out.append((lot, code, date, lab, {"V": v}))
            continue
        cols, fam = GROUPS[group]
        if len(printed) != len(cols):
            held.append(("/".join(lot), code, group, "%d value(s) for %d determinations" % (len(printed), len(cols))))
            continue
        vals = {c: clean(p) for c, p in zip(cols, printed)}
        vals = {c: v for c, v in vals.items() if v}
        if len(vals) != len(cols):
            held.append(("/".join(lot), code, group, "a value the pass leaves blank"))
            continue
        out.append((lot, code, date, lab, vals))
    return out, held


def apply(data, certs):
    by = {}
    for b in data["reg"]:
        for k in {key(b.get("pn")), key(b.get("cb"))} - {""}:
            by.setdefault(k, b)
    added, gained, missing = 0, 0, []
    for lot, code, date, lab, vals in certs:
        block = next((by[key(k)] for k in lot if key(k) in by), None)
        if block is None:
            missing.append(("/".join(lot), code))
            continue
        # The pass writes an Institute code with hyphens (2156-2025, 163-0271-25) and the
        # register with slashes (2156/2025, 163/0271/25) — the same document, two
        # spellings. Matched on the raw string it is written twice, and a second
        # certificate on a lot is a second testing round: two internal certificates
        # appeared in the series that no testing had produced. The desk's own fold,
        # tracker_data.nkey, is what a document is compared by everywhere else.
        have = [c for c in block["certs"] if nkey(c.get("code")) == nkey(code)]
        if have:
            new = {k: v for k, v in vals.items() if k not in (have[0].get("vals") or {})}
            if new:
                have[0].setdefault("vals", {}).update(new)
                gained += len(new)
            continue
        fam = "IPH microbiology" if set(vals) & set("JKLMN") else "IPH mycotoxins, metals, pesticides"
        block["certs"].append({"code": code, "date": date, "lab": lab, "fam": fam,
                               "stab": False, "vals": vals, "flags": {}})
        added += 1
    return added, gained, missing


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    certs, held = rows_to_certs()
    data = json.load(open(a.src, encoding="utf-8"))
    added, gained, missing = apply(data, certs)
    print("rows the pass can place: %d   certificates written: %d   columns added to a "
          "certificate already there: %d" % (len(certs), added, gained))
    for row in held:
        print("   HELD %-11s %-14s %-26s %s" % row)
    for lot, code in missing:
        print("   NO BLOCK %-11s %s" % (lot, code))
    if not a.dry_run and (added or gained):
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
