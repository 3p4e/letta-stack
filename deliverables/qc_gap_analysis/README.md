# Batch gap analysis — CoQ and internal CoA issuance counts

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

| Institution | Certificates |
|---|---:|
| UKIM Faculty of Pharmacy — CNP | 62 |
| IPH — Institute of Public Health | 43 |
| Farmahem | 30 |
| Purely Plant GmbH (in-house) | 15 |
| State Phytosanitary Laboratory | 1 |
| unattributed in register | 18 |

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

## GG1024 — a row missing from the register

`GG1024` is a genuine early production batch, confirmed by the owner. **The
register has no row for it**, although the two other batches of the same vintage,
`HPA1024` and `OPM1024`, do (#79, #80). It is carried here as **#81**.

It is not a stray document. `GG1024.pdf` (23.04.2025) is a complete Purely Plant
in-house release certificate covering Appearance (visual), Identification (HPLC
retention time, DAB), Foreign matter (< 2.0 %, Ph. Eur. 2.8.2), Assay,
Microbiology, Heavy metals, Pesticides and Aflatoxins. Only loss on drying is
absent.

**The register is therefore incomplete, and that is the finding.** Every count in
this document is drawn from the register, so a batch missing from it is a batch
missing from every downstream number until corrected.

A sweep of all batch codes declared inside the ingested certificates against the
register found three discrepancies and no more:

| Declared in a certificate | Verdict |
|---|---|
| `GG1024` | **genuine batch, row missing** — added as #81 |
| `FB012601/1` (ППК26067) | register holds `FB012601` (#53) without the `/1`. Elsewhere `/1` and `/2` sub-lots get their own rows (`CJ052501-1`, `CJ062501-2`), so this is either a sub-lot with no row or a notation inconsistency. **Needs a QC ruling.** |
| `MB0824` | parsing artifact — the certificate reads `серија: MB0824A104`, an OCR reading of `MB0824_04` (#6). Not a batch. |

## Files

- `batch_gap_analysis.csv` — one row per production batch: certificate count,
  per-panel coverage, and the issuance flags (`needs_CoQ`,
  `needs_CoQ_reissue`, `iCoA_scope`).
