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


def pairwise_bridgeable(prev_n, prev_max_anchor, nominal, run_min_anchor,
                         gap=MIN_GAP, max_ratio=MAX_TOL_RATIO):
    """Does SOME shared boundary exist between a tier declared at prev_n
    (whose own worst-case anchor is prev_max_anchor) and a new tier at
    `nominal` (whose own worst-case anchor is run_min_anchor), once each
    side's tolerance is free to be anything from "just enough to cover its
    own anchors" up to the 10% cap? Necessary for any valid transition;
    combined with solve_chain() below it is also sufficient once a full
    nominal sequence is fixed."""
    b_lo = max(prev_max_anchor, (1 - max_ratio) * nominal - gap)
    b_hi = min((1 + max_ratio) * prev_n, run_min_anchor - gap)
    return b_lo <= b_hi + 1e-9


def solve_chain(nominals, needs, caps, gap=MIN_GAP):
    """Given k candidate nominals (each a multiple of NOM_STEP) already known
    to be pairwise-bridgeable,
    solve for ONE symmetric tolerance per tier (nominal ± tol, same both
    ways — the declared format is always a single ± figure) such that the
    whole ladder is EXACTLY contiguous end to end: tier i's ceiling is
    always exactly `gap` below tier i+1's floor, never more, never less.

    tol_i + tol_{i+1} = nominal_{i+1} - nominal_i - gap  for every adjacent
    pair is a linear chain with one degree of freedom (the ladder can
    "slide"); every tol_i is expressed in terms of tol_0 via the alternating
    recurrence, and each tier's own [need, cap] bound is intersected back
    into a feasible range for tol_0.

    Within that range, tol_0 is chosen so the LAST tier of the segment gets
    its own full 10% cap whenever that is reachable — nothing constrains a
    segment's top edge from above, so it should never be squeezed just to
    "share" a slack that only the interior tiers actually need. Earlier
    tiers then absorb exactly as much squeeze as contiguity with that fixed
    top edge forces, never more. (Picking the midpoint of the feasible range
    instead — the previous approach — needlessly narrowed BOTH edges of a
    segment even though only an interior tier, if any, is ever structurally
    forced to give up width; confirmed by hand and by the owner against two
    real cases: Cash Cow's Pot.-3 and High Pro Amnesia's Pot.-2 both reach
    their full cap under this rule, not the previous 1.64%/1.64% squeeze.)
    If the full-cap target for the last tier falls outside what the rest of
    the chain can support, it clamps to the nearest feasible tol_0 instead —
    still the most generous top edge the chain allows.

    Returns [tol_1..tol_k] or None if no fully-symmetric solution exists for
    this exact nominal sequence (the caller then tries a different sequence
    — see build_strain_tiers)."""
    k = len(nominals)
    if k == 1:
        return [caps[0]] if needs[0] <= caps[0] + 1e-9 else None
    D = [round(nominals[i + 1] - nominals[i] - gap, 2) for i in range(k - 1)]
    A = [0.0] * k
    for i in range(1, k):
        A[i] = D[i - 1] - A[i - 1]
    lo_t0, hi_t0 = needs[0], caps[0]
    for i in range(k):
        if i % 2 == 0:
            lo_i, hi_i = needs[i] - A[i], caps[i] - A[i]
        else:
            lo_i, hi_i = A[i] - caps[i], A[i] - needs[i]
        lo_t0, hi_t0 = max(lo_t0, lo_i), min(hi_t0, hi_i)
    if lo_t0 > hi_t0 + 1e-9:
        return None
    last = k - 1
    # tol_last = A[last] + sign*tol_0; solve for the tol_0 that makes
    # tol_last equal caps[last] exactly, then clamp into the feasible range.
    target = (caps[last] - A[last]) if last % 2 == 0 else (A[last] - caps[last])
    tol0 = min(max(round(target, 2), lo_t0), hi_t0)
    tols = [tol0]
    for i in range(1, k):
        tols.append(round(D[i - 1] - tols[-1], 2))
    return tols


def _tiers_for_k(anchors, k, floor, max_ratio, gap):
    """Best (lowest Σ|nominal-anchor|) fully-contiguous, fully-symmetric
    ladder using EXACTLY k tiers over `anchors`, or None if none exists at
    this tier count. Exhaustive over the C(n-1, k-1) ways to cut `anchors`
    into k contiguous, non-empty runs — always small in practice (a single
    strain's tested-result count), so exhaustive is both simple and exact."""
    n = len(anchors)
    if k > n:
        return None
    best = None  # (cost, tiers)

    def eval_cuts(bounds):
        nonlocal best
        groups = [anchors[bounds[i]:bounds[i + 1]] for i in range(k)]
        cand_lists = []
        for g in groups:
            c = list(feasible_nominals(g, floor, max_ratio))
            if not c:
                return
            cand_lists.append(c)

        def choose(idx, chosen):
            nonlocal best
            if idx == k:
                needs = [max(nom - min(g), max(g) - nom) for nom, g in zip(chosen, groups)]
                caps = [round(nom * max_ratio, 2) for nom in chosen]
                tols = solve_chain(chosen, needs, caps, gap)
                if tols is None:
                    return
                cost = sum(abs(nom - a) for nom, g in zip(chosen, groups) for a in g)
                if best is None or cost < best[0] - 1e-9:
                    tiers = [dict(nominal=nom, tol=tol, lo=round(nom - tol, 2), hi=round(nom + tol, 2),
                                  anchors=g, start=bounds[gi], end=bounds[gi + 1])
                             for gi, (nom, tol, g) in enumerate(zip(chosen, tols, groups))]
                    best = (cost, tiers)
                return
            for nom in cand_lists[idx]:
                if chosen and not pairwise_bridgeable(chosen[-1], groups[idx - 1][-1], nom,
                                                        groups[idx][0], gap, max_ratio):
                    continue
                choose(idx + 1, chosen + [nom])

        choose(0, [])

    def cuts(start, groups_left, acc):
        if groups_left == 1:
            eval_cuts([0] + acc + [n])
            return
        for c in range(start + 1, n - (groups_left - 1) + 1):
            cuts(c, groups_left - 1, acc + [c])

    cuts(0, k, [])
    return best


def plan_contiguous(anchors, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP):
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
        res = _tiers_for_k(anchors, k, floor, max_ratio, gap)
        if res is not None:
            return res[1]
    return None


def build_strain_tiers(items, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP):
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

    Returns a list of dicts: nominal, tol, lo, hi, gap_after (bool),
    payloads (the payload objects for every batch the tier covers), and
    anchors (their raw values)."""
    def resolve(sub_items):
        sub_anchors = [a for a, _ in sub_items]
        plan = plan_contiguous(sub_anchors, floor, max_ratio, gap)
        if plan is not None:
            for t in plan:
                t["gap_after"] = False
                t["payloads"] = [p for _a, p in sub_items[t["start"]:t["end"]]]
            return plan
        n = len(sub_items)
        assert n > 1, ("single anchor infeasible — below release floor?", sub_anchors)
        best_m = 1
        for m in range(n, 0, -1):
            if plan_contiguous(sub_anchors[:m], floor, max_ratio, gap) is not None:
                best_m = m
                break
        left = plan_contiguous(sub_anchors[:best_m], floor, max_ratio, gap)
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
        tiers = build_strain_tiers(items)
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
            rule=("Each tier is nominal ± tolerance, nominal always a multiple of %.2f%% "
                  "(20.00%%, 20.50%%, 21.00%% ... — never a finer fraction). " % NOM_STEP) +
                 "Tolerance never more than 10% of the nominal. "
                 "CONTIGUITY (the point of this design): adjacent tiers of the SAME strain "
                 "carry NO blind gap — tier i's ceiling sits exactly 0.01 below tier i+1's "
                 "floor, always, so a batch testing anywhere between two established grades "
                 "still has an applicable declaration; the same discipline the company's own "
                 "Portfolio-Master bracket system already uses (7/10/13/16/19/22/25% ladder — "
                 "fixed 3-point-wide bands, each boundary shared exactly with the next, zero "
                 "gaps end to end; see portfolio_master_brackets below). Tolerance is therefore "
                 "at the FULL 10% cap whenever the data allows it, and shrinks below that ONLY "
                 "as far as needed to meet the neighbouring tier exactly — never to leave a gap, "
                 "never past what still covers every anchor assigned to the tier. The two goals "
                 "(generous ±10% width, and zero gaps) are not always simultaneously reachable "
                 "for a given pair of candidate nominals: full ±10% on both sides can itself "
                 "leave a gap if the nominals end up too far apart. Where that happens the "
                 "nominal choice itself changes, or (within one segment) the LAST tier keeps its "
                 "own full cap and earlier tiers absorb exactly the squeeze that forces (Blue "
                 "Sunset Sherbet, anchors 20.39/23.42/25.01: Pot.-2 sits at its own full cap, "
                 "23.50% ±2.35% [21.15%-25.85%]; Pot.-1 is squeezed to 20.50% ±0.64% "
                 "[19.86%-21.14%] — not because it needs to be that narrow to cover its own "
                 "anchor, but because Pot.-2's full-width claim leaves it no more room, and the "
                 "half-percent grid picks 20.50 over 20.00/21.00 as the closest fit); "
                 "solve_chain() finds the tolerance split, and the whole "
                 "ladder is planned by tier COUNT first (fewest tiers that fit the data — a grade "
                 "ladder should not fragment into one tier per batch just because that shaves a "
                 "few hundredths off the fit) and total |nominal-anchor| distance second, over "
                 "every candidate nominal sequence (a half-percent grid) that is provably "
                 "bridgeable end to end (plan_contiguous). "
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
