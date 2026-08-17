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

Grade design: per-batch anchor = most recent verified result. Tiers are then
built strictly left to right per strain so that they can never overlap — see
declare_tier() / build_strain_tiers() for the full rule (whole-number nominal,
tolerance as generous as allowed up to 10% of the nominal but always clearing
the previous tier's ceiling by at least 0.01, floored at the 5.00% release
acceptance criterion).
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
MIN_GAP = 0.01          # adjacent tiers must never touch, let alone overlap —
                        # at 2-decimal resolution this is the smallest
                        # possible separation (…nn.49% | nn.50%… style).


def cap_feasible_range(anchors, max_ratio=MAX_TOL_RATIO):
    """(lo_i, hi_i): the inclusive whole-number nominal range that keeps
    EVERY anchor within ±max_ratio of it. Empty (lo_i > hi_i) if no whole
    number works for the whole group — checking only that the real-valued
    interval [max(a)/(1+r), min(a)/(1-r)] is non-empty is not enough, since
    it can still contain no integer (often under 0.1 wide for a tight
    cluster)."""
    lo_n = max(a / (1 + max_ratio) for a in anchors)
    hi_n = min(a / (1 - max_ratio) for a in anchors)
    return math.ceil(lo_n - 1e-9), math.floor(hi_n + 1e-9)


def cap_feasible(anchors, max_ratio=MAX_TOL_RATIO):
    lo_i, hi_i = cap_feasible_range(anchors, max_ratio)
    return lo_i <= hi_i


def full_band(nominal, max_ratio=MAX_TOL_RATIO):
    """The FULL-WIDTH band for a whole-number nominal: nominal ± max_ratio
    of itself. Returns (lo, hi, tol). For an integer nominal the tolerance
    lands on an exact cent (10% of a whole number always does), so these
    are clean 2-decimal figures: 27 -> (24.30, 29.70, 2.70)."""
    tol = round(nominal * max_ratio, 2)
    return round(nominal - tol, 2), round(nominal + tol, 2), tol


def feasible_nominals(anchors, floor=5.0, max_ratio=MAX_TOL_RATIO):
    """Every whole-number nominal whose FULL ±max_ratio band both covers
    all of `anchors` and keeps its floor at or above the release criterion.

        0.9·N ≤ min(anchors)  and  1.1·N ≥ max(anchors)  and  0.9·N ≥ floor

    Returned as a range(); empty when no whole number satisfies all three —
    note the real-valued interval can be non-empty yet contain no integer,
    so the integer bounds are what matter."""
    lo_i = math.ceil(max(anchors) / (1 + max_ratio) - 1e-9)
    hi_i = math.floor(min(anchors) / (1 - max_ratio) + 1e-9)
    lo_i = max(lo_i, math.ceil(floor / (1 - max_ratio) - 1e-9))
    return range(lo_i, hi_i + 1)


def plan_full_width(anchors, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP):
    """Lay out a strain's whole tier ladder at once, every tier carrying its
    FULL ±max_ratio width. Returns [(start, end, nominal), ...] over the
    ascending `anchors`, or None when no such ladder exists.

    Why this is a global search and not a left-to-right greedy: with every
    band fixed at ±10% of a whole-number nominal, "where do the splits go"
    and "which nominal does each group get" are one joint decision. A greedy
    pass lets the FIRST tier take its widest legal band, which can leave the
    next group no room and force its tolerance down to a few percent — the
    tier gets squeezed for no reason other than the order it was built in.
    Choosing the whole ladder together avoids that: the split simply moves.

        Blue Sunset Sherbet, anchors 20.39 / 23.42 / 25.01
          greedy : {20.39, 23.42} -> 22.00 % ± 2.20 %   (19.80–24.20 %)
                   {25.01}        -> 25.00 % ± 0.79 %   (24.21–25.79 %)  ← squeezed
          this   : {20.39}        -> 20.00 % ± 2.00 %   (18.00–22.00 %)
                   {23.42, 25.01} -> 25.00 % ± 2.50 %   (22.50–27.50 %)  ← both full

    Objective: minimise Σ|nominal − anchor| over every batch, so each tier's
    declared nominal stays as close as possible to the results it actually
    represents (a nominal is a claim about the product — it should not drift
    above or below its own batches just to buy width). Ties break toward
    fewer tiers. Splits are otherwise free, so the ladder is as granular as
    the ±10% spacing allows: two tiers can only coexist when 1.1·N₁ + gap ≤
    0.9·N₂, i.e. N₂ ≳ 1.222·N₁.
    """
    n = len(anchors)
    if n == 0:
        return []
    # dp[i][N] = (cost, tier_count, split_index, previous_nominal) for the
    # best ladder covering anchors[:i] whose last tier has nominal N.
    dp = [dict() for _ in range(n + 1)]
    dp[0][None] = (0.0, 0, None, None)
    for i in range(1, n + 1):
        for j in range(i):
            run = anchors[j:i]
            for nominal in feasible_nominals(run, floor, max_ratio):
                lo, _hi, _tol = full_band(nominal, max_ratio)
                add = sum(abs(nominal - a) for a in run)
                for prev_n, (cost, count, _pj, _pn) in dp[j].items():
                    if prev_n is not None:
                        _plo, prev_hi, _ptol = full_band(prev_n, max_ratio)
                        if lo < prev_hi + gap - 1e-9:
                            continue          # would overlap or touch the tier below
                    cand = (cost + add, count + 1)
                    cur = dp[i].get(nominal)
                    if cur is None or cand < (cur[0], cur[1]):
                        dp[i][nominal] = (cand[0], cand[1], j, prev_n)
    if not dp[n]:
        return None
    best = min(dp[n], key=lambda N: (dp[n][N][0], dp[n][N][1]))
    out = []
    i, nominal = n, best
    while nominal is not None:
        _cost, _count, j, prev_n = dp[i][nominal]
        out.append((j, i, float(nominal)))
        i, nominal = j, prev_n
    out.reverse()
    return out


def declare_tier(anchors, prev_hi, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP):
    """FALLBACK ONLY — one tier, narrowed if it has to be.

    Used solely when plan_full_width finds no all-full-width ladder for a
    strain (does not occur in the current data: all 24 strains / 44 tiers
    plan at the full ±10%). Keeps the tolerance as generous as the room
    before `prev_hi` allows, down to whatever still covers the anchors."""
    lo_i, hi_i = cap_feasible_range(anchors, max_ratio)
    if lo_i > hi_i:
        return None
    amin, amax = min(anchors), max(anchors)
    ideal = float(math.floor((amin + amax) / 2.0 + 0.5))     # half-up, not banker's
    start = min(max(int(ideal), lo_i), hi_i)
    for nominal in range(start, hi_i + 1):                    # only ever gains room
        nominal = float(nominal)
        tol_needed = math.ceil(max(nominal - amin, amax - nominal) * 100 - 1e-9) / 100.0
        tol_cap = round(nominal * max_ratio, 2)
        room = (nominal - prev_hi - gap) if prev_hi is not None else tol_cap
        tol = min(tol_cap, room)
        if tol < tol_needed - 1e-9:
            continue                          # not enough room at this nominal — try the next
        lo = round(nominal - tol, 2)
        hi = round(nominal + tol, 2)
        if lo < floor - 1e-9:
            continue
        return dict(nominal=nominal, tol=tol, lo=lo, hi=hi)
    return None


def build_strain_tiers(items, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP):
    """items: [(anchor, payload), ...] ascending by anchor, all for one
    strain. Plans the whole ladder at full ±max_ratio width via
    plan_full_width; only if no such ladder exists does it fall back to the
    left-to-right greedy, which may narrow a tier.

    Returns a list of dicts: nominal, tol, lo, hi, full_width (bool),
    payloads (the payload objects for every batch the tier covers), and
    anchors (their raw values).
    """
    anchors = [a for a, _ in items]
    plan = plan_full_width(anchors, floor, max_ratio, gap)
    if plan is not None:
        tiers = []
        for j, i, nominal in plan:
            lo, hi, tol = full_band(nominal, max_ratio)
            tiers.append(dict(nominal=nominal, tol=tol, lo=lo, hi=hi, full_width=True,
                              payloads=[p for _a, p in items[j:i]], anchors=anchors[j:i]))
        return tiers

    tiers = []
    prev_hi = None
    idx, n = 0, len(items)
    while idx < n:
        cur = [idx]
        best = declare_tier([items[idx][0]], prev_hi, floor, max_ratio, gap)
        j = idx + 1
        while j < n:
            trial_anchors = [items[k][0] for k in cur + [j]]
            if not cap_feasible(trial_anchors, max_ratio):
                break
            trial = declare_tier(trial_anchors, prev_hi, floor, max_ratio, gap)
            if trial is None:
                break
            cur.append(j)
            best = trial
            j += 1
        assert best is not None, ("no non-overlapping tier fits this anchor set",
                                  [items[k][0] for k in cur], prev_hi)
        tiers.append(dict(nominal=best["nominal"], tol=best["tol"], lo=best["lo"],
                          hi=best["hi"],
                          full_width=abs(best["tol"] - round(best["nominal"] * max_ratio, 2)) < 1e-9,
                          payloads=[items[k][1] for k in cur],
                          anchors=[items[k][0] for k in cur]))
        prev_hi = best["hi"]
        idx = cur[-1] + 1
    return tiers


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

    # Per-strain warehouse GRADE TIERS (stock batches only), built strictly
    # left-to-right on ascending anchors so that no two tiers can ever
    # overlap (build_strain_tiers / plan_full_width — see their docstrings
    # for the full rule: whole-number nominal, every tier declared at the
    # full ±10% of its own nominal, the whole ladder planned at once so no
    # tier is squeezed by the order it happened to be built in).
    merged = {}
    n_full = n_narrow = 0
    for s in sorted({b["strain"] for b in stock}):
        bs = sorted([b for b in stock if b["proposed"] and b["strain"] == s],
                    key=lambda b: (b["anchor"] if b["anchor"] is not None else b["declared"]))
        if not bs:
            continue
        items = [((b["anchor"] if b["anchor"] is not None else b["declared"]), b) for b in bs]
        tiers = build_strain_tiers(items)
        for i, g in enumerate(tiers, 1):
            n_full += 1 if g["full_width"] else 0
            n_narrow += 0 if g["full_width"] else 1
            for b in g["payloads"]:
                b["tier"] = i
            for a in g["anchors"]:
                assert g["lo"] >= 5.0 - 1e-6, (s, g, a, "release floor")
                assert g["tol"] <= round(g["nominal"] * MAX_TOL_RATIO, 2) + 1e-6, \
                    (s, g, a, "10% ceiling")
                assert g["lo"] <= a <= g["hi"] + 1e-6, (s, g, a, "anchor must sit in its own tier")
            if i > 1:
                assert g["lo"] > tiers[i - 2]["hi"] + MIN_GAP - 1e-6, \
                    (s, "tier", i, "overlaps or touches the previous tier")
        merged[s] = [dict(range=[g["lo"], g["hi"]], nominal=g["nominal"], tol=g["tol"],
                          full_width=g["full_width"],
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
            max_tol_ratio=MAX_TOL_RATIO, min_gap=MIN_GAP,
            rule="EVERY tier is declared at its FULL width: nominal ± 10% of that nominal, "
                 "with the nominal always a whole number (20.00 %, never 20.50 %). So a tier "
                 "is completely described by one integer — 25 means 25.00 % ± 2.50 %, i.e. "
                 "22.50 %–27.50 %. No tier is ever narrower than this unless the data leaves "
                 "no alternative (see FALLBACK). "
                 "LADDER: a strain's tiers are planned ALL AT ONCE, not one after another "
                 "(plan_full_width). Two full-width tiers fit side by side only when "
                 "1.1·N₁ + 0.01 ≤ 0.9·N₂ — roughly N₂ ≥ 1.222·N₁ — which is what keeps them "
                 "from overlapping or even touching. Planning the whole ladder together is "
                 "the point: a left-to-right greedy lets the FIRST tier take its widest legal "
                 "band, which can leave the next group almost no room and squeeze its "
                 "tolerance down to a few percent for no better reason than build order. "
                 "Choosing the splits and the nominals jointly moves the split instead. "
                 "(Blue Sunset Sherbet, anchors 20.39/23.42/25.01: greedy gave 22.00 % ± "
                 "2.20 % then a squeezed 25.00 % ± 0.79 %; planned together it is 20.00 % ± "
                 "2.00 % and 25.00 % ± 2.50 %, both full width.) "
                 "OBJECTIVE: minimise Σ|nominal − anchor| across every batch, so each tier's "
                 "nominal stays as close as it can to the results it represents — a nominal "
                 "is a claim about the product and should not drift above or below its own "
                 "batches merely to buy width. Ties break toward fewer tiers; otherwise the "
                 "ladder is as granular as the ±10% spacing allows. "
                 "COVERAGE: a tier's band always contains every anchor assigned to it "
                 "(0.9·N ≤ min anchor and max anchor ≤ 1.1·N is exactly the feasibility test "
                 "used when choosing N). RELEASE FLOOR: a tier's lower edge may never sit "
                 "below 5.00 % Total THC, so N ≥ 6. "
                 "FALLBACK: if some strain admits no all-full-width ladder at all, that "
                 "strain alone falls back to a left-to-right pass that may narrow a tier; "
                 "such tiers are flagged full_width=false. This does not occur in the "
                 "current data — all 44 tiers across 24 strains plan at the full ±10%. "
                 "A batch's declaration is always its tier's declaration — the same nominal ± "
                 "tolerance is printed everywhere that batch appears; there is no separate "
                 "per-batch figure. This is a PROPOSED revision of the grade bands, evidenced "
                 "from the data in this study; it does not itself amend any issued QCSP 001 "
                 "specification, whose nominal and range remain authoritative until changed "
                 "through the regular procedure."),
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
    print("tiers: %d at full ±%.0f%% · %d narrowed"
          % (n_full, MAX_TOL_RATIO * 100, n_narrow))
    for s, g in merged.items():
        print("%-22s" % s, " + ".join("%.2f±%.2f [%.2f–%.2f] (%d)"
                                      % (x["nominal"], x["tol"], x["range"][0], x["range"][1],
                                         len(x["batches"])) for x in g))
    return data


if __name__ == "__main__":
    build()
