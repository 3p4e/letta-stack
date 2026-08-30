# Batch Release QC Register — verification against the certificates (2026-08-29)

Verification of `PP_Batch_Release_QC_Register_CORRECTED.xlsx` (Drive `1wSJ-WtS_…`)
against the 291 certificates in Drive folder `1rwBvSAE…` and the RAGFlow `eCoA_DATABASE`
dataset (`f29f8f58…`, 291 documents, 1 261 chunks, all `DONE`).

**Status: interim. Layer 1 complete; Layer 2 partially complete; Layer 3 not started.**
Every claim below cites the certificate it rests on. What has *not* been checked is listed
at the end rather than left implied.

## Two corrections to earlier statements in this workstream

1. **The Drive workbook is byte-different from the repo copy but cell-identical.**
   76 108 bytes against 73 432, modified 27.08 against 21.08 — but a full cell-by-cell diff
   across all three sheets returns **zero differences**. The delta is formatting/metadata.
   An earlier statement that this was an unverified newer revision was wrong.

2. **RAGFlow's parse of the microbiology certificates is not reliable for exponents**, and
   an earlier reading of this dataset that relied on it was wrong. See finding 2.

## The sources are not independent

The `eCoA_DATABASE` dataset is an ingest of **exactly the Drive folder given**, and its own
description records a verified 1:1 mirror. So RAGFlow is not a second opinion on the
values — it is a parse of the same paper. Only the rendered certificate page settles a
disagreement, and that is what finding 2 turns on.

## Findings

### 1. 🟢 Structural reconciliation is sound

284 certificate rows across 80 batch blocks, 250 distinct CoA codes, against 291
certificates.

| | |
|---|---|
| Rows resolving to a real certificate | **236** |
| Rows whose code matches under a different batch | 3 |
| Rows claiming a code with no certificate found | 8 |
| Rows claiming no code (`n/a`, `(not numbered)`) | 37 |
| Certificates with no linked row | 55 |

Of the 55 unlinked certificates, **52 belong to a batch the register does carry** — they
are additional certificates for a covered batch, not unrecorded results. Only **3** belong
to a batch the register does not carry at all, and they are findings 3 and 4.

The 8 unmatched codes are not missing certificates: four are OCR misreads the register
*itself* flags in the cell (`ППК52211 (likely OCR misread of ППК25211)` — and `ППК25211`
does exist, filed under `P050112`), two are in-house cross-check descriptions rather than
codes, one is the State Phytosanitary code filed under a P-number, one is an unnumbered
December microbiology report.

**Matching required three normalisations that are worth recording**, because a naive
comparison reports hundreds of false failures: certificate codes mix Cyrillic and Latin
homoglyphs (`197-1-К/26` vs `197-1-K-26`); Farmahem writes loss-on-drying as `-LoD-` where
the register writes `ГС`/`GS`; and in-house certificates are `QCCoA 001v02` on disk but
`PP CoA #NNN` in the register.

### 2. 🔴 The register understates TYMC by a factor of ten on at least three batches, converting a failing result into a passing one

This is the most serious finding and it is confirmed from the rendered certificate pages,
not from any text layer.

| Register | Batch | Certificate | **Certificate reads** | **Register records** | Limit | Lab verdict |
|---|---|---|---|---|---|---|
| r21 | `GG1024_01` | `320/0587/25` | **4,2 × 10⁴ CFU/g** | 4.2×10³ | 10⁴ | ОДГОВАРА |
| r56 | `GP0824_03` | `628/1129/25` | **1,2 × 10⁴ CFU/g** | 1.2×10³ | 10⁴ | ОДГОВАРА |
| r82 | `GP052501` | `946/1684/25` | **3,6 × 10⁴ CFU/g** | 3.6×10³ | 10⁴ | ОДГОВАРА |

Three for three, same signature: the exponent is recorded one lower than the certificate
prints, so a result **over** the Ph. Eur. limit appears **under** it.

**Root cause, and why it went unnoticed.** The exponent is a superscript, and neither
machine-readable source preserves it correctly:

- **Drive's text extraction drops superscripts entirely** — `320/0587/25` extracts as
  `- 10 CFU/g … 5,1 х 10 CFU/g 4,2 x 10 CFU/g`, with no exponents at all.
- **RAGFlow's parse renders them but gets them wrong** — its chunk for the same
  certificate reads `4,2 х 10³`, matching the register's error rather than the paper.

The register agrees with the RAGFlow parse and disagrees with the paper, which points to
the register having been built from the parse. That makes this a **corpus** defect as much
as a register one: a QC agent querying `eCoA_DATABASE` today would report `GG1024_01` as
within specification.

### 3. 🟠 `FB012601` — the certificates say `/1`, the register does not

All three `FB012601` certificates are filed under `FB012601_1`, and `ППК26067` prints, in
its own body text, **`серија: FB012601/1`**. The register carries the batch as bare
`FB012601` (r224–225).

This settles the question of fact behind open item **B5**. The remaining decision — correct
the register row, or register a genuinely separate sub-lot — is a QC ruling.

### 4. 🟠 `GG1024` — a parent-level release document for a batch with no register row

`GG1024, NO-DOC-CODE (Report of Analysis), 23.04.2025, PP.pdf` prints **`Batch No: GG1024`**.
The register carries `GG1024_01` and `GG1024_02` but no parent row. Confirms open item
**B6** from the certificate side.

### 5. 🟠 Loss-on-drying results attributed across two batches

The register's rows 210–215 place both the cannabinoid and the loss-on-drying certificates
for `100-2` and `100-3` under batch **J31122501**. The certificates disagree with each
other:

- `100-2-K-26` and `100-3-K-26` (cannabinoids) declare **J31122501**, and their THC values
  (19.84, 21.84) match the register exactly — the register is right on THC.
- `100-2-LoD-26` declares **`Joker 31 J31112501 (рачно тримиран цвет)`**, and `100-1` /
  `100-3-LoD-26` likewise declare J31112501.

So the register attributes loss-on-drying results from **J31112501**'s certificates to
batch **J31122501**. Both batches exist in the register. Whether Farmahem mislabelled the
LoD certificates or the register mis-filed them cannot be settled from the paper alone —
this needs a QC ruling, not a silent edit.

## Not yet checked

Stated plainly rather than left to inference:

- **Seven of the ten flagged microbiology certificates** have not been page-verified.
  Five (`472/0863/25`, `587/1066/25`, `949/1687/25`, `948/1686/25`, `1220/2171/25`) already
  show an over-limit TYMC **in the register itself**, so they need no transcription fix —
  but they are genuine releases against a failing result. Two (`1032/1851/25`,
  `904/1589/25`) show a passing value in the register and are **suspect** given the 3-for-3
  understatement rate above.
- The two CNP CBN certificates (`ППК26033`, `ППК26058`) and the in-house THC on `P050202`.
- The 26.08.2026 Farmahem T2 re-analysis rows.
- `PM112501` (open item C2) and the `CJ072501` CBD correction.
- Layer 3, the stratified sample for a transcription error rate across the other ~250 rows.

**No cell has been corrected yet.** The three confirmed errors in finding 2 are corrections
that turn released batches into visibly out-of-specification ones; they are recorded here
first so the change is reviewable before it lands.
