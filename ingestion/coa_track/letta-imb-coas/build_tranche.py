#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranche workbooks — the specification matrix restricted to one delivery tranche.

Usage: python3 build_tranche.py [1|2|3]   (default 1)

Same workbook, same rules, same verified data as exports/PP_Spec_Parameter_Matrix.xlsx,
filtered to the batches assigned to the requested tranche in
sources_of_truth/tranches_overview.tsv. Everything the master matrix holds for those
batches carries over unchanged: testing-round sub-rows, per-assay grade cells,
hyperlinked eCoA references, the certificate index (restricted to the certificates that
feed these batches) and the cover-sheet coverage table (recomputed for the subset). The
cover additionally shows the tranche delivery overview — THC bracket, declared THC and
volume per batch — transcribed from the tranches source of truth.

A tranche can include batches for which the ImB_QC_COAs knowledgebase holds no eCoA at
all (control-sheet-only batches). Those appear as all-Missing rows so the tranche is
complete rather than silently short, and they carry no '#' and no proposed CoQ number:
QCSOP 012 v.03 §6.4.1 does not allow a CoQ to be initiated before every specification
parameter is tested, so proposing a number would be premature. The cover names them.

The '#' and proposed CoQ numbers of on-file batches keep their master-matrix values
(chronological across all 77 batches), so a batch cites the same CoQ-PP-2026-NNNN here
and in the master document. Batch keys are matched through crosscheck_sources.norm_batch,
the same folding the eCoA register uses ('CJ052501/01' и 'CJ052501/1' are one batch).
"""
import os
import sys

import build_spec_matrix as bm
import build_spec_param_listing as bl
import crosscheck_sources as cc

HERE = os.path.dirname(os.path.abspath(__file__))
WORD = {"1": "One", "2": "Two", "3": "Three"}


def stub_batch(src):
    """An all-Missing row-block for a tranche batch with no eCoA on file."""
    batch = (src["batch"] or "").strip()
    y, m = bl.prod_key(batch)[:2]
    return {
        "chrono": "—", "prod": "%04d-%02d" % (y, m) if y != 9999 else "—",
        "batch": batch, "p": "—", "strain": (src["strain"] or "").strip(),
        "code": "—", "coq": "—", "round_labels": ["R1"],
        "rounds": [{no: {"values": [], "grades": [], "refs": [], "links": []}
                    for no, _t, _u, _ac in bm.MATRIX_PANEL}],
    }


def main(tranche="1"):
    word = WORD.get(tranche, tranche)
    listing, _stats, _n = bl.build_rows()

    t_rows = [r for r in cc.read_tsv("tranches_overview.tsv")
              if (r["tranche"] or "").strip() == tranche]
    if not t_rows:
        sys.stderr.write("no rows for tranche %r\n" % tranche)
        return 1
    want = {cc.norm_batch(r["batch"]): r for r in t_rows}

    on_file = {cc.norm_batch(r["batch"]) for r in listing}
    missing_keys = sorted(set(want) - on_file)

    subset = [r for r in listing if cc.norm_batch(r["batch"]) in want]
    n_results = sum(1 for r in subset if not r["value"].startswith("Missing"))
    n_missing = sum(1 for r in subset if r["value"].startswith("Missing"))

    rows = bm.pivot(subset) + [stub_batch(want[k]) for k in missing_keys]
    rows.sort(key=lambda b: bl.prod_key(b["batch"]))
    n_missing += len(missing_keys) * len(bm.MATRIX_PANEL)
    index_rows = bm.cert_index(subset)
    assert len(rows) == len(t_rows), (len(rows), len(t_rows))

    overview = []
    total_kg = 0.0
    for b in rows:
        src = want[cc.norm_batch(b["batch"])]
        kg = float(src["volume_kg"])
        total_kg += kg
        overview.append([b["batch"], b["strain"], src["thc_bracket"],
                         float(src["thc_pct"]), kg])
    overview.append(["TOTAL — %d batches" % len(rows), "", "", "", round(total_kg, 2)])
    note = None
    if missing_keys:
        note = ("No eCoA on file for: %s — shown as all-Missing rows; no CoQ number "
                "is proposed for them because QCSOP 012 v.03 §6.4.1 requires every "
                "specification parameter tested before a CoQ is initiated."
                % ", ".join(want[k]["batch"].strip() for k in missing_keys))

    out_xlsx = os.path.join(HERE, "exports", "Tranche_%s.xlsx" % word)
    out_tsv = os.path.join(HERE, "exports", "Tranche_%s.tsv" % word)

    # rebrand the shared builder for this subset, then restore it
    saved = {k: getattr(bm, k) for k in
             ("OUT_XLSX", "OUT_TSV", "MATRIX_TITLE", "READ_TITLE", "READ_SUBTITLE",
              "EXTRA_COVER")}
    try:
        bm.OUT_XLSX = out_xlsx
        bm.OUT_TSV = out_tsv
        bm.MATRIX_TITLE = (
            "Purely Plant — Tranche %s · QCSP 001 specification matrix for the %d "
            "Tranche %s batches · sub-rows = testing rounds · reading guide, tranche "
            "overview and coverage on the 'Read me' sheet · informal working export, %s"
            % (word, len(rows), tranche, bm.BUILD_DATE))
        bm.READ_TITLE = "Purely Plant — Tranche %s" % word
        bm.READ_SUBTITLE = (
            "QCSP 001 specification matrix restricted to the %d batches of delivery "
            "Tranche %s (sources_of_truth/tranches_overview.tsv) · '#' and proposed "
            "CoQ codes keep their master-matrix chronological numbering · informal "
            "working export, not a controlled document · built %s"
            % (len(rows), tranche, bm.BUILD_DATE))
        bm.EXTRA_COVER = (
            "TRANCHE %s — DELIVERY OVERVIEW (as recorded in tranches_overview.tsv)"
            % tranche,
            ["Batch", "Strain", "THC bracket", "Declared THC %", "Volume (kg)"],
            [13, 22, 12, 14, 12],
            overview, note)
        bm.write_xlsx(rows, index_rows, n_results, n_missing)
        bm.write_tsv(rows)
    finally:
        for k, v in saved.items():
            setattr(bm, k, v)

    print("tranche %s: %d batches (%d with no eCoA on file)   sub-rows: %d   "
          "result lines: %d   missing cells: %d   certs: %d   volume: %.2f kg"
          % (tranche, len(rows), len(missing_keys),
             sum(len(b["rounds"]) for b in rows), n_results, n_missing,
             len(index_rows), total_kg))
    print("wrote %s (%d KB)" % (os.path.relpath(out_xlsx, HERE),
                                os.path.getsize(out_xlsx) // 1024))
    print("wrote %s (%d KB)" % (os.path.relpath(out_tsv, HERE),
                                os.path.getsize(out_tsv) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "1"))
