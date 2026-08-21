# Batch gap analysis — CoQ and internal CoA issuance counts

Derived **from the live RAGFlow `eCOA_INGEST` dataset on KVM4**, August 2026.
Every number below is recomputed from the ingested certificates, not carried
over from an earlier working file.

## Method

1. All 389 documents and 9 302 chunks pulled from `eCOA_INGEST` via the
   RAGFlow API.
2. Documents classified cannabis vs water by analytical-method markers
   (`ISO 9308 / 6222 / 7899 / 7027 / 10523` → municipal water;
   cannabinoid / mycotoxin / Ph. Eur. markers → cannabis).
   Result: **134 cannabis-related, 243 water, 2 registers, 4 unreadable**.
3. `PP_Batch_Release_QC_Register.xlsx` — ingested into the dataset — parsed as
   the authoritative batch list: one numbered row per production batch, one
   sub-row per certificate.
4. Each of the 238 certificates classified by its code pattern and issuing
   institution, then rolled up to per-batch panel coverage.

## Headline counts

| Question | Answer |
|---|---|
| Production batches on file | **80** |
| Certificates of Quality to issue (one per batch) | **80** |
| CoQ **reissues** — Farmahem 197-series (cannabinoids + mycotoxins) | **21** |
| CoQ reissues if 051/100-series retests also count | **29** |
| Internal CoAs to issue for untested Ph. Eur. parameters | **78** |

## Certificates on file, by issuing institution

| Institution | Certificates |
|---|---|
| IPH — Institute of Public Health | 84 |
| UKIM Faculty of Pharmacy — Center for Natural Products | 74 |
| Farmahem | 63 |
| Purely Plant GmbH (in-house) | 16 |
| State Phytosanitary Laboratory | 1 |
| **Total** | **238** |

## External panel coverage across the 80 batches

| Parameter | Tested | Not tested |
|---|---:|---:|
| Cannabinoids (THC / CBD / CBN) | 76 | 4 |
| Loss on drying | 58 | 22 |
| Microbiology | 37 | 43 |
| Heavy metals | 49 | 31 |
| Pesticides | 43 | 37 |
| Mycotoxins | 22 | 58 |
| **Identification A (macroscopic)** | **0** | **80** |
| **Identification B (microscopic)** | **0** | **80** |
| **Identification C (TLC)** | **0** | **80** |
| **Appearance / organoleptic** | **0** | **80** |
| **Foreign matter** | **0** | **80** |

Only **11 of 80** batches carry all six outsourced panels.

## The identification finding

No outsourced laboratory has ever reported Identification A, B or C,
appearance, or foreign matter for any batch. Those parameters do not appear as
columns in the batch register and appear in **zero** of the 134 cannabis
certificates.

They appear only in three **legacy Purely Plant in-house CoAs** —
`GG1024`, `HPA1024`, `OPM1024` — which carry Appearance (Visual),
Identification (HPLC retention time vs standard, per DAB) and
Foreign matter (< 2.0 %, Ph. Eur. 2.8.2).

This is consistent with the specification not having been defined when those
batches were released.

## Open item

`GG1024.pdf` declares `Batch No: GG1024`, but the register carries no row under
that exact code — only `GG1024_01` and `GG1024_02`. `HPA1024` and `OPM1024`,
by contrast, do have their own rows (#79, #80). Either `GG1024` is a missing
81st register row or it is the parent of the two `_01`/`_02` sub-lots. This
needs a QC decision before the CoQ set is finalised; the counts above treat
`GG1024` as **not** a separate batch.

## Files

- `batch_gap_analysis.csv` — one row per production batch: certificate count,
  per-panel coverage, and the three issuance flags
  (`needs_CoQ`, `needs_CoQ_reissue`, `needs_iCoA`).
