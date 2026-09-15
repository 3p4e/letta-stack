# Tranche 3 potency certificates — intake of 15.09.2026

Thirty Farmahem reports of analysis, `227-1-К/26` … `227-30-К/26`, from the ProcessedECOAs
folder (each 2 pages; Drive id and SHA-256 of every PDF in `reads_227K.json`). Received by
the laboratory 24.08.2026, analysed 07.09 or 09.09.2026, issued 11.09.2026. Each prints Total
Δ9-THC, Total CBD and Total CBN by HPLC/DAD, ИР 7.2.1-47К, accredited to MKS EN ISO 17025;
no specification column and no conclusion — a report of results. The owner ruled on
12.09.2026 that every one of them is a retest, and on 15.09.2026 gave the campaign its
sampling dates (`sampling_dates.py`: 19–21.08.2026, 10/10/10 by certificate number, internal
certificates issued 24.08.2026).

## How they were read

`reads_227K.json` is the page read of 12.09.2026 (Claude, rendered pages, no text layer, no
classical OCR), one record per certificate: dates, sample line, submission and sample
numbers, the three results with their uncertainties, methods, signatories, and the
reader's notes on each page. `checkpoint_master_coa_table.json` is the second read: the
transcription of the same day that was checkpointed into
`ingestion/coa_track/letta-imb-coas/exports/master_coa_table.tsv` (commit 7393bc4), 25 of
the 30, three result rows each. `apply_227K.py` compares the two on the batch, the P lot,
the issue date and every result and refuses to write on any disagreement; all 25 agree.

Five certificates the checkpoint does not hold rest on the page read alone and are written
with that said in the tracker instance's `source` and here: `227-1-К/26` (BSS1024_01/2,
P050142), `227-4-К/26` (WED102501, P060102), `227-8-К/26` (SCR012601, P060342),
`227-16-К/26` (GRC102501/1, P060142), `227-29-К/26` (BSS1024_01/1, P050122). OI-32 carries
them.

The reader transcribed the series letter as Latin K on 12 certificates and Cyrillic К on
18 — the glyphs are identical on the page and the notes say so. The register takes one
spelling, the Cyrillic К its 197-n-К/26 rows already use (`reg_code()`); the tracker index
takes its own, `227-n-K-26`.

## Where each certificate goes

26 land in an existing register block, found by the cultivation batch as printed or by the
P lot: `227-29-К/26` prints BSS1024_01/1 with P050122, the register's block is BSS1024_01 /
P050122 — the same packaged lot. Four batches have no block and are given one, numbered on
from the last (No. 90–93): BSS1024_01/2 (P050142), WED102501 (P060102), SCR012601 (P060342),
GRC102501/1 (P060142). All four are on the Head of QC's batch list with these P lots and
three of them on the Tranche 3 delivery list; their release testing is on no certificate the
register holds, which the CoQ Register already flags for each.

Every row is written in the shape of the Tranche 1 rows: THC % as printed, "≥ 5.00 %" in
THC spec, CBD % and CBN % as printed ("< LOQ" as "<LOQ"), "/" in every column the
certificate does not report, the code, 11.09.2026, "Farmahem", "Open". Idempotent: a code
already present is skipped.

`instances_227K.py` writes the 30 as #3–#6 testing instances into
`tracker/new_instances.json` (lab FHM-K, identification C "Conforms" on the HPLC profile,
THC, CBD, CBN as printed), the way the desk's index carries the 197-n-K-26 certificates;
the tracker's pool is the index plus that file, never the release register.

## What the intake changes downstream

`testing_series.rounds()` places a re-analysis certificate in a campaign round of its own,
never the release round, so each of the 30 batches has a Tranche 3 retest round: an
internal certificate tested on its sampling day and issued 24.08.2026 (iCoA Register), and
a reissue CoQ that waits for the batch's Tranche 3 mycotoxin certificate (none on file) and
says so on the CoQ Register.

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_227K_2026-09-15/apply_227K.py
    python3 deliverables/qc_gap_analysis/intake_227K_2026-09-15/instances_227K.py

then the v28 pipeline in `tracker/VOCABULARY_2026-09-11.md`.
