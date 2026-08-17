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

Per strain the dataset carries only what the documents actually show: the
number of tested results, the min–max span they occupy, and the sorted values
themselves. No mean/SD/95% CI — per owner instruction those play no part in
setting a potency grade and appear in no document, so they are not computed.

Grade design: per-batch anchor = most recent verified result. A strain's
whole tier ladder is planned together (fewest tiers first, then closest fit)
so that adjacent tiers are CONTIGUOUS — no blind gap — see plan_contiguous()
/ build_strain_tiers() for the full rule (nominal on a half-percent grid —
nn.00 % or nn.50 %, never a finer fraction — tolerance up to 10% of the
nominal, shrunk only as far as needed to meet the neighbouring tier exactly,
floored at the 5.00% release acceptance criterion). Two of 24 strains
contain a genuine, disclosed gap where no candidate nominal pair can bridge
them within the 10% cap — a real discontinuity in that strain's own tested
history, not an artefact of the algorithm.
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

def num(v):
    m = re.search(r"(\d+[.,]\d+|\d+)", v.replace(",", "."))
    return float(m.group(1)) if m else None


def dkey(d):
    p = (d or "").split(".")
    return (p[2], p[1], p[0]) if len(p) == 3 else ("0", "0", "0")


MAX_TOL_RATIO = 0.10   # owner ceiling: declared ± tolerance may never exceed
                        # 10.0% of the nominal, for ANY batch or strain.
MIN_GAP = 0.01          # adjacent tiers must never overlap, and the normal
                        # (contiguous) case sits EXACTLY this far apart — the
                        # smallest possible separation at 2-decimal resolution
                        # (…nn.49% | nn.50%… style) — never more, unless the
                        # data itself leaves a genuine, disclosed gap.


NOM_STEP = 0.5   # nominals are declared in half-percent steps (20.00 %,
                  # 20.50 %, 21.00 %, ...) rather than whole numbers only —
                  # the finer grid gives the planner more candidates to fit
                  # a segment's anchors and neighbours without squeezing.

# Owner-set nominal for a strain's HIGHEST (strongest) tier, overriding the
# automatic closest-to-cluster choice. Everything below cascades down from it
# by the standard top-down rule (build_top_down). The value must still be a
# valid full-width top nominal (its ±10% band must cover that top tier's own
# anchors and clear the release floor) or the build asserts — an override
# cannot silently drop a result out of grade. Add a strain here only when the
# owner has explicitly dictated its top nominal.
TOP_NOMINAL_OVERRIDE = {
    "Grape Pie": 24.0,
    "Motor Breath": 18.0,
}


def feasible_nominals(anchors, floor=5.0, max_ratio=MAX_TOL_RATIO, step=NOM_STEP):
    """Every candidate nominal (a multiple of `step`) whose FULL ±max_ratio
    band both covers all of `anchors` and keeps its floor at or above the
    release criterion. Returned as a list of floats; the real-valued
    interval can be non-empty yet contain no valid grid point, so the
    step-aligned bounds are what matter."""
    lo_n = max(anchors) / (1 + max_ratio)
    hi_n = min(anchors) / (1 - max_ratio)
    lo_i = math.ceil(lo_n / step - 1e-9)
    hi_i = math.floor(hi_n / step + 1e-9)
    lo_i = max(lo_i, math.ceil((floor / (1 - max_ratio)) / step - 1e-9))
    return [round(k * step, 2) for k in range(lo_i, hi_i + 1)]


def build_top_down(groups, floor=5.0, max_ratio=MAX_TOL_RATIO, step=NOM_STEP, gap=MIN_GAP,
                   top_override=None, strain_max=None):
    """Build one contiguous ladder from a fixed segmentation, TOP-DOWN, the
    way the owner declares grades by hand:

      1. The HIGHEST tier gets PRIORITY — it takes its FULL ±max_ratio width
         (nothing constrains a segment's top edge from above, so the strongest
         grade is never squeezed). Its nominal is a grid point that keeps that
         full band over the tier's own anchors.
      2. Each LOWER tier then EXTENDS DOWNWARD from the tier above: its ceiling
         is pinned exactly `gap` below the tier-above's floor (no blind gap),
         and it takes AS MUCH of its own ±max_ratio as it can while reaching up
         to that ceiling. Concretely its nominal is the SMALLEST grid value N
         with 1.1·N ≥ ceiling — i.e. N = ceil((ceiling/(1+max_ratio))/step)·step
         — so tol = ceiling − N is as large as possible yet still ≤ max_ratio·N
         (equality N ≥ ceiling/(1+max_ratio) guarantees tol ≤ cap). This is the
         "predict the next lower nominal and its ±" rule: given the tier above,
         the next one down is determined, not searched.

    `groups`: anchor lists, ascending, one per tier. Returns the tier dicts
    ascending (nominal/tol/lo/hi/anchors) or None if this segmentation cannot
    be realised without a gap, an over-cap tolerance, a floor below the release
    criterion, or a tier that fails to cover its own anchors — in which case
    the caller tries a finer segmentation (more tiers) or, failing all, a real
    disclosed gap. Among the feasible full-width top nominals it keeps the one
    giving the least total |nominal − anchor| across the whole ladder, so the
    declared nominals stay honest to the results and never drift up to overstate
    the product."""
    top = groups[-1]
    tmin, tmax = min(top), max(top)
    # grid nominals whose FULL band covers the top group and clears the floor
    lo_i = math.ceil((tmax / (1 + max_ratio)) / step - 1e-9)
    hi_i = math.floor((tmin / (1 - max_ratio)) / step + 1e-9)
    lo_i = max(lo_i, math.ceil((floor / (1 - max_ratio)) / step - 1e-9))
    top_cands = [round(k * step, 2) for k in range(lo_i, hi_i + 1)]
    if not top_cands:
        return None
    # Owner override for this strain's strongest tier: only applies to the
    # group that actually holds the strain's top anchor, and only if that
    # override is itself a valid full-width top nominal here. Otherwise this
    # segmentation cannot honour it, so it is not a candidate.
    if top_override is not None and strain_max is not None \
            and abs(tmax - strain_max) < 1e-9:
        if any(abs(c - top_override) < 1e-9 for c in top_cands):
            top_cands = [round(top_override, 2)]
        else:
            return None

    best = None  # (cost, tiers ascending)
    for n_top in top_cands:
        tol = round(n_top * max_ratio, 2)
        tiers = [dict(nominal=n_top, tol=tol, lo=round(n_top - tol, 2),
                      hi=round(n_top + tol, 2), anchors=top)]
        ok = True
        ceiling = round(tiers[-1]["lo"] - gap, 2)
        for g in reversed(groups[:-1]):
            gmin, gmax = min(g), max(g)
            n_i = math.ceil((ceiling / (1 + max_ratio)) / step - 1e-9)
            n_i = max(n_i, math.ceil((floor / (1 - max_ratio)) / step - 1e-9))
            nom = round(n_i * step, 2)
            tol = round(ceiling - nom, 2)
            if tol < 0 or tol > round(nom * max_ratio, 2) + 1e-9:
                ok = False
                break
            lo, hi = round(nom - tol, 2), round(nom + tol, 2)
            if lo < floor - 1e-6 or not (lo - 1e-6 <= gmin and gmax <= hi + 1e-6):
                ok = False
                break
            tiers.append(dict(nominal=nom, tol=tol, lo=lo, hi=hi, anchors=g))
            ceiling = round(lo - gap, 2)
        if not ok:
            continue
        tiers.reverse()  # ascending
        cost = sum(abs(t["nominal"] - a) for t in tiers for a in t["anchors"])
        if best is None or cost < best[0] - 1e-9:
            best = (cost, tiers)
    return best[1] if best else None


def _tiers_for_k(anchors, k, floor, max_ratio, gap, top_override=None, strain_max=None):
    """Best top-down ladder (build_top_down) using EXACTLY k tiers over
    `anchors`, or None if none exists at this tier count. Exhaustive over the
    C(n-1, k-1) ways to cut `anchors` into k contiguous, non-empty runs —
    always small in practice (a single strain's tested-result count), so
    exhaustive is both simple and exact. "Best" = least total |nominal-anchor|."""
    n = len(anchors)
    if k > n:
        return None
    best = None  # (cost, tiers)

    def eval_cuts(bounds):
        nonlocal best
        groups = [anchors[bounds[i]:bounds[i + 1]] for i in range(k)]
        tiers = build_top_down(groups, floor, max_ratio, NOM_STEP, gap,
                               top_override=top_override, strain_max=strain_max)
        if tiers is None:
            return
        for gi, t in enumerate(tiers):
            t["start"], t["end"] = bounds[gi], bounds[gi + 1]
        cost = sum(abs(t["nominal"] - a) for t in tiers for a in t["anchors"])
        if best is None or cost < best[0] - 1e-9:
            best = (cost, tiers)

    def cuts(start, groups_left, acc):
        if groups_left == 1:
            eval_cuts([0] + acc + [n])
            return
        for c in range(start + 1, n - (groups_left - 1) + 1):
            cuts(c, groups_left - 1, acc + [c])

    cuts(0, k, [])
    return best


def plan_contiguous(anchors, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP,
                    top_override=None, strain_max=None):
    """Plan one strain's tier ladder with NO blind gap anywhere in it: the
    only separation between adjacent tiers is the minimal 2-decimal buffer
    (…nn.49% | nn.50%… style), never more. Fewest tiers wins first — a grade
    ladder should not fragment into one tier per batch just because that
    minimises distance-to-nominal — then, among ladders at that minimal tier
    count, the one with least total |nominal − anchor|.

    Returns the resolved tier list (nominal/tol/lo/hi/anchors, full ± width
    already computed by solve_chain) or None if NO tier count admits a fully
    contiguous, fully symmetric ladder at all (see build_strain_tiers for
    what happens then — a real, evidenced gap, not a bug)."""
    n = len(anchors)
    if n == 0:
        return []
    for k in range(1, n + 1):
        res = _tiers_for_k(anchors, k, floor, max_ratio, gap,
                           top_override=top_override, strain_max=strain_max)
        if res is not None:
            return res[1]
    return None


def build_strain_tiers(items, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP,
                       top_override=None):
    """items: [(anchor, payload), ...] ascending by anchor, all for one
    strain. Plans the whole ladder contiguous end to end via
    plan_contiguous(). If (rare) two neighbouring results are so far apart
    that no candidate nominal pair can bridge them within the ≤10% cap —
    even as bare single-anchor tiers either side — that is a genuine,
    evidenced discontinuity in the strain's OWN tested history, not
    something to force-close by fabricating an unsupported bridge tier or by
    exceeding the cap. The ladder then splits into independent segments,
    each internally fully contiguous, with an honest, flagged gap only at
    the specific seam the data itself cannot bridge (gap_after=True on the
    tier just below it).

    top_override (optional): an owner-set nominal for the strain's HIGHEST
    tier — the one holding the strain's top anchor. It only steers that one
    tier; every tier below still cascades from it by the standard top-down
    rule.

    Returns a list of dicts: nominal, tol, lo, hi, gap_after (bool),
    payloads (the payload objects for every batch the tier covers), and
    anchors (their raw values)."""
    strain_max = max(a for a, _ in items) if items else None

    def resolve(sub_items):
        sub_anchors = [a for a, _ in sub_items]
        plan = plan_contiguous(sub_anchors, floor, max_ratio, gap,
                               top_override=top_override, strain_max=strain_max)
        if plan is not None:
            for t in plan:
                t["gap_after"] = False
                t["payloads"] = [p for _a, p in sub_items[t["start"]:t["end"]]]
            return plan
        n = len(sub_items)
        assert n > 1, ("single anchor infeasible — below release floor?", sub_anchors)
        best_m = 1
        for m in range(n, 0, -1):
            if plan_contiguous(sub_anchors[:m], floor, max_ratio, gap,
                               top_override=top_override, strain_max=strain_max) is not None:
                best_m = m
                break
        left = plan_contiguous(sub_anchors[:best_m], floor, max_ratio, gap,
                               top_override=top_override, strain_max=strain_max)
        for t in left:
            t["gap_after"] = False
            t["payloads"] = [p for _a, p in sub_items[t["start"]:t["end"]]]
        left[-1]["gap_after"] = True
        return left + resolve(sub_items[best_m:])

    plan = resolve(items)
    return [dict(nominal=t["nominal"], tol=t["tol"], lo=t["lo"], hi=t["hi"],
                gap_after=t["gap_after"], payloads=t["payloads"], anchors=t["anchors"])
            for t in plan]


def build():
    # batch -> P-code (production/internal batch number), where on file.
    # Not every batch has one recorded — the map only carries what's known,
    # never invents one.
    p_codes = {}
    for row in cc.read_tsv("list_of_coas.tsv"):
        p = (row.get("p_number") or "").strip()
        b = (row.get("batch") or "").strip()
        if b and p and p.upper().startswith("P") and p[1:2].isdigit():
            p_codes[cc.norm_batch(b)] = p

    listing, _, _ = bl.build_rows()
    pot = [r for r in listing if r["no"] == "4" and not r["value"].startswith("Missing")]
    results = [dict(batch=r["batch"].strip(), strain=r["strain"].strip(), value=num(r["value"]),
                    printed=r["value"], date=r["date"], lab=r["lab"], cert=r["cert"],
                    p_code=p_codes.get(cc.norm_batch(r["batch"].strip())))
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
        # No mean/SD/CI: per owner instruction the summary statistics play no
        # part in setting a potency grade and are not shown in any document,
        # so they are not computed or stored at all. What a reader needs is
        # how many results exist and the span they actually occupy.
        stats[s] = dict(n=len(vals), min=vals[0], max=vals[-1], values=vals)

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

    # A batch's declaration is always its TIER's declaration — never computed
    # separately per batch. Two numbers for one batch (one in the stock table,
    # a different one on the strain board) is not an option: it is either the
    # same figure everywhere, or the document is not trustworthy. So this pass
    # only marks which batches have an anchor to build a grade from; the
    # NOMINAL ± TOLERANCE itself is assigned below, once per tier, and copied
    # onto every batch the tier covers.
    for b in stock:
        a = b["anchor"] if b["anchor"] is not None else b["declared"]
        b["proposed"] = None if a is None else True   # placeholder; set for real below
        b["basis"] = ("anchor" if b["anchor"] is not None
                       else ("declared (no assay on file)" if a is not None else None))

    # Per-strain warehouse GRADE TIERS (stock batches only) — build_strain_tiers
    # / plan_contiguous (see their docstrings): nominal on a half-percent
    # grid (NOM_STEP), ≤10% of nominal, and NO blind gap between adjacent
    # tiers of the same strain — tier i's ceiling sits exactly MIN_GAP below
    # tier i+1's floor, always, UNLESS the data itself contains a
    # discontinuity no candidate nominal pair can bridge within the cap
    # (gap_after=True; verified genuine below, never just narrowed-and-hoped).
    merged = {}
    n_tiers = n_gaps = 0
    for s in sorted({b["strain"] for b in stock}):
        bs = sorted([b for b in stock if b["proposed"] and b["strain"] == s],
                    key=lambda b: (b["anchor"] if b["anchor"] is not None else b["declared"]))
        if not bs:
            continue
        items = [((b["anchor"] if b["anchor"] is not None else b["declared"]), b) for b in bs]
        override = TOP_NOMINAL_OVERRIDE.get(s)
        tiers = build_strain_tiers(items, top_override=override)
        if override is not None:
            assert abs(tiers[-1]["nominal"] - override) < 1e-9, \
                (s, "top-nominal override not honoured — its ±10% band cannot cover the "
                 "strain's top tier at this grid; check the anchors", override, tiers[-1]["nominal"])
        n_tiers += len(tiers)
        for i, g in enumerate(tiers, 1):
            for b in g["payloads"]:
                b["tier"] = i
            for a in g["anchors"]:
                assert g["lo"] >= 5.0 - 1e-6, (s, g, a, "release floor")
                assert g["tol"] <= round(g["nominal"] * MAX_TOL_RATIO, 2) + 1e-6, \
                    (s, g, a, "10% ceiling")
                assert g["lo"] <= a <= g["hi"] + 1e-6, (s, g, a, "anchor must sit in its own tier")
            if i > 1:
                prev = tiers[i - 2]
                sep = round(g["lo"] - prev["hi"], 2)
                if prev["gap_after"]:
                    n_gaps += 1
                    assert sep > MIN_GAP + 1e-6, (s, "tier", i, "flagged gap_after but not actually wider than the minimum")
                    span = prev["anchors"] + g["anchors"]
                    assert plan_contiguous(span, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP) is None, \
                        (s, "tier", i, "gap_after flagged but a contiguous ladder actually exists — bug")
                else:
                    assert abs(sep - MIN_GAP) < 1e-6, \
                        (s, "tier", i, "not flagged as a genuine gap but isn't exactly contiguous", sep)
        merged[s] = [dict(range=[g["lo"], g["hi"]], nominal=g["nominal"], tol=g["tol"],
                          gap_after=g["gap_after"],
                          batches=[b["batch"] for b in g["payloads"]],
                          anchors=[round(a, 2) for a in g["anchors"]]) for g in tiers]

        # every batch's declaration IS its tier's declaration — one number,
        # never two — and headroom is measured from that same declared floor.
        for g in tiers:
            for b in g["payloads"]:
                a = b["anchor"] if b["anchor"] is not None else b["declared"]
                b["nominal"], b["tol"] = g["nominal"], g["tol"]
                b["proposed"] = [g["lo"], g["hi"]]
                b["headroom_down"] = round(a - g["lo"], 2)

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
        p_codes=p_codes,
        design=dict(
            max_tol_ratio=MAX_TOL_RATIO, min_gap=MIN_GAP, nom_step=NOM_STEP,
            top_nominal_override=dict(TOP_NOMINAL_OVERRIDE),
            rule=("Each tier is nominal ± tolerance, nominal always a multiple of %.2f%% "
                  "(20.00%%, 20.50%%, 21.00%% ... — never a finer fraction). " % NOM_STEP) +
                 "Tolerance never more than 10% of the nominal. "
                 "CONTIGUITY (the point of this design): adjacent tiers of the SAME strain "
                 "carry NO blind gap — tier i's ceiling sits exactly 0.01 below tier i+1's "
                 "floor, always, so a batch testing anywhere between two established grades "
                 "still has an applicable declaration; the same discipline the company's own "
                 "Portfolio-Master bracket system already uses (7/10/13/16/19/22/25% ladder — "
                 "fixed 3-point-wide bands, each boundary shared exactly with the next, zero "
                 "gaps end to end; see portfolio_master_brackets below). "
                 "TOP-DOWN, HIGHEST TIER FIRST (build_top_down): the ladder is declared from "
                 "the top down, the way it is done by hand. The HIGHEST (strongest) tier of a "
                 "segment gets PRIORITY — it takes its FULL ±10% width; nothing constrains a "
                 "segment's top edge from above, so the strongest grade is never squeezed. Each "
                 "LOWER tier then EXTENDS DOWNWARD from the one above: its ceiling is pinned "
                 "exactly 0.01 below the tier-above's floor, and it grabs AS MUCH of its own "
                 "±10% as it can while still reaching up to that ceiling — its nominal is the "
                 "SMALLEST half-percent grid value N with 1.1·N ≥ ceiling, so its tolerance "
                 "(ceiling − N) is as large as the cap allows. This makes the next lower nominal "
                 "and its ± fully PREDICTABLE from the tier above — not searched. There is no "
                 "'available width' box that crams an edge tier: a lower tier is only ever "
                 "narrower than its own full 10% because meeting the tier above exactly leaves "
                 "no more room, never for any other reason. "
                 "(Blue Sunset Sherbet, anchors 20.39/23.42/25.01 → Pot.-2 24.50% ±2.45% "
                 "[22.05%-26.95%] at its own full cap; Pot.-1 20.50% ±1.54% [18.96%-22.04%] — "
                 "as wide as it can be while its ceiling meets Pot.-2's floor at 22.04/22.05.) "
                 "The segmentation (how many tiers and where the cuts fall) is chosen by tier "
                 "COUNT first (fewest tiers that fit the data — a grade ladder should not "
                 "fragment into one tier per batch) and total |nominal-anchor| distance second, "
                 "so declared nominals stay honest to the results and never drift up merely to "
                 "buy width and overstate the product (plan_contiguous). "
                 "GENUINE GAPS: 2 of 24 strains (Graps & Creme; Orange Punch Mimosa) contain "
                 "two neighbouring tested results so far apart that NO candidate nominal "
                 "pair can bridge them within the ≤10% cap, even as bare single-anchor tiers "
                 "either side — the data itself has no batch anywhere near that band, not an "
                 "algorithm limitation. These are left as real, disclosed gaps (gap_after=true "
                 "on the tier below) rather than force-closed by fabricating an unsupported "
                 "'bridge' tier with zero evidence behind it, or by exceeding the 10% cap. A "
                 "future batch testing in one of these zones has no precedent in this strain's "
                 "history and should be assessed individually, exactly as any out-of-established-"
                 "range result would be. "
                 "RELEASE FLOOR: a tier's lower edge may never sit below 5.00 % Total THC. "
                 "A batch's declaration is always its tier's declaration — the same nominal ± "
                 "tolerance is printed everywhere that batch appears; there is no separate "
                 "per-batch figure. This is a PROPOSED revision of the grade bands, evidenced "
                 "from the data in this study; it does not itself amend any issued QCSP 001 "
                 "specification, whose nominal and range remain authoritative until changed "
                 "through the regular procedure."),
            portfolio_master_brackets=(
                "The company's own Portfolio-Master batch labels (portfolio_master.json, 78 "
                "batches, the source behind the renamed-strain board) already use a completely "
                "different, simpler system worth recording alongside the strain-specific ladder "
                "above: SEVEN fixed, strain-agnostic, contiguous 3-percentage-point brackets "
                "covering the whole practical range — 7–10 / 10–13 / 13–16 / 16–19 / 19–22 / "
                "22–25 / ≥25% — every boundary shared exactly with the next (10% ends one "
                "bracket and starts the next; no gap, no strain-by-strain customisation). A "
                "batch is simply assigned whichever fixed bracket contains its raw result — "
                "there is no per-strain 'nominal' concept at all in this system, and no evidence "
                "in that data of results being deliberately placed toward the top of their "
                "bracket (mean fractional position across 75 dated batches ≈ 0.50, i.e. "
                "centred, not skewed high)."),
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
    print("tiers: %d across %d strains · %d genuine (unbridgeable) gaps"
          % (n_tiers, len(merged), n_gaps))
    for s, g in merged.items():
        print("%-22s" % s, " + ".join("%.2f±%.2f [%.2f–%.2f]%s (%d)"
                                      % (x["nominal"], x["tol"], x["range"][0], x["range"][1],
                                         " |GAP|" if x["gap_after"] else "", len(x["batches"]))
                                      for x in g))
    return data


if __name__ == "__main__":
    build()
