#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-check the RAG-derived dataset against the owner's own control sheets.

Three sheets the owner keeps outside the knowledgebase are treated here as the
source of truth for batch identity and released potency:

  sources_of_truth/tranches_overview.tsv  — Tranches Overview.xlsx  (strain, batch,
      THC bracket, released THC %, volume; 78 batches over 3 delivery tranches)
  sources_of_truth/quantities_table.tsv   — Quantities table.xlsx   (batch -> packaging
      lot / P-number, rounded THC, quantity, warehouse; 78 rows)
  sources_of_truth/list_of_coas.tsv       — List of COAs.xlsx       (two sheets: batch ->
      P-number, THC %, whether a CoA is on file, microbiology category)

Nothing here rewrites the knowledgebase. It prints every disagreement so each one can
be run back to the certificate before anything is changed — a sheet is a control record,
not a certificate, and where the two differ the certificate still governs the CoA table.
"""
import csv
import os
import re
import sys
from collections import OrderedDict, defaultdict

import coa_pivot as cp

HERE = os.path.dirname(os.path.abspath(__file__))
SOT = os.path.join(HERE, "sources_of_truth")

PCT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
# A sub-lot is written "/01" on the sheets and "-1" in the knowledgebase; both mean
# the same physical sub-lot, so both fold to "/1" before anything is compared.
TAIL = re.compile(r"[-/]0*(\d+)([A-Z]?)$")
PNUM = re.compile(r"^P\d{6}$")


def norm_batch(raw):
    """Canonical batch key. Folds only spellings the sheets use interchangeably."""
    b = (raw or "").strip().upper()
    b = re.sub(r"\s*-?\s*R\s*&\s*D\s*$", "", b)      # "CJ1024 - R&D" -> "CJ1024"
    b = b.rstrip("*").strip()                          # "JD012601*"    -> "JD012601"
    b = b.replace(" ", "")
    if PNUM.match(b):
        return b                                       # a packaging lot is its own key
    b = TAIL.sub(lambda m: "/%s%s" % (m.group(1), m.group(2)), b)  # "/01", "-1" -> "/1"
    # the sheets transpose Orange Punch Mimosa's prefix on one batch
    if b.startswith("OMP"):
        b = "OPM" + b[3:]
    return b


def norm_strain(raw):
    s = (raw or "").strip().lower()
    s = s.replace("&", " and ").replace("+", " and ")
    s = re.sub(r"[^a-z0-9]+", "", s)
    # spellings the sheets and the certificates use for the same cultivar
    for a, b in (("orangepiemimosa", "orangepunchmimosa"),
                 ("omp", "opm"),
                 ("applesandbannas", "applesandbananas"),
                 ("appelsandbananas", "applesandbananas"),
                 ("appelsandbannas", "applesandbananas"),
                 ("permanentmarket", "permanentmarker"),
                 # Capulator x Seed Junky Genetics. The sheets say "Cap Junkie" and the
                 # older certificates said "Cup Junky"; both are misspellings of the one
                 # cultivar, so they fold together rather than reporting nine batches as
                 # nine disagreements while the sheets await correction.
                 ("capjunkie", "capjunky"),
                 ("cupjunky", "capjunky"),
                 ("cupjunkie", "capjunky"),
                 ("gg4", "gorillaglue4"),
                 ("puremichigen", "puremichigan"),
                 ("cashcow", "cashcow")):
        if s == a:
            s = b
    return s


def num(raw):
    if raw in (None, ""):
        return None
    m = PCT.search(str(raw)) or re.search(r"(\d+(?:[.,]\d+)?)", str(raw))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def read_tsv(name):
    with open(os.path.join(SOT, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def thc_values(recs):
    """Every Total Δ9-THC reading on file for a batch, with its certificate."""
    out = []
    for rec in recs:
        if cp.classify(rec["Parameter"]) != "thc":
            continue
        if cp.STABILITY_RE.search(rec["Parameter"] or ""):
            continue
        head = rec["Result"].split("(")[0]
        if "<" in head or "≤" in head or "loq" in head.lower() or "blq" in head.lower():
            continue
        v = num(head)
        if v is not None:
            out.append((v, rec["Certificate Code"].strip(), cp.issue_date(rec["Issue Date"])))
    return out


def main():
    rows, batches = cp.build()
    by_seq = cp.group_by_seq(rows)

    tr = {norm_batch(r["batch"]): r for r in read_tsv("tranches_overview.tsv")}
    qt = {norm_batch(r["batch_label"]): r for r in read_tsv("quantities_table.tsv")}
    lc = {}
    for r in read_tsv("list_of_coas.tsv"):
        if not (r.get("batch") or "").strip():
            continue
        lc.setdefault(norm_batch(r["batch"]), {}).update(
            {k: v for k, v in r.items() if (v or "").strip()})

    # A certificate names either the cultivation batch or the packaging lot. The
    # Quantities table is the bridge between the two, so a knowledgebase entry filed
    # under a bare P-number resolves back to the batch it actually belongs to.
    lot_to_batch = {}
    for k, r in qt.items():
        p = (r.get("p_number") or "").strip().upper()
        if PNUM.match(p):
            lot_to_batch[p] = k

    findings = defaultdict(list)
    rag = OrderedDict()
    for b in batches:
        key = norm_batch(b["batch"])
        alias = lot_to_batch.get(key)
        entry = {
            "seq": b["seq"], "raw": b["batch"], "p": (b["p_number"] or "").strip(),
            "strain": b["strain"], "thc": thc_values(by_seq[b["seq"]]),
        }
        if alias:
            findings["0. Batch filed under its packaging lot instead of its batch number"].append(
                "seq %-3s %-10s is %s (%s)%s"
                % (b["seq"], key, alias, (tr.get(alias) or lc.get(alias) or {}).get("strain", "?"),
                   "  — DUPLICATE, that batch is already seq %s"
                   % rag[alias]["seq"] if alias in rag else ""))
            if alias in rag:
                rag[alias]["dup_seq"] = b["seq"]
                continue
            key = alias
        rag[key] = entry

    # --- 1. roster ---------------------------------------------------------
    # Where a certificate spells the batch differently from the sheets — UKIM ППК25176
    # names "BSS1024_01", the sheets split it into "BSS1024_01/1" and "/2" — the packaging
    # lot is the identity both sides agree on, so match on it before calling anything missing.
    rag_by_lot = {(r["p"] or "").strip().upper(): k for k, r in rag.items() if (r["p"] or "").strip()}
    sheet_keys = set(tr) | set(qt) | set(lc)

    def matched(k):
        if k in rag:
            return True
        for d, col in ((qt, "p_number"), (lc, "p_number")):
            lot = ((d.get(k) or {}).get(col) or "").strip().upper()
            if PNUM.match(lot) and lot in rag_by_lot:
                findings["A0. Sheet and certificate spell one batch differently (same packaging lot)"].append(
                    "sheet %-14s = RAG %-14s  via %s" % (k, rag_by_lot[lot], lot))
                return True
        return False

    for k in sorted(sheet_keys - set(rag)):
        if matched(k):
            continue
        src = ", ".join(n for n, d in (("Tranches", tr), ("Quantities", qt),
                                       ("List of COAs", lc)) if k in d)
        findings["A. In the control sheets, absent from the RAG batch list"].append(
            "%-14s  (%s)" % (k, src))
    for k in sorted(set(rag) - sheet_keys):
        findings["B. In the RAG batch list, absent from every control sheet"].append(
            "%-14s  seq %s  %s" % (k, rag[k]["seq"], rag[k]["strain"]))

    # --- 2. P-number -------------------------------------------------------
    for k, r in sorted(rag.items()):
        want = None
        for d, col in ((qt, "p_number"), (lc, "p_number")):
            if k in d and (d[k].get(col) or "").strip() not in ("", "0"):
                want = d[k][col].strip()
                break
        if want is None:
            continue
        got = r["p"]
        if norm_batch(want) == k and got in ("", "/", "—"):
            continue                      # R&D batches carry no separate packaging lot
        if got.upper() != want.upper():
            findings["C. P-number (packaging lot) disagrees"].append(
                "%-14s  sheet %-10s  RAG %-10s" % (k, want, got or "(blank)"))

    # --- 3. strain ---------------------------------------------------------
    for k, r in sorted(rag.items()):
        want = None
        for d, col in ((tr, "strain"), (lc, "strain"), ):
            if k in d and (d[k].get(col) or "").strip():
                want = d[k][col].strip()
                break
        if want is None:
            continue
        if norm_strain(want) != norm_strain(r["strain"]):
            findings["D. Strain name disagrees"].append(
                "%-14s  sheet %-24s  RAG %s" % (k, want, r["strain"]))

    # --- 4. released THC % -------------------------------------------------
    for k, r in sorted(rag.items()):
        want = None
        if k in tr:
            want = num(tr[k].get("thc_pct"))
        if want is None and k in lc:
            want = num(lc[k].get("thc_pct"))
        if want is None:
            continue
        vals = [v for v, _c, _d in r["thc"]]
        if not vals:
            findings["E. Sheet states a THC %, no THC result in the knowledgebase"].append(
                "%-14s  sheet %.2f %%" % (k, want))
            continue
        if any(abs(v - want) <= 0.005 for v in vals):
            continue
        near = min(vals, key=lambda v: abs(v - want))
        cert = [c for v, c, _d in r["thc"] if v == near]
        findings["F. Released THC % disagrees"].append(
            "%-14s  sheet %6.2f   RAG %s   (nearest %.2f on %s)"
            % (k, want, "/".join("%.2f" % v for v in sorted(set(vals))), near,
               cert[0] if cert else "?"))

    # --- 5. THC bracket consistency ---------------------------------------
    for k, r in sorted(rag.items()):
        if k not in tr:
            continue
        br = (tr[k].get("thc_bracket") or "").strip()
        want = num(tr[k].get("thc_pct"))
        if want is None or not br:
            continue
        if br.startswith(">="):
            lo, hi = num(br), 100.0
        else:
            m = re.match(r"(\d+)\D+(\d+)", br)
            if not m:
                continue
            lo, hi = float(m.group(1)), float(m.group(2))
        if not (lo <= want < hi + 1e-9):
            findings["G. Sheet's own THC % falls outside its stated bracket"].append(
                "%-14s  %.2f %% vs bracket %s" % (k, want, br))

    # --- 6. CoA-on-file flag vs certificates held -------------------------
    for k, d in sorted(lc.items()):
        if (d.get("coa_on_file") or "").strip().upper() != "YES":
            continue
        if k not in rag:
            continue
        certs = {rec["Certificate Code"].strip() for rec in by_seq[rag[k]["seq"]]
                 if rec["Certificate Code"].strip()}
        if not certs:
            findings["H. Sheet marks a CoA on file, knowledgebase holds no numbered certificate"].append(
                "%-14s  seq %s" % (k, rag[k]["seq"]))

    total = sum(len(v) for v in findings.values())
    print("RAG batches: %d    control-sheet batches: %d    union: %d"
          % (len(rag), len(sheet_keys), len(set(rag) | sheet_keys)))
    print("discrepancies: %d\n" % total)
    for head in sorted(findings):
        print(head + "  (%d)" % len(findings[head]))
        for line in findings[head]:
            print("   " + line)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
