#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche One — the specification matrix restricted to the Tranche 1 batches.

Same workbook, same rules, same verified data as exports/PP_Spec_Parameter_Matrix.xlsx,
filtered to the 21 batches assigned to delivery Tranche 1 in
sources_of_truth/tranches_overview.tsv. Everything the master matrix holds for those
batches carries over unchanged: testing-round sub-rows, per-assay grade cells,
hyperlinked eCoA references, the certificate index (restricted to the certificates that
feed these batches) and the cover-sheet coverage table (recomputed for the subset). The
cover additionally shows the tranche delivery overview — THC bracket, declared THC and
volume per batch — transcribed from the tranches source of truth.

The '#' and proposed CoQ numbers keep their master-matrix values (chronological across
all 77 batches), so a batch cites the same CoQ-PP-2026-NNNN here and in the master
document. Batch keys are matched through crosscheck_sources.norm_batch, the same folding
the eCoA register uses ('CJ052501/01' и 'CJ052501/1' are one batch); the build fails
loudly if any tranche row does not resolve to exactly one matrix batch.
"""
import os
import sys

import build_spec_matrix as bm
import build_spec_param_listing as bl
import crosscheck_sources as cc

HERE = os.path.dirname(os.path.abspath(__file__))

TRANCHE = "1"


def main():
    listing, _stats, _n = bl.build_rows()

    t1 = [r for r in cc.read_tsv("tranches_overview.tsv")
          if (r["tranche"] or "").strip() == TRANCHE]
    want = {cc.norm_batch(r["batch"]): r for r in t1}

    matched = {}
    for rec in listing:
        key = cc.norm_batch(rec["batch"])
        if key in want:
            matched.setdefault(key, rec["batch"])
    unresolved = sorted(set(want) - set(matched))
    if unresolved:
        sys.stderr.write("tranche rows with no matrix batch: %s\n" % unresolved)
        return 1

    subset = [r for r in listing if cc.norm_batch(r["batch"]) in want]
    n_results = sum(1 for r in subset if not r["value"].startswith("Missing"))
    n_missing = sum(1 for r in subset if r["value"].startswith("Missing"))

    rows = bm.pivot(subset)
    index_rows = bm.cert_index(subset)
    assert len(rows) == len(t1), (len(rows), len(t1))

    overview = []
    total_kg = 0.0
    for b in rows:
        src = want[cc.norm_batch(b["batch"])]
        kg = float(src["volume_kg"])
        total_kg += kg
        overview.append([b["batch"], b["strain"], src["thc_bracket"],
                         float(src["thc_pct"]), kg])
    overview.append(["TOTAL — %d batches" % len(rows), "", "", "", round(total_kg, 2)])

    # rebrand the shared builder for this subset, then restore it
    saved = {k: getattr(bm, k) for k in
             ("OUT_XLSX", "OUT_TSV", "MATRIX_TITLE", "READ_TITLE", "READ_SUBTITLE",
              "EXTRA_COVER")}
    try:
        bm.OUT_XLSX = os.path.join(HERE, "exports", "Tranche_One.xlsx")
        bm.OUT_TSV = os.path.join(HERE, "exports", "Tranche_One.tsv")
        bm.MATRIX_TITLE = (
            "Purely Plant — Tranche One · QCSP 001 specification matrix for the %d "
            "Tranche 1 batches · sub-rows = testing rounds · reading guide, tranche "
            "overview and coverage on the 'Read me' sheet · informal working export, %s"
            % (len(rows), bm.BUILD_DATE))
        bm.READ_TITLE = "Purely Plant — Tranche One"
        bm.READ_SUBTITLE = (
            "QCSP 001 specification matrix restricted to the %d batches of delivery "
            "Tranche 1 (sources_of_truth/tranches_overview.tsv) · '#' and proposed "
            "CoQ codes keep their master-matrix chronological numbering · informal "
            "working export, not a controlled document · built %s"
            % (len(rows), bm.BUILD_DATE))
        bm.EXTRA_COVER = (
            "TRANCHE 1 — DELIVERY OVERVIEW (as recorded in tranches_overview.tsv)",
            ["Batch", "Strain", "THC bracket", "Declared THC %", "Volume (kg)"],
            [13, 22, 12, 14, 12],
            overview)
        bm.write_xlsx(rows, index_rows, n_results, n_missing)
        bm.write_tsv(rows)
    finally:
        for k, v in saved.items():
            setattr(bm, k, v)

    out_x = os.path.join(HERE, "exports", "Tranche_One.xlsx")
    out_t = os.path.join(HERE, "exports", "Tranche_One.tsv")
    print("tranche 1 batches: %d   sub-rows: %d   result lines: %d   missing: %d   "
          "certs: %d   volume: %.2f kg"
          % (len(rows), sum(len(b["rounds"]) for b in rows), n_results, n_missing,
             len(index_rows), total_kg))
    print("wrote %s (%d KB)" % (os.path.relpath(out_x, HERE),
                                os.path.getsize(out_x) // 1024))
    print("wrote %s (%d KB)" % (os.path.relpath(out_t, HERE),
                                os.path.getsize(out_t) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
