#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Take the Head of QC's certificate database into the release register.

    python3 deliverables/qc_gap_analysis/apply_ijz_intake.py [--dry-run]

Twenty-three certificates of the Institute of Public Health sit in the owner's Drive
folder `1SmOicCRa8KEqoB-YlCojdap161YMQ-Di` and in no file the desk holds — not the
release register, not `master_coa_table.tsv` (which prints "[COVERAGE GAP] — No record
found in RAG" for these very lots), not the RAGFlow corpus, not the RAGFlow container.
They are the microbiology and the metals/pesticides panel of nineteen packaged lots,
thirteen of which carry a Tranche 1 or Tranche 2 certificate of quality whose #9.1–#9.5
and #11.1–#11.4 have been printing an empty cell for want of exactly these pages.

Each certificate is written into its lot's register block in the register's own shape,
so the carry of 15.09 and `apply_campaign_result.py` place the results by the rules
already in force — this script adds documents, it never writes a certificate row.

The read is `intake_ijz_2026-09-16/`. It is ONE read of the page, not the desk's usual
two, because the owner asked for the fastest route that still tells the truth: where
the page did not render a figure unambiguously the figure is NOT written, and the cell
and the reason are listed in `reads_microbiology.json` under `_held`.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "coq_artifact_data.json")
IN = os.path.join(HERE, "intake_ijz_2026-09-16")
IPH = "IPH — Institute of Public Health"

# (p_lot, cultivation batch, code, date, family, values by the register's column letters)
MICRO = "IPH microbiology"
PANEL = "IPH mycotoxins, metals, pesticides"
ROWS = [
    ("P060152", "J31102501",    "133/0230/26", "06.03.2026", MICRO, {"J": "1.6×10²", "K": "1.9×10²", "L": "< 10", "M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060232", "PM112501",     "135/0232/26", "06.03.2026", MICRO, {"L": "< 10", "M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060122", "ACC102501",    "77/0120/26",  "09.02.2026", MICRO, {"J": "1×10³", "K": "1.6×10³", "L": "< 10", "M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060182", "GRC102501/2",  "76/0119/26",  "09.02.2026", MICRO, {"K": "1×10²", "L": "< 10", "M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060112", "PUM102501",    "74/0117/26",  "09.02.2026", MICRO, {"L": "< 10", "M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060132", "CF102501",     "73/0116/26",  "09.02.2026", MICRO, {"M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060172", "KC102501",     "129/0226/26", "06.03.2026", MICRO, {"J": "3.8×10³", "K": "6.8×10³", "M": "Одговара (absent)", "N": "Одговара (absent)"}),
    ("P060402", "GG012603",     "404/0787/26", "24.06.2026", MICRO, {"J": "5×10³", "K": "4.1×10³", "L": "< 10", "M": "Отсутна", "N": "Отсутна"}),
    ("P060412", "JD012603/02",  "405/0788/26", "24.06.2026", MICRO, {"J": "6.3×10³", "K": "4.4×10³", "L": "< 10", "M": "Отсутна", "N": "Отсутна"}),
    ("P060422", "JD012603/02V", "406/0789/26", "24.06.2026", MICRO, {"J": "5.1×10³", "K": "4.7×10³", "L": "< 10", "M": "Отсутна", "N": "Отсутна"}),
    ("P060362", "JD012603/01",  "365/0695/26", "01.06.2026", MICRO, {"J": "2×10²", "K": "1×10²", "L": "< 10", "M": "Отсутна", "N": "Отсутна"}),
    ("P060372", "CC012603",     "363/0693/26", "01.06.2026", MICRO, {"J": "2.7×10³", "K": "1.6×10¹", "L": "< 10", "M": "Отсутна", "N": "Отсутна"}),
    ("P060382", "SCR012603",    "364/0694/26", "01.06.2026", MICRO, {"J": "5.4×10⁴", "K": "1.8×10⁴", "L": "< 10", "M": "Отсутна", "N": "Отсутна"}),
    ("P060152", "J31102501",    "1056/2026",   "09.03.2026", PANEL, {"O": "<2",  "R": "0.061", "S": "N.D.", "T": "N.D.",    "U": "N.D.",   "V": "N.D."}),
    ("P060232", "PM112501",     "1059/2026",   "09.03.2026", PANEL, {"O": "2.2", "R": "N.D.",  "S": "N.D.", "T": "N.D.",    "U": "N.D.",   "V": "N.D."}),
    ("P060172", "KC102501",     "1058/2026",   "09.03.2026", PANEL, {"O": "2.8", "R": "N.D.",  "S": "N.D.", "T": "N.D.",    "U": "N.D.",   "V": "N.D."}),
    ("P060182", "GRC102501/2",  "1060/2026",   "09.03.2026", PANEL, {"O": "<2",  "R": "N.D.",  "S": "N.D.", "T": "0.0013",  "U": "N.D.",   "V": "N.D."}),
    ("P060112", "PUM102501",    "327/2026",    "11.02.2026", PANEL, {"O": "<2",  "R": "0.078", "S": "N.D.", "T": "0.0187",  "U": "N.D.",   "V": "N.D."}),
    ("P060122", "ACC102501",    "326/2026",    "11.02.2026", PANEL, {"O": "2.3", "R": "0.078", "S": "N.D.", "T": "0.022",   "U": "N.D.",   "V": "N.D."}),
    ("P060132", "CF102501",     "330/2026",    "11.02.2026", PANEL, {"O": "2.1", "R": "0.07",  "S": "N.D.", "T": "0.0942",  "U": "N.D.",   "V": "N.D."}),
    ("P060402", "GG012603",     "3659/2026",   "22.06.2026", PANEL, {"O": "<2",  "R": "0.059", "S": "0.03", "T": "0.05",    "U": "0.015",  "V": "< 0.01"}),
    ("P060412", "JD012603/02",  "3660/2026",   "22.06.2026", PANEL, {"O": "<2",  "R": "0.085", "S": "0.044", "T": "0.042",  "U": "0.042",  "V": "< 0.01"}),
    ("P060422", "JD012603/02V", "3662/2026",   "22.06.2026", PANEL, {"O": "<2",  "R": "0.06",  "S": "0.03", "T": "0.045",   "U": "0.013",  "V": "< 0.01"}),
]


def key(s):
    return str(s or "").strip().upper().replace("_", "").replace("-", "").replace("/", "")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    by = {}
    for b in data["reg"]:
        for k in {key(b.get("pn")), key(b.get("cb"))} - {""}:
            by.setdefault(k, b)
    added, skipped, missing, merged = 0, 0, [], []
    for pn, cb, code, date, fam, vals in ROWS:
        block = by.get(key(pn)) or by.get(key(cb))
        if block is None:
            missing.append((pn, cb, code))
            continue
        have = [c for c in block["certs"] if str(c.get("code") or "").strip() == code]
        if have:
            # idempotent, and additive: a value the register already carries is never
            # rewritten, a value it lacks is added. That is what lets a figure held for a
            # second read be taken in later without touching the twenty-two around it.
            gained = {k: v for k, v in vals.items() if k not in (have[0].get("vals") or {})}
            if gained:
                have[0].setdefault("vals", {}).update(gained)
                merged.append((code, ",".join(sorted(gained))))
            else:
                skipped += 1
            continue
        block["certs"].append({"code": code, "date": date, "lab": IPH, "fam": fam,
                               "stab": False, "vals": vals, "flags": {}})
        added += 1
    print("certificates written into the register: %d   already there: %d" % (added, skipped))
    for code, cols in merged:
        print("   %s gained column(s) %s" % (code, cols))
    for pn, cb, code in missing:
        print("   NO BLOCK for %s / %s — %s not written" % (pn, cb, code))
    if not a.dry_run and (added or merged):
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
