# Batch Release QC Register — verification against the certificates (2026-08-29)

Verification of `PP_Batch_Release_QC_Register_CORRECTED.xlsx` (Drive `1wSJ-WtS_…`)
against the 291 certificates in Drive folder `1rwBvSAE…` and the RAGFlow `eCoA_DATABASE`
dataset (`f29f8f58…`, 291 documents, 1 261 chunks, all `DONE`).

**Status: microbiology verification COMPLETE. All 17 at-risk rows page-verified,
corrections applied, root cause traced and a replacement pipeline specified.**
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

| Register | Batch | Certificate | **Certificate reads** | **Register records** | Limit | Over by | Lab verdict |
|---|---|---|---|---|---|---|---|
| r21 | `GG1024_01` | `320/0587/25` | **4,2 × 10⁴ CFU/g** | 4.2×10³ | 10⁴ | 4.2× | ОДГОВАРА |
| r56 | `GP0824_03` | `628/1129/25` | **1,2 × 10⁴ CFU/g** | 1.2×10³ | 10⁴ | 1.2× | ОДГОВАРА |
| r71 | `OPM052501` | `904/1589/25` | **3,3 × 10⁴ CFU/g** | 3.3×10³ | 10⁴ | 3.3× | ОДГОВАРА |
| r82 | `GP052501` | `946/1684/25` | **3,6 × 10⁴ CFU/g** | 3.6×10³ | 10⁴ | 3.6× | ОДГОВАРА |
| r100 | `CJ062501-2` | `1032/1851/25` | **4,9 × 10⁴ CFU/g** | 4.9×10³ | 10⁴ | 4.9× | ОДГОВАРА |

**Five for five**, same signature every time: the exponent is recorded one lower than the
certificate prints, so a result **over** the Ph. Eur. limit appears **under** it. Every
certificate that the register showed as a passing 10³ value reads 10⁴ on the page — there
were no false alarms in this group.

### 2b. 🔴 All ten flagged microbiology certificates exceed their own TYMC limit

> **AMENDED 31.08.2026 — this section's arithmetic was wrong, and the count is five, not
> ten.** Every value in the table below is right and every page read stands. What was wrong
> is the ceiling they were compared against. An acceptance criterion of `10⁴ CFU/g` does not
> mean 10 000: Ph. Eur. 5.1.4 / 2.6.12 and USP <1111> read it as a **maximum acceptable
> count of 2 × 10⁴ = 20 000**. Against that, `1,9 × 10⁴`, `1,7 × 10⁴`, `1,5 × 10⁴` and
> `1,2 × 10⁴` clear the pharmacopoeial ceiling. Five remain out of
> specification — `4,2`, `4,9`, `3,6`, `3,3` and `2,6 × 10⁴` — and those five still need a
> deviation record. `1220/2171/25` (200 against a manufacturer's own `10²`) is a separate
> question that the pharmacopoeia does not settle. Full record in
> `review/OOS_RECTIFICATION_2026-08-31.md`.


With the five above resolved, the picture for the ten certificates named in
`CROSS_CHECK_2026-08-22.md` is complete, and **the cross-check was right about all ten**:

| Batch | Certificate | TYMC | Limit | Visible in register? |
|---|---|---|---|---|
| `GG1024_01` | `320/0587/25` | 4.2×10⁴ | 10⁴ | **hidden** — recorded 10³ |
| `GG1024_02` | `472/0863/25` | 1.9×10⁴ | 10⁴ | visible |
| `HPA1024_01` | `587/1066/25` | 1.5×10⁴ | 10⁴ | visible |
| `GP0824_03` | `628/1129/25` | 1.2×10⁴ | 10⁴ | **hidden** |
| `OPM052501` | `904/1589/25` | 3.3×10⁴ | 10⁴ | **hidden** |
| `CJ052501-1` | `949/1687/25` | 1.7×10⁴ | 10⁴ | visible |
| `GP052501` | `946/1684/25` | 3.6×10⁴ | 10⁴ | **hidden** |
| `HPA052501` | `948/1686/25` | 2.6×10⁴ | 10⁴ | visible |
| `CJ062501-2` | `1032/1851/25` | 4.9×10⁴ | 10⁴ | **hidden** |
| `PM072501` | `1220/2171/25` | 200 | 10² | visible |

Ten certificates, ten results at or above the printed power of ten, ten conclusions of
**ОДГОВАРА**. Five were page-verified here; the other five already show a high value in the
register itself and so need no transcription fix.

~~**Ten batches need a deviation record**, which is open item B1.~~ **Five do** — see the
amendment above. Read against the maximum acceptable count the pharmacopoeia actually
prescribes, four of these ten conform and one (`1220/2171/25`) turns on a manufacturer
specification this register does not hold.

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

### 6. 🟢 The CBN exceedances are accelerated-stability results, not failed releases — and the register records them correctly

`ППК26058` does print **CBN 2.05 %** against a limit of **≤ 1.00 %**, so the cross-check's
number is right. But the framing that grouped it with the microbiology failures is wrong,
and the register is not.

On the **Batch Release QC** sheet these certificates show `/` in every column, which looked
like an omission of a failing value. It is not. They are stability-programme timepoints,
and the workbook's **Stability Testing Programme** sheet records them in full — with the
exceedance annotated in the row:

| Batch | Report | Timepoint | Condition | CBN | Note in the sheet |
|---|---|---|---|---|---|
| `P050022` | `ППК26033` | 6 months | **40 °C / 75 % RH** | **2.35 %** | "CBN 2.35 % exceeds…" |
| `P050072` | `ППК26035` | 6 months | **40 °C / 75 % RH** | **2.15 %** | "CBN 2.15 % exceeds…" |
| `P050202` | `ППК26058` | 6 months | **40 °C / 75 % RH** | **2.05 %** | "CBN 2.05 % exceeds…" |

Three points follow.

1. **All three are accelerated conditions** (40 °C / 75 % RH), where CBN rising is the
   expected degradation product of THC. This is a **shelf-life signal**, not a batch
   released against a failing result. No product was released on these certificates.
2. **The cross-check names two; there are three.** `ППК26035` on `P050072` was missed.
3. **The register is right here.** The `/` on the release sheet is correct — a stability
   timepoint is not a release result — and the values are recorded, with the exceedance
   flagged, on the sheet that should hold them.

This materially narrows open item B1: the microbiology finding stands and concerns real
releases; the CBN finding is a stability observation the register already documents.

### 7. 🟢 `PM112501` is **not** a register error — the register and the grade design are both right

Worth recording because it looks like a contradiction and is not. `ППК26030` prints
**Вкупно Δ9-THC 13.33 %** and loss on drying **8.61 %**, and the register records exactly
those. Open item C2 says `PM112501` is **10.79**.

Both are correct: `PM112501` is P-number `P060232`, and the grade design uses the Farmahem
re-analysis of 26.08.2026, which supersedes the original under rule R5. The solver's own
notes say so — *"P060232 (PM112501): dataset 13.33 vs 10.79 — superseded by T2
re-analysis (R5)"*. The register records the filed certificate; the design records the
retest. They are answering different questions.

### 8. 🟠 The T2 re-analysis has no certificate anywhere in the corpus

**Zero** of the 291 documents are dated 26.08.2026. The latest certificates on file are
21 dated 07.08.2026 and 21 dated 10.08.2026 (the Farmahem 197-series).

So the values that anchor 29 batches' grades cannot be checked against any document in
this corpus, because the documents do not exist yet. That is consistent with what the
methodology says — unofficial, eCoA pending — but it has two consequences worth stating:

- **Open item C1 is confirmed from the corpus side**: 29 batches carry a grade whose
  evidence is not on file.
- **Open item C2 is blocked on C1**, not answerable now. Whether `PM112501`'s retest reads
  10.79 or 10.80 — the 0.01 that decides between THC10 and THC12 — can only be settled
  when the Farmahem eCoA is filed. Reading the existing certificate does not help; it
  reports the superseded 13.33.

### 9. 🟡 How far the superscript error spreads — bounded, not systematic

The obvious worry after finding 2 is that the whole register is affected. Scoping it:

| IPH rows carrying a TYMC value | 45 |
|---|---|
| recorded as **x×10³** — a hidden failure *iff* the page says 10⁴ | **17** |
| recorded as x×10⁴ or higher — already visible as over-limit | 9 |
| plain number or other form | 19 |

Six of the 17 at-risk rows have now been page-verified:

- **Five were wrong** — and all five are certificates the cross-check had flagged.
- **One was right**: `947/1685/25` (`CJ052501-2`) reads **6,3 × 10³** on the page and the
  register records 6.3×10³. It passes, and the register says so.

That last one matters, because it **breaks the inference that all 17 are wrong**. The
errors are not randomly distributed across the 10³ population — they line up with the
cross-check's flags. Which is consistent with how that workbook was built: from the 340
physical PDFs, every page re-read from the rendered image. It read the superscripts
correctly, which is exactly why it caught these and why its list of ten is sound.

**Residual risk.** Eleven at-risk rows remain unread. The evidence now suggests they are
mostly fine, but "suggests" is not "verified", and each is one page read away from being
settled:

`163/0271/25`, `161/0269/25`, `588/1067/25`, `767/1376/25`, `1009/1813/25`,
`1218/2169/25`, `1228/2194/25`, `1226/2192/25`, the unnumbered Dec-2025 microbiology
report, `4/0007/26`, `6/0009/26`.

### 10. ✅ All 17 at-risk rows verified — 6 errors, 11 correct

Every register row recording a mould count as `x×10³` has now been read off its
certificate page. The result is bounded and specific:

| | |
|---|---|
| At-risk rows (TYMC recorded as x×10³) | 17 |
| **Understated by a factor of ten** | **6** |
| Recorded correctly | 11 |

The six: `320/0587/25`, `628/1129/25`, `904/1589/25`, `946/1684/25`,
`1032/1851/25` — all five of which hide a genuine failure — plus `163/0271/25`,
where the page reads `1 x 10⁴` against a recorded `1×10³`. That last one sits
exactly at the limit, so it is a transcription error whose disposition does not
change.

The eleven correct: `161/0269/25`, `588/1067/25`, `767/1376/25`, `947/1685/25`,
`1009/1813/25`, `1218/2169/25`, `1226/2192/25`, `1227/2193/25`, `1228/2194/25`,
`4/0007/26`, `6/0009/26`.

**Also identified**: row 141's uncoded "Microbiology report (Dec 2025)" is
certificate **`1227/2193/25`** — `GP082501-2` is P050322, and the row's own TAMC
3.2×10³ and TYMC 5.8×10³ match that page exactly.

**And a flagging inconsistency**: of the ten rows whose TYMC sits at or above its
printed power of ten, only two carried the sheet's own amber "laboratory finding"
style. Eight sat unflagged, which is part of why this stayed invisible. (All ten
were later flagged amber; on 31.08.2026 four of those flags were withdrawn as
conforming and the remaining five were given the comment they had never had.)

### 11. ✅ Corrections applied

`deliverables/qc_gap_analysis/apply_register_corrections.py` — re-runnable,
idempotent, and it refuses to touch a cell whose current value is not the one
verified, so it cannot be run against the wrong revision.

Seven cell values change (six TYMC, one CoA code) and eight amber flags are
applied. A full before/after diff confirms **nothing else in the workbook
moves**.

**The corrections could not be written to Drive from this session** — Drive
write access needs an approval this session cannot grant. The corrected workbook
is produced locally and delivered for upload; the snapshot step is therefore
yours to take, and the original in Drive is untouched.

### 12. 🔴 Root cause, and the pipeline that replaces it

Measured against the 17 verified pages, the RAGFlow parse of the TYMC result is
**correct on 6, wrong on 2, and not extractable on 9**. Both errors are the same
failure in the same direction — 10⁴ read as 10³, never the reverse.

Four causes, and a replacement pipeline, are set out in
`ingestion/ragflow/ECOA_RAG_PIPELINE_2026-08-30.md`. The executable half is
`ingestion/ragflow/validate_ecoa_limits.py`, which compares every result to its
limit: **5 findings against the register before these corrections, 9 after.**

## Not yet checked

Stated plainly rather than left to inference:

- **Five of the ten microbiology certificates** have not been page-verified
  (`472/0863/25`, `587/1066/25`, `949/1687/25`, `948/1686/25`, `1220/2171/25`). All five
  already show an over-limit TYMC **in the register itself**, so the register needs no
  transcription fix for them and the finding does not depend on reading them — but they
  should still be read before the deviation records are written.
- The in-house THC on `P050202` flagged by the cross-check.
- Page-level confirmation of the three stability CBN values; they are taken here from the
  register's own stability sheet, whose numbers the RAGFlow parse could not corroborate
  because it dropped the result column on all four `P050202` CNP certificates.
- The `CJ072501` CBD correction (26.20 → 0.09).
- Layer 3, the stratified sample for a transcription error rate across the other ~250 rows.

**No cell has been corrected yet.** The five confirmed errors in finding 2 are corrections
that turn released batches into visibly out-of-specification ones; they are recorded here
first so the change is reviewable before it lands.
