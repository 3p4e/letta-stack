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


MAX_TOL_RATIO = 0.10   # owner ceiling: declared ± tolerance may never exceed
                        # 10.0% of the nominal, for ANY batch or strain.


def declare(lo_req, hi_req, floor=5.0, max_ratio=MAX_TOL_RATIO):
    """Express a required coverage window as NOMINAL ± TOLERANCE.

    The nominal is a whole number (18.00 %, never 18.50 %) — it is the figure
    printed on the specification, the iCoA and the label. The tolerance is
    whatever it has to be for nominal ± tolerance to cover the entire required
    window, rounded UP to 0.01 — EXCEPT that per owner instruction it is
    capped at `max_ratio` (10%) of the nominal: no declared grade may carry a
    tolerance wider than ±10% of its own nominal, full stop. Returns
    (nominal, tolerance, capped) — `capped` is True when the 10% ceiling bit
    before the window's own required width did, i.e. the declared grade does
    NOT fully cover the one-year D+U window for this tier.

        e.g. window 15.69 – 20.31  ->  required tol 2.31 (< 10% of 18) -> 18.00 % ± 2.31 %, not capped
             window  9.7  – 22.9   ->  required tol 6.60 (> 10% of 16) -> 16.00 % ± 1.60 %, capped

    `floor` is the release acceptance criterion (≥ 5.00 % Total THC). A
    symmetric tolerance around a rounded-down nominal can reach below it, which
    would declare a grade whose own lower edge fails release — so the nominal is
    raised to the next whole number until the declared minimum clears the floor
    (the 10% cap rises together with the nominal, so this still terminates).
    """
    def tol_needed(n):
        return math.ceil(max(n - lo_req, hi_req - n) * 100 - 1e-9) / 100.0

    def tol_capped(n):
        return min(tol_needed(n), round(n * max_ratio, 2))

    nom = float(math.floor((lo_req + hi_req) / 2.0 + 0.5))   # half-up, not banker's
    tol = tol_capped(nom)
    for _ in range(64):                       # terminates once nom ≥ the midpoint
        if nom - tol >= floor - 1e-9:
            break
        nom += 1.0
        tol = tol_capped(nom)
    capped = tol_needed(nom) > round(nom * max_ratio, 2) + 1e-9
    return nom, tol, capped


def declare_group(anchors, lo_req, hi_req, floor=5.0, max_ratio=MAX_TOL_RATIO):
    """declare() for a MULTI-batch tier, made safe under the 10% ceiling.

    declare() alone picks its nominal from the D+U window's midpoint — fine
    when the window fits inside ±10%, but if capping is going to bite, that
    midpoint can sit outside the narrower band a ±10% tolerance can actually
    hold, which would leave one of the tier's OWN anchors outside its own
    declared range (not just failing the future guarantee — wrong today).

    So the nominal is instead clamped into the integer range that keeps EVERY
    anchor in the group within ±max_ratio of it — [max(a)/(1+r), min(a)/(1-r)]
    — which the caller must already have confirmed is non-empty (see
    cap_feasible(), used while clustering). Within that safe range, the
    integer closest to the D+U window's own midpoint is chosen, so the
    declaration still tracks the statistical ideal as closely as the ceiling
    allows. Returns (nominal, tolerance, capped).
    """
    lo_n = max(a / (1 + max_ratio) for a in anchors)
    hi_n = min(a / (1 - max_ratio) for a in anchors)
    lo_i, hi_i = math.ceil(lo_n - 1e-9), math.floor(hi_n + 1e-9)
    assert lo_i <= hi_i, ("declare_group called on a cap-infeasible anchor set — "
                          "clustering should never produce this", anchors)
    ideal = float(math.floor((lo_req + hi_req) / 2.0 + 0.5))
    nom = min(max(ideal, lo_i), hi_i)

    def tol_needed(n):
        return math.ceil(max(n - lo_req, hi_req - n) * 100 - 1e-9) / 100.0

    def tol_capped(n):
        return min(tol_needed(n), round(n * max_ratio, 2))

    tol = tol_capped(nom)
    while nom - tol < floor - 1e-9 and nom < hi_i:   # escalate without leaving the safe range
        nom += 1.0
        tol = tol_capped(nom)
    capped = tol_needed(nom) > round(nom * max_ratio, 2) + 1e-9
    return nom, tol, capped


def declare_single(anchor, floor=5.0, max_ratio=MAX_TOL_RATIO):
    """Grade declaration for a tier backed by exactly ONE tested batch.

    A single result gives no population to justify the normal degradation
    (D) + measurement-uncertainty (U) statistical window, so a flat POLICY
    tolerance is declared instead, per owner instruction: nominal ± 10% of
    the nominal itself — the SAME 10% ceiling that caps every other tier's
    tolerance too (declare()'s max_ratio), just applied directly since a
    single point has no window to measure a "required" tolerance from in the
    first place. The nominal is the batch's own anchor, rounded half-up to
    the nearest whole number; the tolerance is exactly max_ratio of that
    nominal, rounded UP to 0.01 (never truncated below the true 10%; for an
    integer nominal this rounding is a no-op — 10% of a whole number always
    lands on an exact cent).

        e.g. anchor 20.3x  ->  nominal 20.00  ->  tolerance 2.00
             20.00 % ± 2.00 %  (18.00 – 22.00 %)

    If a symmetric ±10% would put the declared floor under the 5.00 %
    release A.C., the nominal is escalated upward in whole-number steps
    (the same escalation rule as declare()) until it clears the floor.
    """
    nom = float(math.floor(anchor + 0.5))

    def tol_for(n):
        return math.ceil(n * max_ratio * 100 - 1e-9) / 100.0

    tol = tol_for(nom)
    for _ in range(64):
        if nom - tol >= floor - 1e-9:
            break
        nom += 1.0
        tol = tol_for(nom)
    return nom, tol


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

    # Per-strain warehouse GRADE TIERS (stock batches only). Greedy clustering
    # on ascending anchors over the TRUE required window: a tier opens at the
    # lowest batch's safe floor (anchor − D − U, floored at the 5.00% release
    # A.C.) and accepts further batches while the window stays ≤ W_MAX wide
    # once it also covers their safe ceiling (anchor + max(1.0, U) — the SAME
    # ceiling rule used everywhere else in this study, so a tier can never be
    # narrower than what an individual batch in it would need on its own).
    #
    # BUT: the owner's 10% ceiling on every tolerance (MAX_TOL_RATIO) makes
    # the OLD W_MAX=6.5 clustering unsafe on its own — a tier could be formed
    # whose anchors are up to 6.5 points apart, then get its tolerance capped
    # down to 10% of nominal, which for these values is only ~2-3 points wide.
    # A batch's OWN today-anchor could then fall outside its own tier's
    # capped range — not just fail the one-year guarantee, but be wrong today.
    # So clustering is instead done directly against what the 10% cap can
    # actually hold: a group of anchors can share one whole-number nominal N
    # with tolerance ≤ 10% of N iff 0.9·N ≤ a ≤ 1.1·N for every anchor a in
    # the group, i.e. N ∈ [max(a)/1.1, min(a)/0.9] is non-empty — equivalent
    # to max(a)/min(a) ≤ 1.1/0.9 ≈ 1.2222. A batch joins the running tier only
    # while that stays true; otherwise a new tier opens. This guarantees every
    # batch's own anchor sits inside its own tier's final declared range.
    def cap_feasible(anchors, max_ratio=MAX_TOL_RATIO):
        """True iff a WHOLE-NUMBER nominal exists that keeps every anchor
        within ±max_ratio of it. The real-valued interval [lo_n, hi_n] can be
        non-empty yet contain no integer (it is often under 0.1 wide for a
        tight anchor cluster) — checking only lo_n ≤ hi_n is not enough."""
        lo_n = max(a / (1 + max_ratio) for a in anchors)
        hi_n = min(a / (1 - max_ratio) for a in anchors)
        lo_i, hi_i = math.ceil(lo_n - 1e-9), math.floor(hi_n + 1e-9)
        return lo_i <= hi_i

    merged = {}
    for s in sorted({b["strain"] for b in stock}):
        bs = sorted([b for b in stock if b["proposed"] and b["strain"] == s],
                    key=lambda b: (b["anchor"] if b["anchor"] is not None else b["declared"]))
        if not bs:
            continue
        tiers = []
        cur = None
        for b in bs:
            a = b["anchor"] if b["anchor"] is not None else b["declared"]
            if cur is not None:
                ok = cap_feasible(cur["anchors"] + [a])
            if cur is None or not ok:
                cur = dict(batches=[b["batch"]], anchors=[a], rows=[b])
                tiers.append(cur)
            else:
                cur["batches"].append(b["batch"])
                cur["rows"].append(b)
                cur["anchors"].append(a)
            b["tier"] = len(tiers)
        for g in tiers:                       # declare, then re-verify per batch
            g["single_batch"] = len(g["batches"]) == 1
            if g["single_batch"]:
                g["nominal"], g["tol"] = declare_single(g["anchors"][0])
                g["capped"] = True            # ±10% policy IS the cap, always
            else:
                u_all = [U_RATIO * a for a in g["anchors"]]
                lo_req = min(max(5.0, a - D_YEAR - u) for a, u in zip(g["anchors"], u_all))
                hi_req = max(a + max(1.0, u) for a, u in zip(g["anchors"], u_all))
                g["nominal"], g["tol"], g["capped"] = declare_group(g["anchors"], lo_req, hi_req)
            g["lo"] = round(g["nominal"] - g["tol"], 2)
            g["hi"] = round(g["nominal"] + g["tol"], 2)
            for a in g["anchors"]:
                assert g["lo"] >= 5.0 - 1e-6, (s, g, a, "release floor")
                assert g["tol"] <= round(g["nominal"] * MAX_TOL_RATIO, 2) + 1e-6, \
                    (s, g, a, "10% ceiling")
                if g["single_batch"]:
                    # policy override: the only guarantee required is that the
                    # batch's own tested anchor sits inside its declared grade
                    # and the grade clears the release floor — the normal
                    # one-year D+U coverage guarantee does not apply (see
                    # declare_single's docstring).
                    assert g["lo"] <= a <= g["hi"] + 1e-6, (s, g, a, "single-batch anchor")
                elif not g["capped"]:
                    u = U_RATIO * a
                    # exact now: the declaration is derived from the window itself,
                    # and the tolerance only ever rounds outward.
                    assert g["lo"] <= max(5.0, a - D_YEAR - u) + 1e-6, (s, g, a, "floor")
                    assert a + u <= g["hi"] + 1e-6, (s, g, a, "ceiling")
                else:
                    # the 10% ceiling bit before the D+U window's own required
                    # width did — the declaration is intentionally narrower
                    # than the one-year guarantee would need. The only
                    # guarantee left is that TODAY's tested anchor sits inside
                    # the declared grade.
                    assert g["lo"] <= a <= g["hi"] + 1e-6, (s, g, a, "capped: anchor in range")
        merged[s] = [dict(range=[g["lo"], g["hi"]], nominal=g["nominal"], tol=g["tol"],
                          single_batch=g["single_batch"], capped=g["capped"],
                          batches=g["batches"],
                          anchors=[round(a, 2) for a in g["anchors"]]) for g in tiers]

        # every batch's declaration IS its tier's declaration — one number,
        # never two — and headroom is measured from that same declared floor.
        for g in tiers:
            for b in g["rows"]:
                a = b["anchor"] if b["anchor"] is not None else b["declared"]
                b["nominal"], b["tol"] = g["nominal"], g["tol"]
                b["single_batch"] = g["single_batch"]
                b["capped"] = g["capped"]
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
        design=dict(D_year=D_YEAR, U_ratio=U_RATIO,
                    rule="Required window: lower = anchor − D − U(anchor), floored at 5.00 "
                         "(release A.C.); upper = anchor + max(1.0, U(anchor)); merged per "
                         "strain while the window stays ≤ 6.5 points wide. "
                         "The window is then DECLARED as NOMINAL ± TOLERANCE, in the same "
                         "nominal-±-tolerance FORM the issued QCSP 001 specifications already "
                         "use — but here the nominal is fixed to a whole number (18.00 %, "
                         "never 18.50 % or 18.45 %, unlike the issued specs' bracket-midpoint "
                         "nominals). "
                         "OWNER CEILING: the tolerance may never exceed 10% of the nominal, for "
                         "ANY batch or strain — this binds every declaration in the study. "
                         "Where the window's own required tolerance is ≤ 10% of the nominal, "
                         "that required tolerance is used exactly (rounded UP to the next 0.01, "
                         "so rounding can only widen a declaration, never lose coverage), and "
                         "the tier fully covers the one-year D+U window (capped=false). Where "
                         "the required tolerance would exceed 10%, the ceiling wins instead "
                         "(capped=true): the declared grade is narrower than the one-year "
                         "guarantee would need, and the only thing guaranteed for that tier is "
                         "that TODAY's tested anchor(s) sit inside it — not a remeasure a year "
                         "from now. In THIS study every multi-batch tier is capped (their "
                         "natural D+U windows all exceed 10% of nominal), so capped=true "
                         "everywhere except where noted. "
                         "A batch's declaration is always its tier's declaration — the same "
                         "nominal ± tolerance is printed everywhere that batch appears; there "
                         "is no separate per-batch figure. This is a PROPOSED revision of the "
                         "grade bands, evidenced from the data in this study; it does not "
                         "itself amend any issued QCSP 001 specification, whose nominal and "
                         "range remain authoritative until changed through the regular "
                         "procedure. "
                         "SINGLE-BATCH TIERS (marked single_batch=true): with only one tested "
                         "result there is no population to justify the D+U window at all, so "
                         "the grade is nominal ± 10% of the nominal directly (declare_single()) "
                         "— the same 10% ceiling, just with nothing narrower ever computed to "
                         "be capped down from. capped is always true for these too."),
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
