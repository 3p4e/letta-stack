# Every microbiology certificate, read off its own page

**Scope:** all 40 IJZ-MB microbiological purity certificates reachable from the release
register, verified against the rendered page at 300 DPI. Not against the RAG corpus, not
against a text layer — against the paper.

**Why the page and nothing else.** Google Drive's text extraction strips every exponent
from these documents. The same certificate that prints `4,2 x 10⁴ CFU/g` extracts as
`4,2 x 10 CFU/g`, in the result *and* in the specification. `pdftotext` finds nothing at
all: these are pure scans with no text layer. A single superscript decides pass or fail
here, so the render is the only admissible source.

## Result

| | |
|---|---|
| Certificates read | **40 of 40** |
| Register fields compared | 146 |
| Agreement | **136 — 93.2%** |
| Substantive differences | **10** |
| Cosmetic differences | 28 (the register glosses `Одговара` as `Одговара (absent)`) |

The register is accurate on the great majority of what it records. The ten exceptions
below are real, and two of them are the kind that a column-based check cannot see.

---

## A. Substantive differences, register against page

### A1 · Row 26 — the wrong certificate, and a lost decade

**Two microbiology certificates exist for `GP0824-01`, both received 08.04.2025:**

| | TAMC | TYMC |
|---|---|---|
| `318/0585/25` | **4,2 × 10³** | **6 × 10³** |
| `319/0586/25` | 5,2 × 10³ | 8,8 × 10³ |
| **Register row 26**, coded `319/0586/25` | 4.2×10³ | 6×10² |

The register's TAMC matches `318` exactly. So the row is not simply wrong against `319`
— it is **carrying `318`'s results under `319`'s code**, and `318`'s TYMC has lost a
decade on the way in (6×10³ recorded as 6×10²).

Two fixes are needed and they are separate: correct the code to `318/0585/25`, and correct
the TYMC to `6 × 10³`. Both values then agree with the paper. Whether `319/0586/25` also
deserves a row of its own is a question for QC — it is a real certificate for a real batch
and the register does not currently reflect it anywhere.

### A2 · Bile-tolerant Gram-negative bacteria — four rows

| Row | Batch | Certificate | Register | **Page** |
|---|---|---|---|---|
| 92 | GP062501 | `1009/1813/25` | `<10^1 and >10^1` | **`< 10³ и >10²`** |
| 142 | GP082501-2 | `1227/2193/25` | `< 10 and > 10^3` | **`< 10⁴ и > 10³`** |
| 156 | CJ082501-2 | `4/0007/26` | `< 10^2 and > 10` | **`< 10`** |
| 88 | HPA052501 | `948/1686/25` | `<10¹` | **`< 10`** |

Rows 92 and 142 are not merely wrong, they are **impossible as written**: nothing is both
under and over 10¹, and nothing is both under 10 and over 10³. A value that cannot be true
should never have survived data entry, and a range check at ingest would have caught both.

Row 156 records a bracket where the certificate reports a plain `< 10`.

### A3 · *E. coli* recorded as a count — four rows

Rows **148, 156, 171, 177** record E. coli as `< 10`. Every certificate reports it as
`Одговара` against a specification of `отсутна/g` — **absent in 1 g**, a presence/absence
determination, not an enumeration. `< 10 CFU/g` is not a result this test can produce.

Not a safety finding — the batches complied — but the register states something the
laboratory did not, in a column that a reviewer would read as a measurement.

---

## B. Findings the register cannot express

These are not transcription errors. They are gaps in what the register is able to record.

### B1 · A genuine exceedance invisible to a column check · `1220/2171/25`, row 122

```
Барање/Метода: Ph.Eur. 5.1.8 – Kat. C и производителска спецификација

Вкупен број аеробни бактерии-ТАМС    - 10⁴ CFU/g     110 CFU/g
Вкупен број габи и мувли-ТУМС        - 10² CFU/g     200 CFU/g     ← 2× over
На жолчка толерантни грам-негативни  - ≤ 10² CFU/g   < 10 CFU/g
```

**TYMC 200 against a printed limit of 100.** The register's column limit is 10⁴, so this
result *passes the column and fails the paper*. `validate_ecoa_limits.py` compares against
the column and states this limitation in its own docstring; here is the case, confirmed.

The certificate concludes ОДГОВАРА.

### B2 · Two certificates run a tighter manufacturer specification

`1220/2171/25` and `1221/2172/25` cite `производителска спецификација` alongside
Ph. Eur. 5.1.8:

| | Ph. Eur. Cat. C | These certificates |
|---|---|---|
| TAMC | 10⁵ | **10⁴** |
| TYMC | 10⁴ | **10²** |
| GNB | ≤ 10⁴ | **≤ 10²** |

A per-certificate limit is not a refinement here. It is the difference between a pass and
a deviation, and only the certificate carries it.

### B3 · Two parameters with nowhere to go

The same two certificates test ***Staphylococcus aureus*** and ***Pseudomonas
aeruginosa***, both reported `Одговара`. The register has no column for either, so two
tested parameters are not recorded anywhere.

### B4 · Two certificates absent from the register

`318/0585/25` (see A1) and `305/0549/26` (SCR112501) were read but match no register row.
`305/0549/26` also uses a newer conclusion wording — `Резултатите ... СЕ ВО СОГЛАСНОСТ`
rather than `ОДГОВАРА`, and reports E. coli as `отсутна/g` rather than `Одговара`. Any
parser keyed on the old wording will miss it.

---

## C. TYMC at or above its own printed power of ten — all ten, confirmed on the page

> **AMENDED 31.08.2026 — the "Over by" column below compares against the wrong number.**
> Every result and every page read here stands; the ratios do not. An enumeration criterion
> of `10⁴ CFU/g` means a **maximum acceptable count of 2 × 10⁴ = 20 000** (Ph. Eur. 5.1.4 /
> 2.6.12, USP <1111>), so the ratios that matter are 2.45×, 2.10×, 1.80×, 1.65× and 1.30×
> for the first five — and the last four (`472/0863/25`, `949/1687/25`, `587/1066/25`,
> `628/1129/25`) clear the pharmacopoeial ceiling — though not Purely Plant's own QCSP 001,
> so they are undetermined rather than conforming. `1220/2171/25` at 200 against a manufacturer's own `10²` is a
> question about that specification's wording, not one the pharmacopoeia settles.
> See `review/OOS_RECTIFICATION_2026-08-31.md`.


| Certificate | Batch | Result | Printed limit | Over by |
|---|---|---|---|---|
| `1032/1851/25` | CJ062501/2 | 4,9 × 10⁴ | 10⁴ | 4.9× |
| `320/0587/25` | GG1024-01 | 4,2 × 10⁴ | 10⁴ | 4.2× |
| `946/1684/25` | GP052501 | 3,6 × 10⁴ | 10⁴ | 3.6× |
| `904/1589/25` | OPM052501 | 3,3 × 10⁴ | 10⁴ | 3.3× |
| `948/1686/25` | HPA052501 | 2,6 × 10⁴ | 10⁴ | 2.6× |
| **`1220/2171/25`** | **PM072501** | **200** | **10²** | **2.0×** |
| `472/0863/25` | GG1024-02 | 1,9 × 10⁴ | 10⁴ | 1.9× |
| `949/1687/25` | CJ052501/1 | 1,7 × 10⁴ | 10⁴ | 1.7× |
| `587/1066/25` | HPA1024-01 | 1,5 × 10⁴ | 10⁴ | 1.5× |
| `628/1129/25` | GP0824-03 | 1,2 × 10⁴ | 10⁴ | 1.2× |

Plus `163/0271/25` (BG1024) at exactly 1 × 10⁴ — at the limit, not over it.

**Every one concludes ОДГОВАРА.** That is now established from the paper rather than
inferred from a parse, and it remains a question for the issuing laboratory and for the
deviation records, not something any pipeline can resolve.

These are the same ten the 22.08 cross-check named, and `1220/2171/25` was already among
them with its 10² limit recorded on 29.08 — it is not a new discovery. What is new is
that it had never been read: it was one of the five in that list still marked *not
page-verified*, and all five have now been read. What the page adds is the reason its
limit is 10² — the certificate carries a manufacturer specification of its own, which is
what B2 records.

## D. The six corrections of 30.08.2026, independently confirmed

Each was made from a rendered page during the earlier verification. Each has now been read
again, from the original PDF, by a separate pass:

| Certificate | Batch | Page reads | Correction applied |
|---|---|---|---|
| `163/0271/25` | BG1024 | 1 × 10⁴ | 1×10⁴ ✓ |
| `320/0587/25` | GG1024_01 | 4,2 × 10⁴ | 4.2×10⁴ ✓ |
| `628/1129/25` | GP0824_03 | 1,2 × 10⁴ | 1.2×10⁴ ✓ |
| `904/1589/25` | OPM052501 | 3,3 × 10⁴ | 3.3×10⁴ ✓ |
| `946/1684/25` | GP052501 | 3,6 × 10⁴ | 3.6×10⁴ ✓ |
| `1032/1851/25` | CJ062501-2 | 4,9 × 10⁴ | 4.9×10⁴ ✓ |

All six agree. The corrections were right.

---

## E. What was applied to the register

All ten substantive differences in section A are now in the workbook, applied by
`deliverables/qc_gap_analysis/apply_microbiology_corrections.py` and written to
`PP_Batch_Release_QC_Register_MICRO_2026-08-31.xlsx`. The script is idempotent and
refuses to run against a workbook whose cells differ from the values verified here.

| Cell | Was | Now | Certificate |
|---|---|---|---|
| W26 | `319/0586/25` | `318/0585/25` | the row's TAMC matches 318 |
| K26 | `6×10²` | `6×10³` | `318/0585/25` |
| Z26 | link to 319 | link to 318 | follows the code |
| L88 | `<10¹` | `< 10` | `948/1686/25` |
| L92 | `<10^1 and >10^1` | `< 10^3 and > 10^2` | `1009/1813/25` |
| L142 | `< 10 and > 10^3` | `< 10^4 and > 10^3` | `1227/2193/25` |
| L156 | `< 10^2 and > 10` | `< 10` | `4/0007/26` |
| N148 · N156 · N171 · N177 | `< 10` | `Odgovara (Absent)` | `3/0006/26`, `4/0007/26`, `6/0009/26`, `10/0013/26` |

**The link moved with the code.** Repointing Z26 is not cosmetic: leaving it would have
produced a live link opening `319`'s certificate from a row labelled `318` — the exact
defect that had to be cleaned off 190 rows earlier this week, and the one that does not
announce itself, because the document it opens is real and its numbers look plausible.

**Two comments instead of two columns.** K122 and K118 now carry the manufacturer
specification their certificates print (TAMC 10⁴, TYMC 10², GNB ≤ 10²) and the two extra
parameters tested (*S. aureus*, *P. aeruginosa*, both `Одговара`). K122's comment states
plainly that its 200 passes the column and fails its own paper. Columns were not added:
two rows out of 291 would leave 289 blanks, and the finding belongs to the certificate,
not to the register's schema.

**Effect on the validator.** `validate_ecoa_limits.py` R1 is unchanged at 9 — row 122's
exceedance is still invisible to it, by construction, because the column says 10⁴. (On
31.08 R1 moved to 5, once the rule stopped reading the criterion with `magnitude()`; four
of the nine conform and four CBN stability timepoints moved to a new rule R3.) R2
moves 24 → 23: row 26's TYMC and row 142's GNB stop being flagged because they are now
correct, and row 92's GNB starts being flagged in the same benign class as rows 75, 138
and 217. The amber flags, the 268 hyperlinks and all 8 merged ranges are byte-identical
before and after; exactly 10 cell values and 1 link target changed.

**Left open, deliberately.** `319/0586/25` is a real certificate for a released batch and
now has no row of its own. Giving it one is an addition rather than a correction, and it
is QC's call — the same call the batch owner made for ППК25139. `305/0549/26` (SCR112501)
is in the same position.

---

## Method

For each certificate: fetch the PDF from Drive, render page 1 at 300 DPI with `pdftoppm`,
crop the band carrying the laboratory number and the results table so the image is
self-identifying, and read it. Classical OCR is not used and is forbidden by
`scripts/policy_check.py` rule 1.

Two practical notes for anyone repeating this:

- **The download need not pass through context.** An oversized tool result is written to
  a file on disk; decoding and rendering it locally costs nothing. That is the difference
  between ~2 000 tokens per certificate and ~80 000, and it is what made forty feasible.
- **Crop to include the laboratory number.** A crop showing only the table cannot be
  checked against the document it came from, and mixing up two certificates is exactly the
  error this exercise exists to catch.

## What is still not verified

This covers microbiology only — 146 of the register's ~1 295 populated result values.
Aflatoxins, ochratoxin A, heavy metals, pesticides and loss on drying have still never
been checked against a document, and neither have the 266 dates of issue.
