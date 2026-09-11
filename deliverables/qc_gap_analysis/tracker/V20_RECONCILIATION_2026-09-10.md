# Reconciling the owner's v20 workbook — 10.09.2026

`CoQ_Analysis_Master_v20.xlsx` arrived on 10.09.2026 (Drive
`1cBmbOgHSMlzIGyGjuZFRP5DagigtXx29`, modified 09.09.2026 13:55). It is vendored
here as `CoQ_Analysis_Master_v20_owner.xlsx` so everything below can be re-derived.

It carries something the desk did not have: a pass over the **387 PDFs in
`eCoA_DATABASE`**, read name for name, and **every one of the 600 determinations
of Tranches 1 and 2** resolved to a document, a laboratory, an issue date and the
result that document prints. That is evidence, and it has been taken into the
desk. The workbook also contradicts itself in four places, and those are not.

## 1. Where v20 disagrees with itself

| sheet | state | what it says | what supersedes it |
| --- | --- | --- | --- |
| `Summary Dashboard` | v13-era snapshot | 80 batches, 283 documents, 46 complete | `Dashboard v19` — 89 batches, 387 documents, 51 complete |
| `Batch Coverage v16` | superseded | 11 determination columns for a 12-determination specification — no Identification A | `Batch Coverage v19`, which restores it |
| `CoQ Parameter Tracker v13` | stale | has not absorbed the 155 certificates added on 09.09 | nothing in the workbook; that is the whole `on file, not recorded` column |
| `Delivery T1–T3` | v13-era | calls GG012603, J31102501 and KC102501 short of parameters the 09.09 pass covers, and calls eleven lots ready that `CoQ Readiness 09.09` blocks | `CoQ Readiness 09.09` |

The two readiness answers in that one workbook **disagree on 14 of the 50
batches** of Tranches 1 and 2. Where they disagree, the 09.09 sheets are the
later reading and are the ones used here; the delta is carried batch by batch in
`coq_draft_scope_2026-09-10.csv` so the choice is auditable rather than silent.

## 2. What was taken into the desk, and what was refused

Three sheets were lifted verbatim by `extract_v20_evidence.py` into flat sources
beside the schedule — `cell_resolution_2026-09-09.tsv` (600 rows),
`coverage_update_2026-09-09.tsv` (90) and `identity_block_2026-09-09.tsv` (40).
`cell_resolution.py` then decides, cell by cell, what the desk may print from
them. It refuses far more than it accepts, under four rules:

| | rule | cells |
| --- | --- | --- |
| 0 | a result the desk cannot cite by document code is not printable | 2 refused |
| 1 | a document that has not been issued certifies nothing | 118 refused |
| 2 | a single printed value fills a single printed line | accepted |
| 3 | a list the sheet does not label is not a mapping | 179 refused |

Rule 3 is not caution for its own sake. Microbiology prints five lines and heavy
metals four, and the sheet gives five and four values — in the certificate's own
order, with no analyte names. **On BSS1024, HPA1024 and OPM1024 the desk and this
sheet hold the same heavy-metal values against different analytes.** The order
cannot be assumed, so those cells stay blank.

**69 result cells** were filled, on determinations 3, 4, 5, 6, 8 and 12 — 36 of
them Total CBN, which was the single largest blank class on the certificates.
Nothing the desk already held was overwritten: **0 non-blank cells changed.**

## 3. What the two records say about the same 600 cells

| state | n | |
| --- | ---: | --- |
| agree | 218 | both hold a value and it is the same value |
| **values** | **43** | both hold a value and the values differ — a finding |
| **order** | **3** | the same values against different analytes — a finding |
| blocked | 110 | the only document is an iCoA that has not been issued |
| ambiguous | 51 | an unlabelled list of analyte values |
| basis note | 25 | the pass names where identity comes from, not a result |
| uncited | 2 | the only document carries no document code |
| none | 39 | neither record holds anything |
| not comparable | 86 | the two records hold different numbers of lines |
| no desk lot | 23 | the desk carries no initial-release CoQ for the batch |

Comparison is on what the two records **mean**, not how they spell it: `1.6×10⁴`
against `1,6 x 10⁴ CFU/g`, `N.D.` against `н.д.`, `Одговара (absent)` against
`Одговара /25 g` are the same result. Only a difference that survives that
counts.

**None of the 46 disagreements is resolved here.** The 09.09 pass compared 550
cells against page transcriptions and found no error in the tracker, so the
desk's value stands until a person reads the page. They are on the
`Reconciliation 09.09` sheet of v21 with both readings side by side. Three of
them need a person soonest:

- **GP0824_02 · #9**, certificate 471-0862-25 — the desk reads `<10, <10, <10`
  for TAMC, TYMC and bile-tolerant Gram-negatives; the pass reads
  `700, 10, <10² и >10`. Those are not the same result.
- **GP0824_02 · #11**, certificate 2471-2025 — the desk holds arsenic at
  `0.047 mg/kg`; the pass reads all four metals as not detected.
- **Total Δ⁹-THC on five lots.** The release assay — the figure that prints in
  the banner of the certificate — differs between the two records:

  | lot | certificate | the desk holds | the pass reads |
  | --- | --- | ---: | ---: |
  | HPA1024 | 197-13-K-26 | 14.97 | 19.68 % w/w |
  | OPM1024 | 197-17-K-26 | 19.96 | 20.03 % w/w |
  | GG1024 | 220-9-K/26 | 13.34 | 15.51 % w/w |
  | JD012603/02 | 220-17-K/26 | 20.54 | 14.43 % w/w |
  | JD012603/02V | 220-18-K/26 | 15.16 | 17.09 % w/w |

  None of the five is issuable today for other reasons, so nothing is printed on
  a disputed assay — but JD012603/02 differs by 6.11 points, which is a grade
  apart, and the page has to settle it.

One more is a value the desk now holds and should not print: **GG1024 · #8, loss
on drying `76.07 %` from ППК25008**, read in this pass. Against a ≤ 12.0 %
criterion that is not a loss on drying, and the schedule now marks the lot OUT OF
SPECIFICATION on the strength of it. GG1024 has no P lot and is not issuable
anyway, but the page has to be re-read before that figure is relied on.

## 4. The identity determinations are not a transcription problem

This is the finding that changes what "nearly ready" means. Identification A,
Identification B and foreign matter are blank on almost every lot in both
tranches, and the reason is not that nobody typed them in.

- **118 of the 600 cells cite an in-house `iCoA-PP_26-nnn` whose issue date is
  PLANNED**, on **40 of the 50 batches**. The certificate that carries the result
  has not been issued, so there is nothing to cite.
- Of the five in-house documents that do exist and were read: appearance is the
  single word "Confirms" with no description; **foreign matter is "Confirms"
  against a < 2.0 % specification with no percentage printed** — Ph. Eur. 2.8.2
  is gravimetric and EudraLex Vol. 4 Ch. 6 §6.7 requires the result; and
  **microscopy was not performed on any of them**.
- Three "Report of Analysis" documents carry no document code, no version and no
  report number (EudraLex Vol. 4 Ch. 4 §4.9). This build refuses to cite them.

Issuing the iCoAs does not by itself close this: the microscopy has to be
performed and the foreign-matter percentage has to be printed.

## 5. Four batches that were reported as having nothing on file

The delivery reconciliation of 07.09.2026 reported **ACC102501, CF102501,
PUM102501 and CC012603** as delivered with nothing on file anywhere. **That is now
out of date**: the 09.09 pass names certificates for all four. They still have no
row on Batch Coverage, because a Batch Coverage row is a tracker lot and these are
on no tracker lot, so the closure had nowhere to land — the lots have to be added
to the tracker first. v21's Delivery sheet now reads
`— CERTIFICATES ON FILE, NO TRACKER ROW —` for them rather than `— NO RECORD —`,
and names the certificates.

## 6. What v21 is

`CoQ_Analysis_Master_v21.xlsx`, built by

    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=21 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx --build-date=10.09.2026

v13 plus three things:

1. **A third mark on Batch Coverage.** `○` — the owner's own mark from
   `Batch Coverage v19` — means a certificate is on file for this parameter and
   the tracker does not name it. **84 parameters on 24 lots** now read `○` where
   they read `✗`. It is deliberately **not** counted as coverage: nothing can be
   cited on a certificate of quality until the desk records the document, so a
   `○` counts as missing and the missing list says why. Ready-to-issue therefore
   stays at 44 of 78 — the honest number — and the sheet now distinguishes an
   evidence gap from a record gap.
2. **A `Reconciliation 09.09` sheet** carrying everything in §2–§5 with the
   numbers behind it.
3. **The Delivery sheet corrected** for the four batches of §5.

`verify_workbook.py` and `verify_prose.py` both return **0 findings** on it, and
the deeper pass compares 5,567 printed results against the certificate records
with 0 findings. `verify_pages.py` was not re-run: it needs the certificate page
corpus, which is not in this container.

The artifact page is rebuilt at the same version — `coq_master_v21.html` — and
carries the reconciliation as a view of its own. Two repairs were needed to get
there: LibreOffice could not open a spreadsheet at all in this container
(`libreoffice-calc` was never installed, so the page pipeline had been broken for
several sessions), and the page's subtitle hard-coded `v11 · 05.09.2026` whatever
workbook built it — the same defect as the file name that was fixed for v13, in
the line underneath.

## 7. What it did to the certificates

The Tranche 1 and 2 drafts were recompiled from the reconciled desk:
**168 blank printed lines → 147**. Total CBN and the pesticide panel are gone
from the gap list entirely. What is left is exactly what §3 and §4 predict:

| line | blank on | why |
| --- | --- | --- |
| #1, #2, #7 | 21 of 22 each | the iCoA that carries them has not been issued (§4) |
| #10.1 Aflatoxin B₁, #10.3 Ochratoxin A | 22 of 22 each | the certificate reports the aflatoxin sum, not the single analytes |
| #9.1–9.5, #10.2, #11.1–11.4 | 4 lots | an unlabelled list of analyte values (rule 3) |

Eighteen of the 22 drafts now carry exactly five blank lines, and all five are
accounted for above. None of them is a transcription anyone can do today.
