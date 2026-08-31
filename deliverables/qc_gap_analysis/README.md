# Batch gap analysis — CoQ and internal CoA issuance counts

> ## The current workbook is `PP_Batch_Release_QC_Register_LINKED_2026-08-31.xlsx`
>
> This directory holds thirteen workbooks, one per correction pass, and **the file named
> `FINAL` is not the last one.** Each is the input to the next script's refuse-on-mismatch
> guard, so none can be deleted without breaking the chain that proves what changed; the
> order is what tells you which is current, and the order is:
>
> `CORRECTED` (owner-supplied) → `CORRECTED_2026-08-30` → `CORRECTED_2026-08-31` →
> `LINKS` → `MICRO` → `LINKS2` → `IPH` → `FHM` → `DATES` → `CNP` → `FINAL` → **`LINKED`**
>
> That order is not a guess and is not what the file listing suggests — an earlier version of
> this note had `MICRO` before `LINKS`, which is wrong. `replay_correction_chain.py` rebuilds
> the whole thing from the owner's original and compares each step, and the register proves
> the order itself: the committed `LINKS` does not carry the ten microbiology corrections,
> while `LINKS2` carries them *and* a different link on row 26 — because correcting that row's
> code from `319/0586/25` to `318/0585/25` changed which certificate it resolves to. The link
> moved because the code moved.
>
> Run `python3 deliverables/qc_gap_analysis/replay_correction_chain.py` to re-derive the
> corrected register from `CORRECTED.xlsx`. Every value at every step matches the committed
> workbook, and the final one matches exactly on values and links. Two link differences at the
> intermediate steps are expected and explained in that script's docstring: both are fixes
> made later in the week, landing earlier in the replay than they did in history.
>
> The counts below describe `CORRECTED.xlsx` and still hold. The correction passes changed
> values, links, dates and flags, and inserted one row (ППК25139); they did not add or
> remove a batch, and 284 is still the number of rows carrying a CoA code.
>
> Verification against the source documents is in `review/*_PAGE_VERIFICATION_2026-08-31.md`,
> `review/PDF_LINK_AUDIT_2026-08-31.md` and `review/BATCH_TEST_COVERAGE_2026-08-31.md`.
> 226 certificates were read off their pages; 1 033 of 1 073 populated result cells (96.3%)
> are now verified against a document.

Derived from **`PP_Batch_Release_QC_Register_CORRECTED.xlsx`** (owner-supplied,
modified 18.08.2026), parsed cell-by-cell with `openpyxl` — not from OCR.

> **Supersedes the first pass.** An earlier version of this analysis read the
> register through RAGFlow's OCR'd chunks of `PP_Batch_Release_QC_Register.xlsx`
> — the *uncorrected* file — and inferred coverage from certificate type rather
> than from cell values. That understated coverage badly: it reported 238
> certificates and 11 fully-covered batches against the true 284 and 43. The
> batch count (80), the reissue count (21) and the internal-CoA split (68 / 12)
> were unaffected.

## Headline counts

> **What the first three rows count, exactly.** Both figures are easy to misread from the
> register, and both were misread while writing this note — the numbers below are right and
> the misreading was mine.
>
> **81 batches on file; the register holds 80.** The eighty-first is `GG1024`, and
> `batch_gap_analysis.csv` marks it `in_register=N` — a batch with one certificate that never
> made it into the register. So "on file" is the right word and 81 is the right number, while
> any count taken *from* the register says 80 and is equally right: its Ref column runs 1 to
> 80 with no gaps. The CoQ row follows: 81 are owed, because `GG1024` is owed one too.
>
> **284 certificates is every row carrying something in the CoA-code column; 247 of them name
> a document.** The other 37 say a certificate does not exist: 17 read `(not numbered)`, 18
> read `n/a`, and 2 read `n/a — Purely Plant in-house CoA (… no certificate/report)`.
> 247 + 17 + 18 + 2 = 284 exactly, and the CSV's per-batch `certificates` column sums the
> same way, so the figure is self-consistent with its data.
>
> Whether those 37 belong in a count called "certificates on file" is a QC decision and is
> **not made here**, because it is not obvious in one direction. The 17 and the 18 are
> entirely empty rows and are plainly not certificates. The 2 in-house rows carry 16 result
> values each: they are records of testing that never got a certificate number, which is a
> different thing from nothing. Changing the number means recomputing the CSV's per-batch
> column on somebody else's definition of the word, so what is recorded here is the
> composition.
>
> Live per-batch testing coverage, measured against the current workbook by
> `deliverables/qc_gap_analysis/batch_test_coverage.py`: 80 register batches, **42** with both
> microbiology and physico-chemical results, **28** with none of microbiology, metals or
> mycotoxins. Those are not drop-in replacements for the 43 and 35 below — they count
> families of testing where the rows below count six named panels — but they are the live
> numbers and the script prints its own definitions.

| Question | Answer |
|---|---|
| Production batches on file | **81** |
| Certificates on file | **284** |
| Certificates of Quality to issue (one per batch) | **81** |
| CoQ **reissues** — Farmahem 197-series (cannabinoids + mycotoxins) | **21** |
| Batches needing the **full** internal CoA panel | **69** |
| Batches needing **Identification C only** | **12** |
| Batches complete on all six outsourced panels | **43** |
| Batches with **no** micro / metals / mycotoxin result | **35** |

## Parameter model

**Appearance and Identification A are the same test.** The Ph. Eur. macroscopic
examination of *Cannabis flos* (07/2024:3028) *is* the appearance examination —
they are not separate parameters and are not counted separately here.

Identification under the monograph, as reported by CNP:

| | Test | Performed by |
|---|---|---|
| **A** | Macroscopy — the appearance examination | CNP |
| **B** | Microscopy | CNP |
| **C** | TLC | **no laboratory — see below** |

## Who tests what

**CNP** (UKIM Faculty of Pharmacy, Center for Natural Products) issues a single
certificate covering identification, foreign matter, loss on drying and the
cannabinoid assay together:

> Метод: Идентификација (2.8.33), определување на страни материи (2.8.2),
> губиток со сушење (2.2.32) и содржина на канабиноиди (2.2.29) во цвет од
> канабис согласно монографијата (07/2024:3028) во Европската фармакопеја
> (Ph. Eur. 11.5)

**12 certificates** are in this format, covering register batches **#60–71**:

| ППК | Date | Batch |
|---|---|---|
| ППК26110 | 30.06.2026 | FB012603V |
| ППК26111 | 30.06.2026 | JD012603/02V |
| ППК26112 | 30.06.2026 | FB012603 |
| ППК26113 | 30.06.2026 | JD012603/02 |
| ППК26114 | 30.06.2026 | GG012603 |
| ППК26115 | 30.06.2026 | JD022601 |
| ППК26116 | 06.07.2026 | SCR022601 |
| ППК26117 | 06.07.2026 | P160012 |
| ППК26118 | 06.07.2026 | P160022 |
| ППК26119 | 06.07.2026 | P160032 |
| ППК26127 | 21.07.2026 | FB032601 — **Страни материи 0.08 %, НЕ ОДГОВАРА** (cannabis seed present) |
| ППК26128 | 21.07.2026 | GG032601 |

Earlier CNP certificates (ППК25xxx / ППК26001–26109 / ТПК25xxx) predate the
Ph. Eur. format and report only loss on drying and cannabinoids.

**Identification C (TLC) has never been performed by any laboratory** — zero
occurrences across all 389 ingested documents, including all 12 Ph. Eur.
certificates. It is discharged in-house by risk analysis with scientific
justification, using the qualitative determination from the HPLC cannabinoid
assay.

## External panel coverage across the 80 batches

| Parameter | Tested | Not tested |
|---|---:|---:|
| Cannabinoids (THC / CBD / CBN) | 81 | 0 |
| Loss on drying | 71 | 10 |
| Microbiology | 46 | 35 |
| Heavy metals | 46 | 35 |
| Pesticides | 46 | 35 |
| Mycotoxins | 53 | 28 |
| Identification A / appearance (macroscopy) | 12 | 69 |
| Identification B (microscopy) | 12 | 69 |
| Foreign matter (2.8.2) | 12 | 69 |
| **Identification C (TLC)** | **0** | **81** |

## Internal CoA issuance

| Scope | Batches |
|---|---:|
| Full panel — Identification A/B, Identification C, foreign matter | **69** |
| Identification C only (already hold a CNP Ph. Eur. certificate) | **12** |

Whether this is **69** or **81** documents is a QC decision: if Identification C
is discharged by a single risk-analysis annex citing the HPLC assay, only the 69
need an internal CoA. If Identification C must be stated per batch, all 81 do.

## Certificates on file, by issuing institution

The register carries 284 rows bearing a CoA code, but only **250 distinct codes** —
34 codes appear against more than one batch row, because one certificate can cover
several batches. The split below counts distinct codes.

| Institution | Certificates |
|---|---:|
| IPH — Institute of Public Health | 89 |
| UKIM Faculty of Pharmacy — CNP | 78 |
| Farmahem | 63 |
| Purely Plant GmbH (in-house) | 17 |
| State Phytosanitary Laboratory | 1 |
| unattributed in register | 2 |

> **Corrected 22.08.2026.** An earlier version of this table read 62 / 43 / 30 / 15
> / 1 / 18 and summed to 169 against a stated total of 284 — it counted only part
> of the register and is simply wrong. The error was caught by the cross-check in
> `CROSS_CHECK_2026-08-22.md`, where an independent build of the same evidence
> found 63 Farmahem certificates against the 30 stated here. No other figure in
> this document was derived from that table.

## Cohorts — outsourced coverage

| Batches | State | Range |
|---:|---|---|
| **43** | complete on all six panels | #1–51 |
| **28** | cannabinoids only — micro, metals, pesticides, mycotoxins never run | #42–71 |
| **7** | missing loss on drying, micro, metals, pesticides | #72–78 |
| **2** | missing loss on drying only | #79–80 |

The 35 batches with no microbiology, heavy-metal or mycotoxin result **cannot be
closed by an internal certificate** — they require samples sent to a laboratory.
That is a separate problem from the identification gap.

## Method

1. `PP_Batch_Release_QC_Register_CORRECTED.xlsx` parsed with `openpyxl`:
   header on row 4, specification limits on row 5, data from row 6. A row whose
   first cell holds an integer starts a batch; following rows are that batch's
   further certificates.
2. A panel counts as tested when **any** of its columns holds a real value for
   that batch — blank, `/`, `None`, `-` and `—` all read as absent.
   Cannabinoids = THC/CBD/CBN; micro = TAMC, TYMC, bile-tolerant GNB,
   Salmonella, E. coli; mycotoxins = aflatoxins Σ, aflatoxin B₁, ochratoxin A;
   metals = Pb, Cd, As, Hg.
3. Identification and foreign matter are **not columns in the register** — that
   coverage was established from the certificates themselves in `eCOA_INGEST`
   (389 documents, 9 302 chunks pulled via the RAGFlow API).
4. Cross-check: the 12 CNP Ph. Eur. certificates found in RAGFlow
   (ППК26110–26119, 26127, 26128) map to exactly batches #60–71 in the
   register, and the 21 batches carrying a 197-series certificate agree between
   both sources.

Note on term matching: CNP writes **`Макроскопија`** / **`Страни материи`**.
Searching for the adjectival stems (`макроскопск`, `туѓи примеси`) returns
nothing and produces a false "never tested" result. The scan here matches the
nominal forms.

## Batch identity — how a code is read

Two rules from the owner, and they interact:

- **The separator before a sub-lot index carries no meaning.** `GG1024/01`,
  `GG1024_01`, `GG1024-01` and `GG 1024_01` are one batch. Spacing and a leading
  zero on the index are equally insignificant.
- **A sub-lot index is part of a batch code, so a batch carrying one can carry
  another.** `GG1024_01/01` is sub-lot 01 of batch `GG1024_01` — a distinct record
  from its parent, with `GG1024_01/02` possible alongside it.

The CSV therefore carries a canonical `batch_key`: every segment normalised and
rejoined with `/`, so parent and child key apart and the hierarchy stays visible.
`GG1024_01` → `GG1024/1`; `GG1024_01/01` → `GG1024/1/1`. A trailing V marks a
verification sample and belongs to the identity — `JD012603-02V` → `JD012603/2V`,
which is not `JD012603/2`. CI asserts the column and that no two rows collapse onto
one key, which would be the same batch counted twice in every figure here. All 81
rows key distinctly.

### How often documents actually depart from the rule

The rule matters because the sources disagree constantly. `batch_spellings.py`
keys every batch code appearing in the register, on the certificate face, in the
scan filename and in this analysis, and groups them:

| | |
|---|---:|
| Batch keys observed across all sources | 121 |
| Recorded with **more than one** spelling | **35** |
| Most spellings of a single batch | **4** |

`GP0824/2` alone is written `GP 0824-02`, `GP 0824_02`, `GP0824-02` and
`GP0824_02`. The owner's example, `GG1024/1`, appears as `GG 1024_01`,
`GG1024-01` and `GG1024_01`. Full listing in `batch_spellings.csv`.

None of this is an error in the batches — it is an error waiting to happen in any
pipeline that keys on the string. One batch becomes three records, its certificates
scatter across them, and nothing looks wrong. Everything reading batch codes out of
documents must key through `ingestion/common/batch_id.py`.

### The convention changed between vintages

Reading the 81 batches as families exposes it:

| Vintage | Families | Parent has its own row |
|---|---|---|
| 2024 — `BSS1024`, `GG1024`, `HPA1024`, `OPM1024` | 4 | **4 of 4** |
| 2025 onward — `CJ052501`, `CJ062501`, `CJ082501`, `GP072501`, `GP0824`, `GP082501`, `GRC102501`, `JD012603`, `MB0824` | 9 | **0 of 9** |

In 2024 the parent bulk lot was registered and released in its own right; from 2025
only sub-lots are registered. That is not a defect, but it decides two open
questions below.

## GG1024 — a row missing from the register

`GG1024` is a genuine early production batch, confirmed by the owner. **The
register has no row for it**, although the two other batches of the same vintage,
`HPA1024` and `OPM1024`, do (#79, #80). It is carried here as **#81**.

It is not a stray document. `GG1024.pdf` is a complete Purely Plant in-house
release certificate on form `QCCoA 001v02`, a distinct two-page document with its
own SHA-256 (`8029082e7b163c6c`), held in both `ImB_COAs` and `ImB_QC_COAs`.

**The batch-identity rule settles it structurally.** `GG1024` is a 2024-vintage
parent whose sub-lots `GG1024_01` and `GG1024_02` are registered as #4 and #8. The
three other 2024 families — `BSS1024`, `HPA1024`, `OPM1024` — all carry a parent row
(#2, #79, #80) *and* sub-lot rows, and all three have a parent-level in-house
release CoA on disk (`HPA1024.pdf`, `OPM1024.pdf`, `BSS1024_CoA.pdf`) exactly as
GG1024 does. GG1024 is the only 2024 family missing its parent row. That is a
clerical omission, not an ambiguity.

**The register is therefore incomplete, and that is the finding.** Every count in
this document is drawn from the register, so a batch missing from it is a batch
missing from every downstream number until corrected.

A sweep of all batch codes declared inside the ingested certificates against the
register found three discrepancies and no more:

| Declared in a certificate | Verdict |
|---|---|
| `GG1024` | **genuine batch, row missing** — added as #81 |
| `FB012601/1` (ППК26067) | `/1` is a real sub-lot index under the identity rule, and FB012601 is a 2026 batch, where the convention registers sub-lots and not parents. Two independent readings confirm the certificate prints `/1`. So #53 should almost certainly read `FB012601/1` — or an unregistered sub-lot exists. **Still a QC ruling, but no longer an open question of fact.** |
| `MB0824` | parsing artifact — the certificate reads `серија: MB0824A104`, an OCR reading of `MB0824_04` (#6). Not a batch. |

## Cross-check against an independent build

`CROSS_CHECK_2026-08-22.md` compares every headline here against
`QC_eCoA_Database_ProductCoA_2026-08-22.xlsx`, an independent database built from
the 340 physical PDFs rather than from the register. The 21 CoQ reissues, the 12
CNP Ph. Eur. certificates, the FB032601 foreign-matter failure and the total
absence of Identification C all reproduce exactly. It also surfaces roughly ten
certificates released against a failing microbiological result — a class of
problem this coverage analysis does not look for — and raises one open QC decision
about the 41 in-house `QCCoA 001v02` release CoAs.

## Register revisions — which workbook is current

Each step is a separate script and a separate file, so any one of them can be
re-read, re-run or backed out without unpicking the others. **The current workbook is
`PP_Batch_Release_QC_Register_IPH_2026-08-31.xlsx`.**

| Workbook | Produced by | What it added |
|---|---|---|
| `..._CORRECTED.xlsx` | owner-supplied | the baseline this analysis is drawn from |
| `..._CORRECTED_2026-08-30.xlsx` | `apply_register_corrections.py` | six TYMC values read off the page; ten exceedances flagged amber |
| `..._CORRECTED_2026-08-31.xlsx` | `add_ppk25139_and_codes.py` | the ППК25139 row; four certificate codes confirmed; row 41 flagged |
| `..._LINKS_2026-08-31.xlsx` | `repair_register_pdf_links.py` | 166 PDF links repointed at their own certificate |
| `..._MICRO_2026-08-31.xlsx` | `apply_microbiology_corrections.py` | the ten microbiology corrections from reading all forty pages |
| `..._LINKS2_2026-08-31.xlsx` | `repair_register_pdf_links.py` (rerun) | 58 more links, after teaching the matcher four filename conventions |
| **`..._IPH_2026-08-31.xlsx`** | `apply_iph_corrections.py` | mercury on row 31, from the IPH physico-chemical page reads |

**Order matters in one place only.** `add_ppk25139_and_codes.py` inserts a row and
shifts everything below 46 down by one, so anything addressing rows by index must run
before it. `apply_register_corrections.py` does, and did. The two scripts that came
after it use post-insert row numbers, and `repair_register_pdf_links.py` addresses rows
by certificate code rather than by index, so it is immune either way.

## Files

- `CROSS_CHECK_2026-08-22.md` — the comparison, and the corrections it produced.
- `batch_spellings.py` / `batch_spellings.csv` — every spelling of every batch
  across the register, the certificate faces, the scan filenames and this
  analysis, keyed through `ingestion/common/batch_id.py`.
- `QC_eCoA_Database_ProductCoA_2026-08-22.xlsx` — the independent build, as
  supplied, unmodified.
- `batch_gap_analysis.csv` — one row per production batch: certificate count,
  per-panel coverage, and the issuance flags (`needs_CoQ`,
  `needs_CoQ_reissue`, `iCoA_scope`).

  `in_register` records whether the batch has a row in
  `PP_Batch_Release_QC_Register_CORRECTED.xlsx`. It is `N` only for `GG1024`,
  which is a genuine batch the register omits. CI reconciles the two: every
  register batch must appear here, and any row marked `N` must be explained in
  this README — so an omission from the register stays visible rather than being
  quietly absorbed into the totals.
