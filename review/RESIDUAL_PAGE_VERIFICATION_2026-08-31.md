# Closing the campaign: the last six certificates, and what is left

The four family passes — microbiology, IPH physico-chemical, Farmahem, CNP potency — each
ended with an estimate of coverage carried forward by addition: 146, then 403, then 571, then
797, then ~993. This pass replaces the estimate with a count, and then closes what the count
found.

## Counting instead of estimating

`deliverables/qc_gap_analysis/verification_coverage.py` folds every row's CoA code through the
same homoglyph rule used everywhere else in this repository and looks for it among the
certificates whose pages were actually read, recorded in `review/*_page_reads_*.json`. The unit
is the populated result cell; `/` and `n/a` are not results and are counted neither way.

**The counted figure was 91.6%, not the ~77% the running estimate had reached.** The estimate
was too pessimistic, because it added families and never noticed that a certificate read for
one parameter had been read for all of them.

What the count left was small enough to finish: **90 cells over 16 rows.**

| | Rows | Cells | |
|---|---|---|---|
| `PP CoA #nnn / ППКnnnnn` | 6 | 24 | already verified — the fold could not see it |
| IJZ-MB microbiology | 5 | 25 | genuinely unread |
| State Phytosanitary | 1 | 1 | genuinely unread |
| Purely Plant in-house | 4 | 40 | no external document exists |

### The 24 that were already verified

Six rows name **two** documents in one cell — `PP CoA #018 / ППК25378` — so the folded code
matched no certificate and the rows counted as unverified. Their values had in fact been read,
and comparing them against the CNP readings gives **18 of 18 agreeing**.

The pairing turns out to be deliberate, and it settles a question left open by the date pass.
Every one of the six sits directly above a bare `ППКnnnnn` row:

| Row | Code cell | Date | Values |
|---|---|---|---|
| 127 | `PP CoA #018 / ППК25378` | 21.01.2026 | 4 |
| 128 | `ППК25378` | 12.12.2025 | 0 |

The upper row is the **in-house CoA**, dated when it was issued, carrying the numbers it
transcribed. The lower row is the **CNP report those numbers came from**, dated when *it* was
issued, carrying none of its own. So the `21.01.2026` that `apply_date_corrections.py`
deliberately declined to touch is correct, and so is the `12.12.2025` on the row beneath it.
Two documents, two rows, two dates, all right.

> **Correction (later the same day).** This section first said the pattern "holds on all six
> pairs". It holds on five. Block 37 has **three** rows — r163 `PP CoA #037 / ППК26005`
> (21.01.2026), r164 `PP CoA #037` (20.02.2026), r165 `ППК26005` (21.01.2026) — so both
> documents already have a row of their own and the combined cell on r163 is redundant, while
> its date is `ППК26005`'s. Nothing there is a wrong value, and `PP CoA #037`'s own row carries
> the 20.02.2026 its file confirms. See `review/PDF_LINK_AUDIT_2026-08-31.md`.

`verification_coverage.py` now tries the whole cell first and then any embedded control-book
number, so a two-document cell is credited to the certificate it names. That took the counted
figure to **96.3%**.

---

## The five microbiology reports · 25 of 25 agree

`627/1128/25`, `766/1375/25`, `229/0392/26`, `230/0393/26`, `231/0394/26` — all IJZ-MB, all
missed by the first sweep. Nothing needed correcting. Every apparent difference is the register
glossing the page more fully: `Одговара (absent)` for `Одговара`, `< 10^3 and > 10^2` for
`< 10³ и >10²`, `2×10²` for `2 x 10²`. All five hold the issue date, not the receipt date, in
the Date of issue column — which is what the two IPH date corrections established should be
there.

### `J311122501` is confirmed a typo

The IPH pass found two certificates for one Jokerz 31 batch printing serials one digit apart —
`1625/2026` with `J31122501`, `1628/2026` with `J311122501` — and could not say which was
right without more evidence.

`230/0393/26` (trimmed) and `231/0394/26` (hand-trimmed) are the microbiology reports for the
same two samples, sampled the same day, and **both print `J31122501`**. Two laboratories and
three certificates against one. The register's `J31122501` is right, and `1628/2026` carries
the error.

### The IJZ-MB notation changed in 2026, and it breaks the obvious parser

| Report | Form | TAMC as printed |
|---|---|---|
| `627/1128/25`, `766/1375/25` | ОБ 7.8.3 216 Верзија 2 | `< 10 CFU/g`, `2 x 10² CFU/g` |
| `229/0392/26`, `230/0393/26`, `231/0394/26` | ОБ 7.8.3 216 **Верзија 3** | `120 CFU/g`, `1900 CFU/g`, `850 CFU/g` |

The 2026 reports print plain integers where every 2025 report prints a coefficient times a
power of ten. A parser that reads counts by matching `\d[,.]?\d*\s*[xх×]\s*10[⁰-⁹^]` — which is
exactly what the superscript problem forced everyone to write — returns **nothing at all** on
the newer form. Not a wrong value: an absent one, which is the failure mode that hides.

The 2026 reports also changed their verdict wording from `примерокот ОДГОВАРА` to
`Резултатите ... СЕ ВО СОГЛАСНОСТ`, and grew a `Напомена` and an impartiality declaration. The
IPH pass found the same wording change on `305/0549/26`. **Both the value format and the
verdict format changed at the same laboratory in the same period, and a parser keyed on either
reads the newer certificates as empty.**

---

## The phytosanitary report · one correction, row 109

`10802_2845/2`, State Phytosanitary Laboratory, 17.11.2025.

| | |
|---|---|
| Register held | `Not found any pesticide above LOQ (≤LOQ) — COMPLIES with **USP and Ph.Eur.**` |
| Page | `Забелешка: Анализата е направена врз основа на барањето за испитување на пестициди според **cPh Eur.**` |
| Corrected to | `… — COMPLIES with **Ph. Eur.**` |

The result is not in doubt and is impressive: nothing above the 0,01 mg/kg limit of
quantification across **471 residues** — 265 by LC/MS/MS and 206 by GC/MS/MS, both МКС EN
15662:2011 — against IPH's fixed 25-row panel. Ph. Eur. is right too. **USP is the half with no
support: it appears nowhere on the page.** The correction removes an unsupported claim rather
than replacing a wrong one.

Two further facts are recorded in the cell comment rather than changed, because neither is this
register's to decide:

- **The MRL column reads `/`.** The laboratory states no maximum residue level, so "complies"
  on this row means *nothing was detected*, not *below a limit*. A record shaped
  `{value, limit}` has nothing to put in `limit` here.
- **The commissioning client is New Garden Pharma**, not Purely Plant — `Клиент: ЊУ ГАРДЕН
  ФАРМА`, sample identified as `Blue Sunset Sherbet BSS 052501 NGP`. And the report is numbered
  `10802_2845/2` in its header while `Бр. на барање за анализа` on the same page reads
  `10802-2845/1`.

### The guard caught me, for the third time

A first draft of `apply_residual_corrections.py` had the old value as `… COMPLIES with USP`,
because the survey that found the row printed cells truncated to 60 characters and `USP` is
exactly where the cut fell. The refuse-on-mismatch check rejected the workbook and printed the
full string — which is how `and Ph.Eur.` came to light, and how a correction that would have
silently deleted a true half of the cell was stopped.

That is now three times the guard has caught a misreading of mine rather than a corrupt
workbook: the IPH annotation on row 32, the Farmahem `< LOQ` expansions, and this. **A
correction script that only writes when the old value is exactly what was verified is worth
more than the corrections it applies.**

---

## What is left: 40 cells, none of them readable

| | |
|---|---|
| Populated result cells | 1 073 |
| On a page-verified certificate | **1 033 — 96.3%** |
| Never checked against a page | **40 — 3.7%** |

Every external certificate the register cites has now been read. The 40 remaining cells sit on
four **Purely Plant in-house** rows:

| Row | Document | Cells |
|---|---|---|
| 90 | `In-house HPLC cross-check NPCCC/SCP-02, NGP/QCG/SOP-024` | 4 |
| 108 | `In-house GC cross-check NGP/QCG/SOP-024` | 4 |
| 285 | `n/a — Purely Plant in-house CoA (Batch HPA1024, no certificate/report)` | 16 |
| 288 | `n/a — Purely Plant in-house CoA (Batch OPM1024, no certificate/report)` | 16 |

They are unverifiable because they **are** the record, not because anyone skipped them. Their
own code cells say so.

### One of them contradicts itself

Row 288's bile-tolerant GNB reads **`<10²>10³`** — below 100 and above 1000 at once. Nothing
can be both.

The microbiology pass met this construction twice, on rows 92 and 142, and corrected both,
because an IJZ-MB certificate said what the laboratory had actually reported. Here there is no
document to consult. Two readings are plausible — `< 10³ and > 10²`, the standard IJZ-MB
phrasing, or `< 10² and > 10` a decade lower — and both comply with the `≤ 10⁴` limit, so the
batch's disposition does not turn on it.

The cell was **already amber** before this pass, one of the register's original 18 flags
alongside `L285` on the sibling in-house row. What it did not carry was any statement of what
is wrong with it. The diagnosis is now in the comment; the value is left alone. Guessing a
number into a release register is worse than leaving a visible contradiction in it.

---

## The campaign, in one table

| Block | Documents | Values | Agreement | Corrections |
|---|---|---|---|---|
| IJZ-MB microbiology | 40 | 146 | 93.2% | 10 |
| IPH physico-chemical | 44 | 257 | 99.6% | 1 |
| Farmahem cannabinoids | 63 | 168 | 97.6% | 4 |
| Dates of issue | 266 rows | 226 corroborated | — | 11 |
| CNP potency | 73 | 202 | **100%** | 0 (+40 cells filled) |
| Residual | 6 | 26 | 96.2% | 1 |
| **Total** | **226 certificates** | **1 033 cells** | | **27 corrections, 40 fills** |

Every correction was read off a page, applied by an idempotent script that refuses a workbook
it does not recognise, and checked afterwards for byte-level integrity — 268 hyperlinks, 8
merged ranges, and the amber and red flags all intact.

Coverage went from about 2% to **96.3%**, and the 3.7% that remains has no document behind it
to read.
