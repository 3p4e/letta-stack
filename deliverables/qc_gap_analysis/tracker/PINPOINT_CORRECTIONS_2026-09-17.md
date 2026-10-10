# The three pinpoint corrections of 17.09.2026 — what each one turned out to be

> **The Head of QC, 17.09.2026**
>
> "I want you to do pinpoint corrections to **P050212** at parameter 9 — check the values,
> correct the microbiology parameter results and reference the eCOA **534/1065/26** and insert
> those results; **P050022** at parameter 9 correct and check the parameters under 9
> microbiology, TAMC and BT, and parameter 11 — in the eCOA for heavy metals all parameters are
> ND and in the CoQ there is an actual value inserted; **P060382**, check all the heavy metals
> parameters because in the CoQ there is no values and NT is entered and I'm sure there is an
> eCOA for it; for P060382 also in the CoQ there is no LoD tested and it says NT."

Three lots, three different answers. Two were real defects and are fixed; the third is a gap in
the testing, not in the desk, and it is named.

---

## 1 · P050212 — the certificate now references 534/1065/26 and prints its results

`534/1065/26` (IJZ-MB, received 25.08.2026, issued **31.08.2026**) was in no record the
certificates are compiled from. It belongs to the same delivery as the thirty the intake of
16.09.2026 took — same covering letter `03-500/1` of 24.08.2026, request 326/2026 beside that
intake's 324/2026 — but falls outside the 536–565 range that intake was scoped to. `OI-42` had
it listed as one of 58 scans cited in the Head of QC's own 09.09 pass and nowhere else.

Read twice on 17.09.2026, both reads agreeing on all seven lines, and written into the P050212
block. **`CoQ-PP_26-089` (the 12-month reissue) now prints:**

| # | parameter | was — `1032/1851/25` · 17.10.2025 | now — **`534/1065/26` · 31.08.2026** |
| --- | --- | --- | --- |
| 9.1 | TAMC | 2.2 × 10⁴ | **6,2 × 10³** |
| 9.2 | TYMC | 4.9 × 10⁴ · OUT OF SPECIFICATION | **2,3 × 10²** |
| 9.3 | bile-tolerant gram-neg. | < 10⁴ and > 10³ | < 10⁴ and > 10³ |
| 9.4 | *Salmonella* | Absent · Отсутна | Absent · Отсутна |
| 9.5 | *E. coli* | Absent · Отсутна | Absent · Отсутна |

The certificate's **date of issue moved with the document**, by the Head of QC's own ruling of
the same day: the new page is dated after the certificate was, so the standing issuance rule
re-dates it — **17.08.2026 → 07.09.2026**. `coq_register_2026-09-10.csv` and the master
workbook's CoQ Register were restamped to match.

**The release certificate `CoQ-PP_26-027` was not touched**, and that is deliberate: it states
the round that released the lot, where TYMC was 4.9 × 10⁴ and out of specification. A campaign
certificate is a retest document (the ruling of 10.09.2026), so no release certificate rests on
one. The excursion stays on the release record and is cleared on the reissue — which is what a
retest is for. `OI-17` is updated: P050212 is one of three of its thirteen lots now resolved.

`535/1066/26` came in with it, the same delivery for the sister lot P050222, and
`CoQ-PP_26-110` prints it (TAMC 4,2 × 10³, TYMC < 10). Its 18.09.2026 already postdates the
document, so that date did not move.

---

## 2 · P050022 — the certificate was citing the retest of each determination, not the release

This was not a reading error. **The certificate was citing the wrong document**, twice, and the
Head of QC found it by noticing that the arsenic figure did not match the report he was reading.

P050022 has two microbiology certificates and two contaminant reports:

| determination | release testing | retest |
| --- | --- | --- |
| #9.1–#9.5 | **`471-0862-25` · 22.05.2025** — TAMC 700, TYMC < 10, bile-tolerant < 10² и > 10 | `627/1128/25` · 02.07.2025 — all < 10 |
| #10.2, #11, #12 | **`2471/2025` · 30.05.2025** — aflatoxins Σ < 2, Pb/Cd/As/Hg all н.д., pesticides н.д. | `3176/2025` · 26.06.2025 — As 0.047 |

The release certificate `CoQ-PP_26-007` was printing the **later** document of each pair. Both
pages were read at full resolution, twice, on 17.09.2026. **`CoQ-PP_26-007` now prints:**

| # | parameter | was | now |
| --- | --- | --- | --- |
| 9.1 | TAMC | < 10 · `627/1128/25` | **700** · `471-0862-25` |
| 9.2 | TYMC | < 10 · `627/1128/25` | **< 10** · `471-0862-25` |
| 9.3 | bile-tolerant gram-neg. | < 10 · `627/1128/25` | **< 10² and > 10** · `471-0862-25` |
| 10.2 | aflatoxins Σ | < 2 · `3176/2025` | < 2 · **`2471/2025`** |
| 11.1 | lead | ND · `3176/2025` | ND · **`2471/2025`** |
| 11.2 | cadmium | ND · `3176/2025` | ND · **`2471/2025`** |
| 11.3 | **arsenic** | **0.047** · `3176/2025` | **ND** · **`2471/2025`** |
| 11.4 | mercury | ND · `3176/2025` | ND · **`2471/2025`** |
| 12 | pesticide residues | ND · `3176/2025` | ND · **`2471/2025`** |

The rule is the Head of QC's own, of 10.09.2026: *the first value of a parameter obtained is the
initial quality control testing, and every later one is a retest.* A release certificate is the
certificate of the release round, so it prints the **first** result on file — not the latest one
that happens to predate its issue date, which is what the compilation had been taking.
`apply_release_round.py` now states that, and a sweep of all eighty-nine release certificates
found **exactly two** in this position. The second is `CoQ-PP_26-010` (P050042): #9 cited
`2156/2025` of 07.05.2025 where `407-0745-25` of 05.05.2025 is the release page, two days
earlier, TAMC 10 against < 10. It is corrected the same way.

The reissue `CoQ-PP_26-095` keeps `627/1128/25` and `3176/2025` — a reissue states the retest,
and that is what those two documents are.

**Three register cells the pages disagreed with were corrected** at the same time, each from
the page: `471-0862-25` TYMC `10` → **`< 10`**; `2471/2025` pesticides `< LOQ` → **`N.D.`**; and
the aflatoxin column `2471/2025` never had → **`< 2`**. Recorded in
`intake_release_round_2026-09-17/`.

---

## 3 · P060382 — searched again, and there is nothing to cite

Everywhere the desk can reach, checked again on 17.09.2026:

| where | what it holds for P060382 |
| --- | --- |
| the release-register block | three documents: `364/0694/26` microbiology, `197-21-К/26` cannabinoids, `197-21-М/26` mycotoxins |
| the Head of QC's 09.09 resolution pass | "**NOTHING ON FILE** — no document anywhere" for loss on drying and for the contaminants |
| the eCoA spec listing | "Missing / not tested" |
| RAGflow | nothing beyond the three above |
| the owner's Drive — lot folder, title search, full-text search | the same two Farmahem reports and the microbiology, and nothing else |

The one lead worth chasing was `197-21-М/26`: Farmahem's "М" certificate might have carried
metals as well as mycotoxins. **It was downloaded and read at full resolution on 17.09.2026.**
Its own *Параметри кои се предмет на анализа* line reads *"Идентификација и квантификација на
микотоксини во сув цвет од канабис"*, and the report gives aflatoxins B₁, B₂, G₁, G₂ and
nothing else — no metals, no pesticides, no loss on drying.

So the certificate is right to print **"not tested — no certificate covers it"** for #8, #11 and
#12. This is a gap in the testing, not in the desk, and it is `OI-55` — either the reports exist
somewhere the desk cannot see, in which case one scan into `eCoA_DATABASE` closes it, or the lot
was never sent for those determinations and needs to be, or released explicitly without them.
P060382 is also one of the thirteen lots of `OI-53`, which asks the same question about loss on
drying for all of them.

---

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_IJZMB2_2026-09-17/apply_IJZMB2.py
    python3 deliverables/qc_gap_analysis/apply_microbiology_retest.py
    python3 deliverables/qc_gap_analysis/intake_release_round_2026-09-17/apply_release_reads.py
    python3 deliverables/qc_gap_analysis/apply_release_round.py

All four are idempotent.
