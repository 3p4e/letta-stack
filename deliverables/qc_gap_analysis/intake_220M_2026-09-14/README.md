# Tranche 2 mycotoxin certificates — intake of 14.09.2026

Thirty-two Farmahem reports of analysis, `220-1-М/26` … `220-32-М/26`, from the Drive
folder `1. PP/DATA_B/QC_eCoA/Kkkk/T2M/220 Pjureli plant M` (each 2 pages; the SHA-256 of
every PDF is in `reads_gemini.json`). Received by the laboratory 17.08.2026, analysed
07.09.2026, issued 11.09.2026. Every certificate prints **ND** (< 0.5 µg/kg) for Aflatoxin
B1, B2, G1, G2 and Ochratoxin A, uncertainty "/".

## How they were read

The owner asked for these to be read directly rather than through the RAGFlow pipeline.
`reads_claude.json` is Claude's transcription of each certificate from the rendered page
crops (page 2's report number, dates, sample line and results table; page 1's issue-date
row), at 150 DPI — no text layer, no classical OCR. `reads_gemini.json` is an independent
read of the same pages by Gemini through the repository's own `extract_ecoa_records.read_gemini`,
kept only as a cross-check: all 32 agree with the transcription on every result, code, date
and batch (Gemini files the lab's submission number under `p_number`, which is a field
mapping, not a reading). The runner's read A (gpt-5) could not be served on 14.09.2026 —
OpenAI key refused, OpenRouter credit exhausted, CometAPI quota zero — which is why the
second read is Gemini's alone.

## Where each certificate goes

`placement.json`, and `apply_220M.py` re-derives it from the register it is given. 26 of
the 32 are the owner's Tranche 2 list; the laboratory also tested six more in the same
series: P050282 (Clemosa a Bud), P060042 and P060082 (Orange Punch Mimosa, Sleepy Joe),
and three batches printed with no P-number — JD042601, FB042601, CC042601.

23 certificates land in an existing register block. Nine batches have no block:
ACC102501 (P060122), CF102501 (P060132), GG1024, JD012603/01 (P060362), PUM102501
(P060112), CC012603 (P060372) — the six the delivery reconciliation of 07.09 and the
truth check of 14.09 found absent from the release register — and the three new batches.
The script opens a block for each, numbered on from the last one, with the strain the
certificate prints and its P-number where it prints one. Where it does not, the P-number
is the Head of QC's batch list's (`tracker/batch_dates.csv`, the one place the desk keeps
cultivation batch ↔ P-number): JD042601 = P060492, harvested 21.07.2026 and packaged
13.08.2026, four days before the laboratory received the sample. FB042601 and CC042601 are
on no list the desk holds — not the register, not the batch list, not the owner's tracker —
and keep no P-number; that is OI-33.

## The tracker

The tracker's document pool is the owner's tracker index plus `tracker/new_instances.json`
— never the release register, which gives the builder a certificate's family label and its
values but not the document. So the first v27 build, register written and schedule run,
rendered no 220 code in any tracker cell. `instances_220M.py` writes the 32 as #10 testing
instances into `new_instances.json` (idempotent, keyed on the code), the way the 30 IJZ-MB
certificates of 04.09.2026 went in, after checking that the two reads agree on the code,
the issue date, the batch and every result — one disagreement stops it. Aflatoxin B1 and
Ochratoxin A are the page's; Aflatoxins Σ is written ND only when B1, B2, G1 and G2 all
are, which is how the owner's 197-М/26 rows already read it.

Two definition gaps were found by that first build and are closed in the code:

- `family()` in `build_coq_schedule.py` labelled only the 197- series a re-analysis while
  `is_reanalysis()` already knew 220- was one, and the tracker files a retest by the
  label. The label now derives from `REANALYSIS_SERIES` — one list, which also carries the
  227- potency series the owner called retests on 12.09.2026 (none in the register yet,
  OI-32).
- Eight lots' in-house tracker cells looked their internal CoA up under another lot's key:
  the at-issue placeholder `iCoA — at issue (P060302)` folds to one key under `nkey()`,
  which strips a trailing parenthetical, so the last lot written held the key for all of
  them (SCR012601 in v26). Invisible while every one was at issue — the wrong lookup
  returned the same "— at issue —" — and wrong the day any of them was numbered. Fixed in
  `build_tracker_v8.py` (`_inst_ck`), and `verify_workbook.py` now checks that every
  lookup on the tracker keys its own lot (27 cells in v26 fail it).

## What v27 shows

Built 14.09.2026 from a copy of this tree with the register written and the instances in
place: 32 tracker cells cite a 220 certificate, `220-n-M-26, (11.09.2026) [FHM-M]`, in the
#10 retest row of its lot; the tracker carries 87 lots, up from 80 (ACC102501, CF102501,
PUM102501, CC012603, JD042601, FB042601, CC042601 — every one on the Work Order as a lot not
on the owner's tracker); the iCoA Register cites 27 of the codes and the CoQ Register 30
(220-17 and 220-18 are P060412 and P060422, two of the three P lots the owner's tracker
merges into JD012603, whose retest round cites 220-16; 220-30/31/32 have no dated round).
Against v26: 109 internal-CoA codes and 68 CoQ codes renumber, because a batch that
enters the register enters the issue-ordered series (GG1024's release round, dated
03.06.2026, becomes iCoA-PP_26-004), and 18 retest rounds take 11.09.2026 as their date.
`verify_workbook.py`: 0 findings, 5,350 printed results compared; `verify_prose.py`: 0.

`apply_220M.py --no-new-blocks` writes only the 23 certificates whose batch already has a
block and holds the nine, for the owner who wants the register's numbering to stand until
the nine batches are ruled on; then 50 internal-CoA codes renumber and no CoQ code does.

## Why this is a script and not a written register

The register is the owner's file. Writing it from this environment was refused twice on
14.09.2026 (auto-mode permission classifier: "Modify Shared Resources" — in place and as a
new dated version alike), so the write is packaged as one reviewable command:

    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/apply_220M.py

    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/instances_220M.py

then the usual chain — `build_coq_schedule.py`, `export_coq_artifact_data.py`, the tracker
build (`--version=27`) — picks the 32 results up as Tranche 2 mycotoxin retests (`220-` is
a re-analysis series, `is_reanalysis`).
