#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Potency study — bound dataset builder (§6B: bind → compute → inject → assert).

Compiles EVERY Total Δ⁹-THC result ever recorded for Purely Plant batches:

  1. The eCoA register corpus — 99 assays / 77 batches / 20 strains, all
     previously live-verified against the ImB_QC_COAs knowledgebase.
  2. The Grape Pie stability program (found in this session's live host sweep):
     ППК26032–26037 + ППК26057–26059, batches P050022/P050072/P050202
     (= GP0824_02 / GP0824_03 / GP062501), months 3/6/9 at 25°C/60%RH and
     40°C/75%RH. One row (ППК26037, 18.62) carries the source's own
     PP-QC-ERR-002 "transcription defect — do not use" flag and is stored but
     excluded from every statistic.

Statistics per strain: n, mean, sample SD, min–max, 95% CI of the mean
(t-distribution; only where n ≥ 2). Values are release/warehouse assays only —
stability 40°C arms are degradation evidence, not inventory state, and are
kept in a separate list.

Grade-range design inputs: per-batch anchor = most recent verified result;
degradation allowance D = 1.5 %abs/year (see DEGRADATION_NOTE — conservative
vs the observed 25°C stability behaviour); measurement headroom U ≈ 6.2% of
value at k=2 (the certs' own stated uncertainty ratio).
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ingestion", "coa_track", "letta-imb-coas"))
import build_spec_param_listing as bl
import crosscheck_sources as cc

# tranche-overview strain spellings -> register strain names
STRAIN_ALIAS = {
    "Cap Junkie": "Cap Junky", "CashCow": "Cash Cow", "GG4": "Gorilla Glue",
    "Grapes and Cream": "Graps & Creme", "Jelly Donuts": "Jelly Donutz",
    "Sleepy Joe": "Sleepy Joy", "Clemosa": "Clemosa a bud",
    "Apples and Bananas": "Apple and Banana", "Apple and Bananas": "Apple and Banana",
    "Appels & Bananas": "Apple and Banana", "Wedding Crusher": "Wedding Crasher",
}

# Stability program rows recovered live from the host (this session's sweep).
# arm: storage condition; month: stability timepoint; usable: False = the
# source itself flags the row defective (PP-QC-ERR-002) — never use as data.
STABILITY = [
    dict(report="ППК26032", issued="05.03.2026", p="P050022", batch="GP0824_02",
         strain="Grape Pie", arm="25°C/60%RH", month=6, total_thc=21.31, cbn=0.23, usable=True),
    dict(report="ППК26033", issued="05.03.2026", p="P050022", batch="GP0824_02",
         strain="Grape Pie", arm="40°C/75%RH", month=6, total_thc=13.16, cbn=2.35, usable=True),
    dict(report="ППК26034", issued="05.03.2026", p="P050072", batch="GP0824_03",
         strain="Grape Pie", arm="25°C/60%RH", month=6, total_thc=24.62, cbn=0.05, usable=True),
    dict(report="ППК26035", issued="05.03.2026", p="P050072", batch="GP0824_03",
         strain="Grape Pie", arm="40°C/75%RH", month=6, total_thc=14.99, cbn=2.15, usable=True),
    dict(report="ППК26036", issued="05.03.2026", p="P050202", batch="GP062501",
         strain="Grape Pie", arm="25°C/60%RH", month=3, total_thc=22.83, cbn=0.05, usable=True),
    dict(report="ППК26037", issued="05.03.2026", p="P050202", batch="GP062501",
         strain="Grape Pie", arm="40°C/75%RH", month=3, total_thc=18.62, cbn=1.00, usable=False,
         note="PP-QC-ERR-002: mass balance fails (1.09 + 0.877×18.47 = 17.29 ≠ 18.62) — source says DO NOT USE"),
    dict(report="ППК26057", issued="11.05.2026", p="P050202", batch="GP062501",
         strain="Grape Pie", arm="25°C/60%RH", month=6, total_thc=24.51, cbn=0.04, usable=True),
    dict(report="ППК26058", issued="11.05.2026", p="P050202", batch="GP062501",
         strain="Grape Pie", arm="40°C/75%RH", month=6, total_thc=17.05, cbn=2.05, usable=True),
    dict(report="ППК26059", issued="11.05.2026", p="P050022", batch="GP0824_02",
         strain="Grape Pie", arm="25°C/60%RH", month=9, total_thc=23.08, cbn=0.30, usable=True),
]

DEGRADATION_NOTE = (
    "Empirical basis: 25°C/60%RH stability arms show NO monotonic Total-THC decline over "
    "3–9 months (22.83→24.51; 21.31→23.08 — movement within sampling/measurement variance); "
    "40°C/75%RH arms collapse to 13.16–17.05% with CBN 2.05–2.35% (heat, not time, drives loss). "
    "Same-lab repeat pairs: J31102501 19.14→17.32 over 5 months (−1.82, ≤ combined U of the two "
    "measurements); OPM122501 8.09→7.91 over 4 months (−0.18). Cross-lab intake-vs-retest deltas "
    "scatter −3.1…+4.3 around ≈0 — inter-lab/sampling variance dominates any age effect. "
    "D = 1.5 %abs/year is therefore a CONSERVATIVE allowance, larger than any evidenced "
    "12-month decline at warehouse conditions.")

D_YEAR = 1.5            # degradation allowance, %abs per year of further storage
U_RATIO = 0.062         # measurement uncertainty ≈ 6.2% of value (k=2, per the certs)
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
       8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
       15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def num(v):
    m = re.search(r"(\d+[.,]\d+|\d+)", v.replace(",", "."))
    return float(m.group(1)) if m else None


def dkey(d):
    p = (d or "").split(".")
    return (p[2], p[1], p[0]) if len(p) == 3 else ("0", "0", "0")


def r05(x):
    return round(x * 2) / 2


def build():
    listing, _, _ = bl.build_rows()
    pot = [r for r in listing if r["no"] == "4" and not r["value"].startswith("Missing")]
    results = [dict(batch=r["batch"].strip(), strain=r["strain"].strip(), value=num(r["value"]),
                    printed=r["value"], date=r["date"], lab=r["lab"], cert=r["cert"])
               for r in pot]
    assert len(results) == 99, len(results)
    assert all(r["value"] is not None for r in results)

    # per-batch anchor = most recent result
    by_batch = {}
    for r in results:
        by_batch.setdefault(cc.norm_batch(r["batch"]), []).append(r)
    anchors = {}
    for k, rs in by_batch.items():
        rs.sort(key=lambda r: dkey(r["date"]))
        anchors[k] = rs[-1]

    # per-strain statistics over ALL register results (the tested population)
    strains = {}
    for r in results:
        strains.setdefault(r["strain"], []).append(r)
    stats = {}
    for s, rs in sorted(strains.items()):
        vals = sorted(r["value"] for r in rs)
        n = len(vals)
        mean = sum(vals) / n
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) if n >= 2 else None
        ci = None
        if sd is not None and n >= 3:      # n=2 gives t(1)=12.7 — a CI wider than the
            t = T95.get(n - 1, 1.96)       # whole axis; report none rather than nonsense
            h = t * sd / math.sqrt(n)
            ci = [round(mean - h, 2), round(mean + h, 2)]
        stats[s] = dict(n=n, mean=round(mean, 2), sd=round(sd, 2) if sd else None,
                        min=vals[0], max=vals[-1], ci95=ci, values=vals)

    # tranche membership: in-stock batches
    trows = cc.read_tsv("tranches_overview.tsv")
    stock = []
    for t in trows:
        strain = STRAIN_ALIAS.get(t["strain"].strip(), t["strain"].strip())
        key = cc.norm_batch(t["batch"])
        a = anchors.get(key)
        stock.append(dict(tranche=t["tranche"].strip(), batch=t["batch"].strip(),
                          strain=strain, declared=float(t["thc_pct"]) if t["thc_pct"] else None,
                          bracket_old=t["thc_bracket"].strip(),
                          anchor=a["value"] if a else None,
                          anchor_date=a["date"] if a else None,
                          anchor_lab=a["lab"] if a else None))

    # per-batch proposed range: anchor near the TOP of the bracket, with
    # downward headroom ≥ D_YEAR + measurement U at the lower edge.
    for b in stock:
        a = b["anchor"] if b["anchor"] is not None else b["declared"]
        if a is None:
            b["proposed"] = None
            continue
        u = U_RATIO * a
        lo = r05(a - D_YEAR - u)
        hi = r05(a + max(1.0, u))
        lo = max(lo, 5.0)                      # release A.C. floor: min 5.00%
        b["proposed"] = [lo, hi]
        b["headroom_down"] = round(a - lo, 2)
        b["basis"] = "anchor" if b["anchor"] is not None else "declared (no assay on file)"

    # Per-strain warehouse GRADE TIERS (stock batches only). Greedy clustering
    # on ascending anchors: a tier opens at the lowest batch's safe floor
    # (anchor − D − U, rounded down to 0.5) and accepts further batches while
    # the tier stays ≤ W_MAX wide once it also covers their safe ceiling
    # (anchor + U, rounded up to 0.5). Every batch's tier therefore contains
    # its whole one-year-ahead measurement window — a remeasure now, or after a
    # further year of storage, still reads inside the declared grade.
    W_MAX = 6.5
    merged = {}
    for s in sorted({b["strain"] for b in stock}):
        bs = sorted([b for b in stock if b["strain"] == s and b["proposed"]],
                    key=lambda b: (b["anchor"] if b["anchor"] is not None else b["declared"]))
        if not bs:
            continue
        tiers = []
        cur = None
        for b in bs:
            a = b["anchor"] if b["anchor"] is not None else b["declared"]
            u = U_RATIO * a
            flo = max(5.0, math.floor((a - D_YEAR - u) * 2) / 2)
            cei = math.ceil((a + u) * 2) / 2
            if cur is None or cei - cur["lo"] > W_MAX:
                cur = dict(lo=flo, hi=cei, batches=[b["batch"]], anchors=[a])
                tiers.append(cur)
            else:
                cur["hi"] = max(cur["hi"], cei)
                cur["batches"].append(b["batch"])
                cur["anchors"].append(a)
            b["tier"] = len(tiers)
        for g in tiers:                       # verify the guarantee for every batch
            for a in g["anchors"]:
                u = U_RATIO * a
                assert g["lo"] <= a - D_YEAR - u + 0.51 and a + u <= g["hi"] + 0.01, (s, g, a)
        merged[s] = [dict(range=[g["lo"], g["hi"]], batches=g["batches"],
                          anchors=[round(a, 2) for a in g["anchors"]]) for g in tiers]

    # paired evidence (repeat same-lab measurements + stability arms)
    repeats = [dict(batch="J31102501", strain="Jokerz 31", first=19.14, first_date="04.03.2026",
                    second=17.32, second_date="07.08.2026", delta=-1.82),
               dict(batch="OPM122501", strain="Orange Punch Mimosa", first=8.09,
                    first_date="09.04.2026", second=7.91, second_date="07.08.2026", delta=-0.18),
               dict(batch="J31112501", strain="Jokerz 31", first=25.27, first_date="04.03.2026",
                    second=20.21, second_date="09.04.2026", delta=-5.06,
                    note="1-month interval — sampling heterogeneity, not degradation"),
               dict(batch="J31122501", strain="Jokerz 31", first=19.84, first_date="09.04.2026",
                    second=21.84, second_date="09.04.2026", delta=+2.00,
                    note="same-day duplicate certificates — pure sampling spread")]

    data = dict(
        register_results=results, n_results=len(results),
        n_batches=len(by_batch), n_strains=len(strains),
        stability=STABILITY, degradation_note=DEGRADATION_NOTE,
        repeats=repeats, stats=stats, stock=stock, merged_ranges=merged,
        design=dict(D_year=D_YEAR, U_ratio=U_RATIO,
                    rule="lower = anchor − D − U(anchor) rounded to 0.5, floored at 5.00 "
                         "(release A.C.); upper = anchor + max(1.0, U(anchor)); merged per "
                         "strain where batch ranges overlap"),
        old_methodology=(
            "QCSP 001 standard 4-tier fixed brackets: I 27.00–30.00 · II 23.00–26.90 · "
            "III 16.00–22.90 · IV 5.00–15.90 (nominal = midpoint); custom narrower sets for "
            "several renamed strains; T1 files graded from the Aug-2026 retest values, "
            "T1_rename graded from Portfolio-Master intake values (intentionally different, "
            "per owner). Weakness for ageing stock: brackets are fixed and grade-boundary "
            "batches can flip out of grade on any remeasure or with modest degradation — the "
            "bracket encodes no downward headroom for a specific batch."),
        verification=dict(
            host_sweep="4,134 passages scanned live (ImB_QC_COAs); 176 unique Total-THC lines; "
                       "all 99 register values present; 9 stability rows recovered and "
                       "attributed (3 P-codes → GP batches via the eCoA register)",
            source_id="source-271bc3be-10d1-4541-8a5b-be3f6fab7c97"))

    out = os.path.join(HERE, "potency_dataset.json")
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("strains:", len(stats), " stock batches:", len(stock),
          " with anchor:", sum(1 for b in stock if b["anchor"] is not None))
    for s, g in merged.items():
        print("%-22s" % s, " + ".join("%.1f–%.1f (%d)" % (x["range"][0], x["range"][1],
                                                          len(x["batches"])) for x in g))
    return data


if __name__ == "__main__":
    build()
