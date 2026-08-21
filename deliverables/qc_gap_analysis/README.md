# Batch gap analysis — CoQ and internal CoA issuance counts

Derived **from the live RAGFlow `eCOA_INGEST` dataset on KVM4**, August 2026.
Every number is recomputed from the ingested certificates, not carried over
from an earlier working file.

## Headline counts

| Question | Answer |
|---|---|
| Production batches on file | **80** |
| Certificates of Quality to issue (one per batch) | **80** |
| CoQ **reissues** — Farmahem 197-series (cannabinoids + mycotoxins) | **21** |
| Batches needing the **full** internal CoA panel | **68** |
| Batches needing **Identification C only** | **12** |

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
| Cannabinoids (THC / CBD / CBN) | 76 | 4 |
| Loss on drying | 58 | 22 |
| Microbiology | 37 | 43 |
| Heavy metals | 49 | 31 |
| Pesticides | 43 | 37 |
| Mycotoxins | 22 | 58 |
| Identification A / appearance (macroscopy) | 12 | 68 |
| Identification B (microscopy) | 12 | 68 |
| Foreign matter (2.8.2) | 12 | 68 |
| **Identification C (TLC)** | **0** | **80** |

## Internal CoA issuance

| Scope | Batches |
|---|---:|
| Full panel — Identification A/B, Identification C, foreign matter | **68** |
| Identification C only (already hold a CNP Ph. Eur. certificate) | **12** |

Whether this is **68** or **80** documents is a QC decision: if Identification C
is discharged by a single risk-analysis annex citing the HPLC assay, only the 68
need an internal CoA. If Identification C must be stated per batch, all 80 do.

## Certificates on file, by issuing institution

| Institution | Certificates |
|---|---:|
| IPH — Institute of Public Health | 84 |
| UKIM Faculty of Pharmacy — CNP | 74 |
| Farmahem | 63 |
| Purely Plant GmbH (in-house) | 16 |
| State Phytosanitary Laboratory | 1 |
| **Total** | **238** |

## Method

1. All 389 documents and 9 302 chunks pulled from `eCOA_INGEST` via the
   RAGFlow API.
2. Documents classified cannabis vs water by analytical-method markers
   (`ISO 9308 / 6222 / 7899 / 7027 / 10523` → municipal water; cannabinoid /
   mycotoxin / Ph. Eur. markers → cannabis): **134 cannabis, 243 water,
   2 registers, 4 unreadable**.
3. `PP_Batch_Release_QC_Register.xlsx` — itself ingested into the dataset —
   parsed as the authoritative batch list: one numbered row per production
   batch, one sub-row per certificate.
4. Each of the 238 certificates classified by code pattern and issuing
   institution, then rolled up to per-batch coverage.

Note on term matching: CNP writes **`Макроскопија`** / **`Страни материи`**.
Searching for the adjectival stems (`макроскопск`, `туѓи примеси`) returns
nothing and produces a false "never tested" result. The scan here matches the
nominal forms.

## Open item

`GG1024.pdf` declares `Batch No: GG1024`, but the register carries no row under
that exact code — only `GG1024_01` and `GG1024_02`. `HPA1024` and `OPM1024` do
have their own rows (#79, #80). Either `GG1024` is a missing 81st row or it is
the parent of the two sub-lots. The counts above treat it as **not** a separate
batch; ruling the other way moves every total by one.

## Files

- `batch_gap_analysis.csv` — one row per production batch: certificate count,
  per-panel coverage, and the issuance flags (`needs_CoQ`,
  `needs_CoQ_reissue`, `iCoA_scope`).
