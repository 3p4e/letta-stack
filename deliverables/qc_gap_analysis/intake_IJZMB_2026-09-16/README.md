# The IJZ-MB campaign microbiology — intake of 16.09.2026

Thirty certificates from the Institute of Public Health's microbiology department,
laboratory numbers `536/1067/26` … `565/1096/26`, for the campaign sampling the laboratory
received on **25/26.08.2026** and reported on **31.08.2026** (14) and **01.09.2026** (16).
Each is one page: TAMC, TYMC, bile-tolerant gram-negative bacteria, *Escherichia coli*,
*Pseudomonas aeruginosa*, *Staphylococcus aureus* and *Salmonella*, against Ph. Eur. 5.1.8
Kat. C and the manufacturer's specification. The scans are in the owner's
`eCoA_DATABASE`, named `<ddmmyy>_<code>_IJZ-MB_<batch>-<P lot>.pdf`.

## Why this intake exists

The thirty have been **testing instances on the tracker since 04.09.2026** and were never
rows of the **release register** — and the release register is the one source the
certificates of quality are compiled from. `OI-34` recorded the risk on 14.09.2026. The
cross-check of 16.09.2026 measured it:

> **24 certificates of quality print microbiology that a newer certificate for the same lot
> contradicts — twelve of them reissues.**

The gap is not cosmetic. P050012's certificate prints TAMC `2.1 × 10⁴` where the campaign
certificate for the same lot reads `< 10`; P050132 prints TYMC `3.3 × 10⁴` against `< 10`.
A reissue rests on a retest campaign, so it must print that campaign's microbiology. This
intake is the write that makes it do so.

## The gate

Every certificate carries **two independent reads** (the eCoA runner's A and B, ingested
04.09.2026) and a page whose SHA-256 and pixel verification are recorded in
`tracker/split_manifest_IJZ-MB_2026-09-01.csv` (30 of 30 pixel-verified).
`apply_IJZMB.load_reads()` compares the two reads on all five determinations the register
carries and **refuses to write anything if any certificate disagrees**.

* **Four disagreed on a value**, every one on the bile-tolerant gram-negative line and
  every one the same way: one read stopped at `< 10²` where the other carried the full
  range `< 10² и > 10`. `537/1068/26`, `542/1073/26`, `544/1075/26` and `547/1078/26` were
  each settled by a **third read of the page on 16.09.2026** (`read_C` in
  `reads_IJZMB.json`). **The fuller read was right all four times** — which is exactly the
  defect class `OI-36` records, now with four more instances.
* **Four differed only in how the laboratory spells absence** — `Отсутна`, `Отсуства`,
  `Отсуствa`, `Отсуствува`. `_fold()` reads those as one assertion, which is the standing
  vocabulary ruling of 11.09.2026, not a new judgement.

## What was written, and what was not

**29 rows into existing blocks; no block opened.** The row carries the five determinations
as the page prints them, `/` in every column the certificate does not report, the
laboratory number in the register's own spelling, the date of issue and
`IPH — Institute of Public Health` — the shape of the register's existing IJZ-MB rows.

Twelve lots' blocks are keyed by the cultivation batch with no P number on the label row;
they are found through the Head of QC's batch list and the scan's own file name
(P060162 = SJ102501, P060202 = J31112501, P060222 = OPM112501, P060252 = GG112501,
P060262 = J31122501, P060272 = CC112501, P060292 = FB112501, P060302 = GG012601,
P060312 = JD012601, P060392 = FB012603V, P060432 = FB012603, P060442 = SCR022601).

For **P060302 and P060312** the batch list writes the starred `GG012601＊` / `JD012601＊`
while the register block is labelled without the star. Placing them there **is not a ruling
on OI-28**: the `227-К/26` certificate of the *same lot* already sits in that same block,
put there by the intake of 15.09.2026, so this puts each lot's microbiology beside its own
potency and nothing more.

**One certificate is held back — `548/1079/26`.** It is filed under P050192 (BSS052501,
Blue Sunset Sherbet) because its typed serial reads `PO50192`. But the page prints the
strain **Sleepy Joe** and carries a **handwritten `P060192`**, and P060192 is SJ112501,
whose strain the register gives as Sleepy Joy. Which lot this certificate belongs to is the
Head of QC's to settle — `OI-37`. A microbiology result on the wrong lot's certificate is
worse than a missing one, so it is not written.

## The expanded panel

All thirty report *P. aeruginosa* and *S. aureus*, **absent on every one**. The owner's
release register has no column for them, so they are not written into it; they are kept in
`reads_IJZMB.json`. Until today `OI-13` stated that the expanded microbiology option "has
never been run" and that "neither is claimed on any certificate" — **that was false**: 31
certificates on file report the panel, the earliest from 01.12.2025. OI-13 is rewritten,
and what the certificates of quality should print for determinations #9.6 and #9.7, which
today print nothing, is put to the owner there.

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_IJZMB_2026-09-16/apply_IJZMB.py \
        --register <the owner's PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx>

Idempotent: a certificate already in the register is skipped, and the script reports what
it held back and why.
