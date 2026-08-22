# Cross-check against the independent eCoA database build

Two people built a certificate database from the same evidence base, from opposite
ends, without seeing each other's work:

| | This analysis | `QC_eCoA_Database_ProductCoA_2026-08-22.xlsx` |
|---|---|---|
| Anchor | `PP_Batch_Release_QC_Register_CORRECTED.xlsx`, one row per batch | the 340 physical PDFs in `ImB_COAs` + `ImB_QC_COAs` |
| Reading | cell-by-cell `openpyxl`, plus RAGFlow `eCOA_INGEST` for identification | every page re-read from the rendered image, field by field |
| Question | which batches lack which panel, and how many documents must be issued | what does each certificate actually say |
| Blind to | what a certificate says beyond the panel it covers | which batches exist — no batch master list was available |

That makes the comparison worth doing: where two independent methods land on the
same number, the number is probably right. Where they diverge, the divergence
localises a real defect in one of them.

## Where the two builds agree exactly

| Finding | This analysis | Shared workbook |
|---|---|---|
| Farmahem 197-series retest campaign | 21 batches | 21 `197-n-K/26` + 21 `197-n-M/26` reports, **21 distinct batches** |
| → CoQ reissues to raise | **21** | same 21 batches, matched one-for-one, no residue on either side |
| CNP Ph. Eur. 3028 certificates | 12 (ППК26110–26119, 26127, 26128) | 12 certificates carrying `Страни материи` — the same 12 numbers |
| Foreign-matter non-conformity | FB032601, 0.08 %, НЕ ОДГОВАРА | ППК26127, `0.08% (Не одговара)` |
| Identification C (TLC) | never performed, 0 of 81 | no TLC parameter anywhere in 2 416 transcribed results |
| Farmahem certificates on file | 63 | 63 |
| Batch population | 81 batches | 78 of those 81 carry at least one certificate |

The 197-series agreement is the strongest single result here. Two different
extraction paths, one from register cells and one from scanned report headers,
produced the same 21 batches with no batch appearing in one and not the other.
**The 21 CoQ reissues can be treated as settled.**

Identification C is the second. A build that read every page of every certificate
found no thin-layer chromatography anywhere. The in-house risk-analysis route,
citing the qualitative HPLC determination, remains the only way to discharge it.

## Where the numbers look different but are not

**"188 batches" versus 81.** Sheet `7_Batch_Index` lists batch strings exactly as
printed, deliberately un-normalised — its own README says so. Normalising spacing,
separators and strain-name prefixes collapses 188 strings to 113 codes; resolving
those against the register's P-number column collapses them onto **78 of the 81
batches**. `BG 1024` / `BG1024` / `Blue Gelato BG1024`, and `GG1024_01` /
`GG 1024_01` / `GG1024-01`, are one batch each, not three.

The normalisation is not a convenience: it is the owner's identity rule, recorded
in `README.md` §Batch identity. The separator before a sub-lot index carries no
meaning, but the index itself does, and it nests — `GG1024_01/01` is sub-lot 01 of
batch `GG1024_01`, a distinct record from its parent. Collapsing one level and
stopping would have merged parent into child. Under the full rule all 81 batches
key distinctly, which is what makes the 78-of-81 match meaningful rather than an
artifact of loose matching.

The residue is small and informative:

| Code | Reading |
|---|---|
| `PO50022`, `PO50202`, `GPO824-02` | letter O read for a zero — OCR, not a batch |
| `J311122501` | a doubled digit against `J31122501` |
| `MB0824_01` on ППК25118 | a well-formed sub-lot code, not an OCR artifact — see below |

**"262 certificates" versus 284.** Different denominators, both correct:

| Count | Value |
|---|---:|
| Register rows carrying a CoA code | 284 |
| Distinct CoA codes in the register | 250 |
| Distinct certificates found in the files | 262 (understated — see below) |

34 codes appear against more than one batch row, which is why 284 rows carry 250
codes. The workbook's scope also excludes `WATER_TESTING` entirely.

## What the shared workbook found that this analysis missed

### 1. Conformity was never checked here — and roughly ten certificates fail

This analysis asked only whether a panel had been *tested*. It never asked whether
the reported value *passes*. The shared workbook did, and found a recurring
pattern in the IPH microbiology reports:

> TYMC result 4,2 × 10⁴ CFU/g exceeds the stated specification of 10⁴ CFU/g,
> yet the conclusion states ОДГОВАРА

At least ten IPH certificates carry a microbiological count above the printed
limit while still concluding ОДГОВАРА, among them `320/0587/25` (GG1024-01),
`472/0863/25` (GG1024-02), `948/1686/25` (HPA052501), `1032/1851/25` (CJ062501/2),
`587/1066/25`, `904/1589/25`, `946/1684/25`, `949/1687/25`, `628/1129/25` and
`1220/2171/25`. Two CNP certificates (ППК26033 on P050022, ППК26058 on P050202)
carry a CBN assay out of specification, and the in-house CoA for P050202 an
out-of-specification total Δ9-THC.

This is a different class of problem from the coverage gap and it is more urgent:
a batch with no test can still be tested, but a batch released against a failing
result already left the building. **Each of these needs a deviation record.**

Caveat on that sheet: the `Finding category` column is over-assigned — remarks
reading "none missing" are tagged `missing page`, and signature-legibility notes
are tagged `out of specification`. The free-text descriptions are reliable; the
category labels are not. Of the 48 rows tagged out-of-specification, the
descriptions support roughly 15.

### 2. ППК25118 prints a batch its filename contradicts

The certificate is filed as `MB0824_04 (P050032) 3.pdf` and the page reads
`MB0824_01`. This analysis flagged the same certificate as an OCR artifact and read
it as `MB0824_04`; the independent transcription read `MB0824_01`.

Under the batch-identity rule this is no longer safely dismissable as a misread.
`MB0824_01` is a **well-formed sub-lot code** — the register carries `MB0824_04`
and `MB0824_05`, so sub-lots 01 to 03 of the same parent may well have existed and
never been registered. The certificate has to be looked at: either it is misfiled
under the wrong sub-lot, or an unregistered sub-lot is on record. `GRC102501` is in
the same position, registered at sub-lot 2 with no `/1`.

### 3. FB012601/1 is confirmed as printed, not as a parsing artifact

ППК26067 prints `FB012601/1` while being filed in a folder named `FB012601`, and
the register carries `FB012601` without the `/1`. Two independent readings now
agree the certificate itself says `/1`.

The batch-identity rule since supplied by the owner closes most of the remaining
question: `/1` is a genuine sub-lot index, not decoration, and FB012601 is a 2026
batch — a vintage where the register lists sub-lots and never the parent (9
families out of 9). So #53 reading a bare `FB012601` is the anomaly. Either the row
should read `FB012601/1`, or a sub-lot exists that was never registered. The edit
is a QC decision; the fact is no longer in doubt.

### 4. The scanning stock is materially worse than the register suggests

150 of the 340 files are byte-identical redundant copies, and 140 certificates sit
inside multi-certificate bundles — up to three certificates from two laboratories
in one PDF, with pages out of reading order. One certificate is incomplete
(`1625/2026`, J31122501: 3 of 4 declared pages present). This is the concrete
version of the group-scan risk raised earlier: a filename-keyed pipeline cannot
see any of it.

## What this analysis has that the shared workbook does not

**The register.** Its own limitations section states the position plainly:

> NO BATCH MASTER LIST WAS AVAILABLE. […] Sheet 7_Batch_Index is therefore built
> from the batch codes PRINTED ON THE CERTIFICATES, not from an authoritative
> batch list. Gaps (a batch with no CoA) CANNOT be identified until that list is
> supplied.

Every issuance number depends on that list. Without it there is no denominator, so
no CoQ count, no iCoA count, and no way to see a batch that has no certificate at
all. The two artifacts are complementary rather than competing: this analysis
supplies the denominator, the shared workbook supplies verified numerators.

## A defect in the shared workbook: nine certificates were merged away

Sheet `1_Certificate_Register` carries one row, `PURELYPLANT|None`, whose
"No. of physical copies on disk" reads 13 and whose source-file list names
thirteen different files. Its own remark explains why:

> MANIFEST MISMATCH: manifest cid is 'PURELYPLANT_None' with doc_no null

Those thirteen files are **not** copies. Sheet `6_Source_File_Index` gives each its
own SHA-256:

| File | KB | SHA-256 (16) | Batch |
|---|---:|---|---|
| `ImB_COAs/BG1024_CoA.pdf` | 379.7 | `706eff3d6d097cef` | BG1024 |
| `ImB_COAs/BSS1024_CoA.pdf` | 378.9 | `44981a8c93cb746e` | BSS1024 |
| `ImB_COAs/CJ1024_CoA.pdf` | 345.4 | `fd60f3f7602b50e3` | CJ1024 |
| `ImB_COAs/GG1024.pdf` | 629.9 | `8029082e7b163c6c` | GG1024 |
| `ImB_COAs/GP0824_02_bulk_CoA.pdf` | 349.7 | `705eaa07cd6fa8ea` | GP0824_02 |
| `ImB_COAs/HPA1024.pdf` | 622.9 | `943fa82639c67cb1` | HPA1024 |
| `ImB_COAs/OPM1024.pdf` | 631.9 | `52322669f9f39348` | OPM1024 |
| `ImB_COAs/P050042.pdf` | 349.3 | `8264d5a7f7791e67` | OPM1024_01 |
| `ImB_COAs/P050052.pdf` | 337.8 | `d88a6ad552ad3e5d` | HPA1024_01 |
| `ImB_COAs/P050212.pdf` | 7806.1 | `429e3ee4f57a6459` | CJ062501-2 |

Ten distinct documents (the other three files are `ImB_QC_COAs` mirrors of three of
them), of which only the P050212 one was transcribed. Every one maps cleanly onto
a batch in the register.

Consequences:

- distinct certificates is **≥ 271**, not 262;
- in-house Purely Plant release CoAs number **41**, not 32 — 44 files carrying a
  `PURELYPLANT` record, 41 distinct by SHA-256;
- nine batches are absent from `7_Batch_Index` as in-house-CoA holders when they
  do hold one.

**`GG1024.pdf` is therefore confirmed, not refuted.** It is a distinct two-page
document with its own hash, held in two locations, exactly as reported in
`README.md` §GG1024. The independent build did not fail to find it — it merged it
into a neighbouring record.

The batch-identity rule then confirms it a second way, structurally. Of the four
2024-vintage families, `BSS1024`, `HPA1024` and `OPM1024` each carry a parent row
in the register *and* a parent-level in-house release CoA in this very bucket —
`BSS1024_CoA.pdf`, `HPA1024.pdf`, `OPM1024.pdf`. `GG1024` has the CoA and not the
row, and is the only 2024 family in that position. From 2025 on the convention
changes and no parent is registered at all, so the omission is confined to one
vintage and one batch. The register still has no row for GG1024, and that remains
the finding.

## The one place the shared workbook changes a number here

Forty-one in-house Purely Plant release CoAs exist on form `QCCoA 001v02`, and
every one of them carries, verbatim:

| Parameter | Acceptance criterion | Method |
|---|---|---|
| Appearance | Dark green to pale yellow or light brown to reddish-brown female inflorescence, with characteristic aromatic odour | Visual |
| Identification** | The retention time of each cannabinoid of the test solution corresponds to its of the standard solution | DAB |
| Foreign matter | < 2.0 % | Ph. Eur. 2.8.2 |

Read against the parameter model in `README.md` — where appearance **is**
Identification A — these documents already carry Identification A and foreign
matter for the batches that hold them. They do **not** carry Identification B:
there is no microscopy on the form, and the identification is chromatographic.

Of the 69 batches placed in the full internal-CoA panel, **32 hold one of these
CoAs** (41 less the nine merged records and the batches outside that scope), and
**37 hold nothing at all**. That splits the 69 into two genuinely different
situations, and it is a QC decision, not an arithmetic one:

| If the QCCoA 001v02 record… | Full panel | Ident B only | Ident C only |
|---|---:|---:|---:|
| does not discharge anything (current basis) | 69 | 0 | 12 |
| discharges Identification A + foreign matter | 37 | 32 | 12 |

The second reading is only available if those CoAs are current records rather than
the superseded in-house CoAs already excluded from the certificate counts. That
is the QC Manager's call. Nothing in this document assumes it; the headline
figures in `README.md` remain on the first basis until it is decided.

## Method note

The comparison was made by normalising the shared workbook's as-printed batch
strings and resolving them against the register's batch and P-number columns; the
scripts are throwaway and are not committed. No file in either workbook was
modified. The shared build states it used Tesseract at 300 dpi for page
classification — that is outside the reading chain used in this repository
(`kimi-k2.6` → `moonshot-v1-128k-vision-preview` → `gpt-4o`), and is recorded here
only because it is a difference in method, not a defect: its transcription was
done from rendered page images, not from Tesseract output.
