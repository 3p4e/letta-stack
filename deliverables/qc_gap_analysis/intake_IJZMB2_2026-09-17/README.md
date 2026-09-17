# The two IJZ-MB certificates the first intake could not reach — intake of 17.09.2026

`534/1065/26` (**P050212**, CJ062501-2, Cap Junky) and `535/1066/26` (**P050222**,
CJ062501/1, Cap Junky), both issued **31.08.2026** by the Institute of Public Health's
microbiology department.

They belong to the same campaign delivery as the thirty the intake of 16.09.2026 took:
the same covering letter `03-500/1` of 24.08.2026, requests **325/2026** and **326/2026**
beside that intake's 324/2026, received **25.08.2026**, reported 31.08.2026, the same
seven-line panel against Ph. Eur. 5.1.8 Kat. C and the manufacturer's specification. They
fall **outside the 536–565 range** the first intake was scoped to, which is exactly where
`OI-42` left them — named in the Head of QC's own 09.09 resolution pass, present on Drive,
and in no record the certificates of quality are compiled from.

## Why now

The Head of QC asked for `534/1065/26` by number on 17.09.2026 — *"reference the eCOA
534/1065/26 and insert those results"* — and then gave the rule that generalises it:

> "If the certificate for microbiological purity from the external laboratory is at a newer
> date, meaning we have retested that parameter, you will also have to adjust the dating,
> the date of issue of the certificate of quality accordingly."

`apply_microbiology_retest.py` is that rule. This is the intake it needs. `535/1066/26` comes
with it because it is the same delivery for the sister lot and the rule reaches it the same
way.

## The gate

**Two reads of each page, and they agree on all seven lines of both.** The eCoA runner holds
no read of either page — they were never ingested — so both reads are the desk's own, taken
on 17.09.2026 from separate renderings of the scan, and `reads_IJZMB2.json` says so rather
than calling them A and B as though a second system had produced one. `disagreements()`
refuses to write anything if the two ever stop agreeing. The SHA-256 of each scan as
downloaded is recorded beside the reads.

| | 534/1065/26 · P050212 | 535/1066/26 · P050222 |
| --- | --- | --- |
| TAMC | 6,2 × 10³ CFU/g | 4,2 × 10³ CFU/g |
| TYMC | 2,3 × 10² CFU/g | < 10 CFU/g |
| bile-tolerant gram-negative | < 10⁴ и > 10³ CFU/g | < 10⁴ и > 10³ CFU/g |
| *E. coli* | Отсутна/g | Отсутна/g |
| *P. aeruginosa* | Отсутна/g | Отсутна/g |
| *S. aureus* | Отсутна/g | Отсутна/g |
| *Salmonella* | Отсутна/25 g | Отсутна/25 g |
| conclusion | СЕ ВО СОГЛАСНОСТ | СЕ ВО СОГЛАСНОСТ |

Both typed serials read with a letter O — `PO50212`, `PO50222` — as this laboratory's forms
do. Unlike `548/1079/26`, which `OI-37` still holds back, nothing else on either page
disagrees: the strain is Cap Junky on both and the lots are the two Cap Junky lots, so there
is no identity question to settle.

## What was written, and what was not

**Two rows, into the existing P050212 and P050222 blocks; no block opened.** TAMC, TYMC,
bile-tolerant gram-negative bacteria, *Salmonella* and *E. coli* in columns J … N, in the
spelling the register's own IJZ-MB rows carry, with the laboratory number, the date of issue
and `IPH — Institute of Public Health`.

*P. aeruginosa* and *S. aureus* are reported on both pages and absent on both. The owner's
release register has no column for either, so they stay in `reads_IJZMB2.json` — which is
what `OI-13` puts to the Head of QC for determinations #9.6 and #9.7.

Both codes were added to `testing_series.RETEST_ONLY`. They are the same campaign as the
thirty, so they are the same kind of document: **retest, never release.** A release
certificate of quality cannot rest on either, and nor should it — the ruling of 10.09.2026
already said so of the delivery they belong to.

## What it changed downstream

`534/1065/26` is what `CoQ-PP_26-089` (the P050212 12-month reissue) now prints for #9.1–#9.5,
in place of `1032/1851/25` of 17.10.2025 — and since the new document is dated **after** the
certificate was, the certificate's date of issue moves with it. `535/1066/26` does the same
for `CoQ-PP_26-110`, whose 18.09.2026 already postdates it, so that date does not move.
`apply_microbiology_retest.py` has the arithmetic and the full list.

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_IJZMB2_2026-09-17/apply_IJZMB2.py [--dry-run]

Idempotent: a certificate already in the register is skipped.
