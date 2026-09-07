# What the verification campaign found that a person has to decide

Eight review documents came out of reading 226 certificates against the register. They record
what was corrected — 28 cells changed, 40 filled, 21 links repaired — and, scattered through
them, **everything that was deliberately *not* corrected because the decision is not a
transcription's to make.** This is that list, gathered in one place.

Nothing here is a defect in the register's arithmetic. Every one is a question about what a
number means, what a row is for, or what a laboratory intended.

**Current workbook: `deliverables/qc_gap_analysis/PP_Batch_Release_QC_Register_FHM4_2026-08-31.xlsx`.**

---

## 1 · Decisions that bear on a batch's disposition

### 1.1 One batch failed release and the register cannot show it

`ППК26127`, `FB032601`, 21.07.2026 — the only CNP certificate in the corpus carrying a
ЗАКЛУЧОК, and the only one concluding **НЕ ОДГОВАРА**, *поради утврдено присуство на семе од
канабис*. Foreign matter reads **0.08 % against a maximum of 2.00 %** — twenty-five times
inside the limit — because the operative half of the limit is its parenthetical, *без присуство
на семе*, and it is not a number.

**Every numeric value on that page is in specification.** The register has no foreign-matter
column and no verdict column, so row 260 is indistinguishable from row 262, which passed. The
certificate code is flagged red with the conclusion quoted in the comment; that is a marker,
not a fix.

> **Decide:** whether the register gains a foreign-matter column and a verdict column. Until it
> does, a batch that failed release looks like one that passed to every automated check and to
> any reader who does not open the comment.

*Evidence: `review/CNP_PAGE_VERIFICATION_2026-08-31.md` §B.*

### 1.2 Five TYMC results over their acceptance criterion, every one concluding ОДГОВАРА

Confirmed from the pages, not inferred from a parse: **five** IJZ-MB certificates report a
mould count above the acceptance criterion, from 1.30× to 2.45× over, and all five conclude
that the sample conforms — `320/0587/25` (42 000), `1032/1851/25` (49 000), `946/1684/25`
(36 000), `904/1589/25` (33 000) and `948/1686/25` (26 000), all TYMC.

> **Corrected 31.08.2026.** This item read *"Ten TYMC results … from 1.2× to 4.9× over"*.
> The ten certificates and their counts are right; the ceiling was not. An enumeration
> criterion of `10⁴ CFU/g` means a **maximum acceptable count of 2 × 10⁴ = 20 000**
> (Ph. Eur. 5.1.4 / 2.6.12, USP <1111>), so `472/0863/25` (19 000), `949/1687/25` (17 000),
> `587/1066/25` (15 000) and `628/1129/25` (12 000) conform, and their amber flags have been
> withdrawn. `1220/2171/25` is item 1.4, not this one. Record:
> `review/OOS_RECTIFICATION_2026-08-31.md`.

> **Reopened later the same day.** Those four do not "conform" — they are **undetermined**.
> Purely Plant's own release specification, `QCSP 001 v.03` (all 48 product specifications
> in `deliverables/imb_spec_pdfs/`), prints `TYMC | Ph. Eur. 2.6.12 cat. C | ≤ 10⁴ CFU/g`
> and states **no maximum acceptable count**, and Ph. Eur. 5.1.4's own scope says the ×2
> note does not automatically extend to a manufacturer's specification. Read as written it
> means 10 000, and the four are 1.20× to 1.90× over. Which reading governs is a QA
> determination on that document. See "Reopened" in `review/OOS_RECTIFICATION_2026-08-31.md`.

> **Decide:** deviation records for the five, and a question to IJZ about how a result over a
> printed limit reaches a conforming conclusion. No pipeline can resolve this.

> **Also decide, and this is now the bigger question:** what `QCSP 001 v.03`'s
> `≤ 10⁴ CFU/g` means. Four release results (rows 35, 38, 57, 75) clear the pharmacopoeial
> maximum acceptable count of 20 000 and exceed a literal 10 000. QCSP 001 also labels those
> rows `Ph. Eur. 2.6.12 cat. C` — a chapter that has no categories — while printing Category
> B figures, and the version in force on the June-2025 test date is unestablished (header
> v.01, footer v.03 signed 01.06.2026). Row 35 is inside the pharmacopoeial ceiling by 5 % on
> a two-significant-figure value, so its raw plate count is worth pulling either way.

*Evidence: `review/MICROBIOLOGY_PAGE_VERIFICATION_2026-08-31.md` §C.*

### 1.3 Four stability samples over the CBN limit — is the limit meant to apply to them?

All four Grape Pie samples held at **40 °C / 75 % RH** exceed the `≤ 1.00 %` CBN limit printed
on their own certificates — 1.09, 2.05, 2.15, 2.35 — with Δ9-THCA decarboxylated to near zero
beside them. The matched 25 °C / 60 % RH samples read 0.04 to 0.30 with THCA intact. This is
the study behaving as a stability study should. **None of the four certificates carries a
verdict of any kind.**

Their results were not in the register at all until this week; writing them took the
register's own R1 rule from 9 findings to 13.

**Updated 31.08.2026.** They no longer count as R1 findings at all. R1 is *release* results
above their criterion, and the register's own `Stability Testing Programme` sheet says in its
subtitle that its results "are NOT batch-release results and must not be used as release or
CoA-register values". A new rule **R3** reports them separately, and the published page marks
them *stability timepoint* rather than *over*. Reporting them beside a genuine release failure
said something false about the batch. R1 on the current workbook is **5**, all TYMC.

> **Still to decide, unchanged:** whether an accelerated-condition sample is expected to meet a
> release limit. That belongs in the stability protocol, not in this register. Amber meanwhile,
> and the four cell comments say the certificates carry no verdict of any kind.

*Evidence: `review/CNP_PAGE_VERIFICATION_2026-08-31.md` §A.*

---

## 2 · What belongs in the register

### 2.1 Two certificates have no row

`318/0585/25` and `305/0549/26` (SCR112501) are real certificates for real batches, read off
their pages, and neither is reflected anywhere in the register. `319/0586/25` is in the same
position — row 26 was found carrying **`318`'s results under `319`'s code**, and correcting the
code left `319` with no row.

> **Decide:** whether each gains a row. This is an addition, not a correction — the same call
> the owner already made for ППК25139.

*Evidence: `review/MICROBIOLOGY_PAGE_VERIFICATION_2026-08-31.md` §A1, §B4.*

### 2.2 Copper is measured on nine certificates and recorded nowhere

From `80/2026` onward the IPH metals table adds a **бакар** row: 1,859 to 3,661 mg/kg(l) across
nine certificates, with **no MaxDK printed** — a measured value against no limit. The register
has no copper column. On `87/2026` copper sits under its own **МИНЕРАЛИ** heading and its unit
is printed **`mg/tableta`**, per tablet, on a dried-flower sample.

> **Decide:** whether copper gets a column, and ask IJZ for the limit it is measured against
> and about the unit on `87/2026`.

*Evidence: `review/IPH_PHYSCHEM_PAGE_VERIFICATION_2026-08-31.md` §E.*

### 2.3 The register has no disposition column at all

No release date, no verdict, no status. It records what each certificate says and not what was
decided about the batch. Three separate findings in this campaign — 1.1, 1.2 and the 38
batches at 2.5 — could not be expressed because of it.

> **Decide:** whether a release-decision column belongs here or in a separate record.

### 2.4 Block 37 has three rows for two documents

| Row | Code | Date | Values |
|---|---|---|---|
| 163 | `PP CoA #037 / ППК26005` | 21.01.2026 | 4 |
| 164 | `PP CoA #037` | 20.02.2026 | 0 |
| 165 | `ППК26005` | 21.01.2026 | 0 |

Both documents already have a row of their own, so row 163's combined code cell is redundant,
and its date is `ППК26005`'s while `PP CoA #037`'s own row correctly holds the 20.02.2026 its
file confirms. No value is wrong.

> **Decide:** which row carries the batch's results.

*The other five two-document blocks are consistent and need nothing: the header row is the
in-house CoA with its own date, the row beneath is the CNP report with its own. That resolves
the open item the date pass left — only block 37 remains.*

*Evidence: `review/PDF_LINK_AUDIT_2026-08-31.md`.*

### 2.5 Thirty-eight batches have no microbiology recorded

Of 80 batches, 42 have both microbiology and physico-chemical results and **38 have no
microbiology**. Thirty-seven of those are 2026 batches — the recent end of the register, where
testing still in flight would be — so the shape is consistent with work in progress rather than
work skipped. The register has no way to say which.

**One is not recent.** `OPM1024_01`, row 30, latest certificate **07.05.2025**, fifteen months
old. Its row 32 holds a complete set of microbiological results whose **source document has
never been identified**: the row's code names the physico-chemical report `2156/2025` with an
annotation saying the microbiology sub-report's own laboratory reference could not be read.

> **Decide:** identify the source document behind row 32. That one is worth doing now; the
> other 37 need only confirmation that testing is in flight.

*Evidence: `review/BATCH_TEST_COVERAGE_2026-08-31.md`.*

---

## 3 · Questions for the issuing laboratories

| # | Certificate | Question |
|---|---|---|
| 3.1 | `1625/2026` | Declares conformity to **Ph. Eur. 2.8.18** for an aflatoxin result **it never prints** — the row is blank and both page boundaries were re-rendered uncropped to be sure. It also carries **no МЕТАЛИ section at all**, while its sibling `1628/2026` does. |
| 3.2 | `1628/2026` | Prints serial **`J311122501`**, one digit longer than the `J31122501` on `1625/2026` and on both microbiology reports `230/0393/26` and `231/0394/26`. Three documents against one: **confirmed a typo on `1628/2026`**, and it should be corrected at source. |
| 3.3 | `100-2-ГС/26`, `100-3-ГС/26` | Both print **`J31112501`** where their own cannabinoid twins — same samples, consecutive internal numbers CF-151 to CF-154 — print `J31122501`. **`J31112501` is a real batch** (rows 193–196), so this is not a typo any format check can catch and not one `batch_id.py` can repair: the documents name a different real batch. The likeliest reading is the previous sample's number carried down into two loss-on-drying reports. The register places all four under `J31122501` and is right. |
| 3.4 | `5697/2025` | Mercury MaxDK printed as **`0,01`**, an order of magnitude tighter than the `0,1` on every neighbouring certificate. Result `0,002` complies either way. Real limit or typing slip? |
| 3.5 | `87/2026` | Copper reported in **`mg/tableta`** on a dried-flower sample. |
| 3.6 | `ППК26002`, `ППК26004` | Analysis-completion dates that cannot be right: `16.01.2025`, a year before the sample was delivered, and `16.12.2026`, eleven months after the certificate was issued. Siblings from the same delivery print `16.01.2026`. Neither value is recorded in the register. |
| 3.7 | `100-3-ГС/26` | Bound with its **pages in reverse order** — results on page 1, cover on page 2, the only document in its family like that. Any pipeline assuming "page 1 is the cover" reads the wrong page. |

---

## 4 · Two things the register cannot settle by itself

### 4.1 Rows 89 and 98 — dates that disagree with nothing readable

Row 89 holds `04.10.2025` where its file is named `04.12.2025`; row 98 holds `24.01.2026`
against `21.01.2026`. Both look exactly like the single-digit slips corrected a dozen times
this week.

**The QCCoA form prints no date of issue at all** — certificate number, strain, batch,
manufacturing month, retest month, and nothing else. The pages were rendered; there is nothing
to read. The filename is an independent transcription that corroborated 215 dates in the date
pass, but it is not a document.

> **Needs:** the issuing record. Correcting a release register from a file listing while the
> document is silent is the substitution this campaign exists to catch.

### 4.2 Row 288 — a value that contradicts itself, with no source

Bile-tolerant GNB reads **`<10²>10³`**: below 100 and above 1000 at once. The microbiology pass
met the same construction twice and corrected both, because a certificate said what the
laboratory meant. This row's own code cell reads `n/a — Purely Plant in-house CoA (Batch
OPM1024, no certificate/report)`. Both plausible readings comply with the `≤ 10⁴` limit, so no
disposition turns on it.

> **Needs:** the underlying in-house record.

---

## 5 · Housekeeping, each a one-line change nobody should make unilaterally

| # | | |
|---|---|---|
| 5.1 | **Two spellings of one absence** | `(not numbered)` on 17 rows, `n/a` on 18 — adjacent rows, same meaning. Reports that count by the code cell put the same fact in two buckets. |
| 5.2 | **"284 certificates on file"** | 247 name a document; 37 say one does not exist. Two of those 37 carry 16 result values each — testing that never got a certificate number, which is not the same as nothing. |
| 5.3 | **Three spellings of not-detected** | `N.D.`, `Н.д. (not detected)`, `н.д.` — all faithful to some certificate, all defeating exact-match tooling. |
| 5.4 | **Column limits are single-vintage** | Loss on drying states the 3028 limit of 12.00 % where 61 of 73 CNP certificates apply 10.00 %; the heavy-metal headers state the later of two limit sets, ten times tighter than what 23 of 44 IPH certificates applied. Twice stricter than the paper, once looser. A check against the column is not a check against the certificate. |

---

## 6 · Owner actions carried forward

- **Snapshot the Drive workbook before replacing it** with `..._QCSP_2026-08-31.xlsx`.
- **Rotate the RAGFlow API key.** It is still in this repository's git history at commit
  `83ea904`; **the repository must stay private until it is rotated.**
- **Open the deviation records** for 1.2, and decide on 1.1 and 1.3.

---

## What is not on this list

Everything that was a transcription error is fixed. This week's page-verification passes
changed 28 cells, filled 40 that held `/`, and repaired 21 links; the corrections live in ten
idempotent scripts that refuse a workbook they do not recognise. 1 033 of 1 073 populated
result cells (96.3%) are verified against a document; the remaining 40 sit on four in-house
rows whose own code cells say no certificate exists. 246 of 267 rows open the right document
and none opens the wrong one.

The register is now accurate. What is left is what it cannot express.
