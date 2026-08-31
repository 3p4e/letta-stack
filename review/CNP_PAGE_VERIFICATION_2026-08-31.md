# The CNP potency certificates, read off their own pages

**Scope:** the last large never-verified block in the register — **all 73** certificates
from the UKIM Faculty of Pharmacy Center for Natural Products, carrying Δ9-THC, CBD, CBN and
loss on drying across 79 register rows. Every value taken from the rendered page. These are
pure scans; `pdftotext` returns nothing.

## Result

| | |
|---|---|
| Certificates read | **73 of 73** |
| Register values compared | 202 |
| Agreement | **202 — 100%** |
| Corrections to existing values | **0** |
| Results the register did not hold | **40 cells across 10 certificates** |

**Not one value the register already held is wrong.** This is the first family to come back
perfect, and it is also the family where perfection was cheapest to check — which is the
point, not a coincidence.

Every CNP certificate of the older form prints Δ9-THC, Δ9-THCA and Вкупно Δ9-THC in adjacent
rows, and prints the relation between them in its own footnote:

> \*\*\* Вкупно Δ9-THC - сума на содржина на Δ9-THC и Δ9-THCA x 0.877, изразена како Δ9-THC

So each page carries a proof of its own consistency that needs nothing outside itself. It held
on **60 of 60** certificates that print the breakdown, every one to within 0.01. A family that
can check its own arithmetic is a family that gets transcribed correctly.

Set against the other three blocks read this week, the pattern is not about care:

| Block | Notation | Agreement |
|---|---|---|
| IJZ-MB microbiology | superscript exponents, `<10³ and >10²` | 93.2% |
| Farmahem | four columns, result beside its own uncertainty | 97.6% |
| IPH physico-chemical | plain decimals | 99.6% |
| **CNP potency** | **plain decimals with a printed self-check** | **100%** |

---

## A. Ten stability certificates whose results are recorded nowhere · rows 52-54, 58-60, 94-97

These rows name a certificate, an issue date and an institution, and then hold `/` in every
result cell. The register's own legend defines `/` as *parameter not covered by that
certificate*. All ten certificates cover all four parameters. **The rows assert an absence the
documents contradict.**

They are the Grape Pie stability studies — three sample lots (`P050022`, `P050072`, `P050202`)
at 3, 6 and 9 months, under 25 °C / 60 % RH and 40 °C / 75 % RH. Filling them is a correction,
not an addition; every value passes R4.

| Row | Certificate | Condition | Δ9-THC | CBD | CBN | LoD |
|---|---|---|---|---|---|---|
| 94 | `ППК26036` | m3, 25 °C | 22.83 | 0.05 | 0.05 | 5.83 |
| 95 | `ППК26037` | m3, **40 °C** | 18.62 | 0.04 | **1.09** | 5.38 |
| 52 | `ППК26032` | m6, 25 °C | 21.31 | 0.03 | 0.23 | 6.32 |
| 53 | `ППК26033` | m6, **40 °C** | 13.16 | 0.05 | **2.35** | 5.84 |
| 58 | `ППК26034` | m6, 25 °C | 24.62 | 0.04 | 0.05 | 5.92 |
| 59 | `ППК26035` | m6, **40 °C** | 14.99 | 0.02 | **2.15** | 5.52 |
| 96 | `ППК26057` | m6, 25 °C | 24.51 | 0.05 | 0.04 | 6.85 |
| 97 | `ППК26058` | m6, **40 °C** | 17.05 | 0.03 | **2.05** | 6.60 |
| 54 | `ППК26059` | m9, 25 °C | 23.08 | 0.03 | 0.30 | 6.62 |
| 60 | `ППК26060` | m9, 25 °C | 25.98 | 0.04 | 0.04 | 7.07 |

**Every one of the four 40 °C / 75 % RH samples is over the `≤ 1.00 %` CBN limit printed on
its own certificate.** Four for four, and the Δ9-THCA column says why: at 40 °C the acid has
decarboxylated to 0.17, 0.01, BLQ and 0.07, and the neutral cannabinoids have oxidised on to
CBN. The matched 25 °C samples read 0.04 to 0.30 with THCA intact between 10 and 17 %. This is
the study working.

It still matters that these numbers were in no register at all: **not one of the ten was
visible to any check**, and once written, four of them trip the register's own R1 rule
immediately — R1 findings go from 9 to 13. None of the certificates carries a verdict of any
kind, so whether an accelerated-condition sample is expected to meet a release limit is a
question for the stability protocol. They are flagged amber, which the legend defines as *a
laboratory finding*.

Six further rows — 124, 128, 132, 136, 140, 165 — also hold `/` throughout, and are **left
exactly as they are**. Each names a certificate that already appears with its values on an
earlier row of the same batch block. They are second references, not gaps.

---

## B. The one batch that failed release, and why nothing numeric could catch it · row 260

`ППК26127`, `FB032601`, 21.07.2026. It is the only CNP certificate in the corpus that carries
a **ЗАКЛУЧОК**, and the only one that concludes:

> Испитуваниот примерок сув цвет од медицински канабис сорта Fat Bastard, серија FB032601 …
> во однос на параметарот „Страни материи“, **НЕ ОДГОВАРА** на барањата пропишани во
> Ph. Eur. 11.5, монографија *Cannabis flos* (07/2024:3028), **поради утврдено присуство на
> семе од канабис.**

Its foreign-matter result is **0.08 %** against a maximum of **2.00 %** — twenty-five times
inside the limit — and the cell beneath it reads `(Не одговара)`.

The operative half of that limit is its parenthetical: *макс. 2.00 % (без присуство на семе и
листови подолги од 1 cm)*. Seed was found. The sample fails whatever the percentage says.

**Every numeric value on this page is in specification.** R1 passes it. R4 does not apply to
this form. The register's column comparisons pass it. A validator that compares a value
against a limit — which is the entire design of `validate_ecoa_limits.py`, and of the typed
extraction record the ingestion plan proposes — passes it. The only thing that fails this
batch is a sentence.

And the register has no foreign-matter column and no verdict column, so **row 260 is today
indistinguishable from row 262**, `GG032601`, which passed. The certificate code is flagged
red, which the legend already defines as *result the issuing laboratory declared out of
specification*, with the conclusion quoted in the cell comment. Adding the two columns is a QC
decision, not a transcription fix.

This is the strongest single argument in the whole verification campaign for **carrying the
laboratory's own verdict as a field**, separately from any value. A record that stores
`{value: 0.08, limit: 2.00}` and derives conformity by subtraction gets this batch wrong. A
record that stores `verdict_printed: "НЕ ОДГОВАРА"` gets it right without understanding a word
of it.

---

## C. The loss-on-drying column states one limit where the certificates apply two

The register's header reads `≤ 12.00 (3028)` — the Ph. Eur. monograph 07/2024:3028 figure.
**Only 12 of the 73 certificates are issued against that monograph.** The other 61 print
`Губиток при сушење ≤ 10.00 %` and were judged against 10.00.

Nothing in the set is affected in fact: the highest reading is 9.68 % on `ППК25370`, under both
limits. But 9.52 % (`ППК25368`) and 9.68 % sit just under the limit that actually applied and
look comfortable against the one the register shows.

**This is the third time this week the same shape has appeared** — the IPH heavy-metal limits
changed vintage mid-corpus, the microbiology 10⁴ column hid a result over its own printed 10²,
and now this. Twice the register was stricter than the paper and produced false alarms; here it
is looser. *A validator that compares against the column is not comparing against the
certificate, in either direction.* A scope note is on the header cell; the fix is a per-row
limit, which is what the typed record exists to carry.

---

## D. Two certificate forms, and only one of them can check its own arithmetic

| | Older form | Ph. Eur. 11.5 form |
|---|---|---|
| Certificates | 61 | 12 (`ППК26110`–`26128`) |
| Method | DAB 2018 monograph | Ph. Eur. 11.5, *Cannabis flos* 07/2024:3028 |
| Rows | LoD, CBDA, CBD, CBN, Δ9-THC, Δ9-THCA, Вкупно CBD, Вкупно Δ9-THC | identification, foreign matter, LoD, and the three totals only |
| LoD limit | ≤ 10.00 % | макс. 12.00 % |
| Identification | not tested | macroscopy + microscopy, `Одговара` |
| Foreign matter | not tested | макс. 2.00 % |
| **R4 possible** | **yes** | **no — no Δ9-THC / Δ9-THCA breakdown is printed** |

The newer, more thorough form is the one that **cannot be self-checked**. It reports more
parameters and gives away less: without the acid and neutral figures there is no arithmetic
relation between anything on the page, so a transcription error in the total is invisible. The
12 certificates on this form are exactly the 12 for which page-reading is the only control
there is.

The newer form also introduces the trap the ingestion plan named in advance and can now point
at a page: `Вкупно Δ9-THC* — мин. 5.00 %` is a **specification**, not a measurement. An
extractor without a spec guard reports 5.00 as the batch's potency. The register handles this
correctly — it carries `≥ 5.00 %` in its own THC-spec column and 20.83 as the result.

Two per-form inconsistencies worth recording: the identification limit cell cites `Ph.Eur.
11.0` on `ППК26110/26112/26114/26127/26128` and `Ph.Eur. 11.5` on `ППК26116`–`26119`, while the
Метод paragraph above always says 11.5. And foreign matter prints a number on only two of the
twelve (`0.09 %` on `ППК26114`, `0.42 %` on `ППК26117`, `0.08 %` on `ППК26127`); the other nine
print `/` with `(Одговара)` beneath it — a tested parameter with no reported value.

---

## E. A suffix is the only thing separating two different samples

| Certificate | серија | Δ9-THC | LoD |
|---|---|---|---|
| `ППК26063` | `JD112501` | 19.64 | 6.69 |
| `ППК26065` | `JD112501*` | **13.93** | 6.38 |
| `ППК26113` | `JD012603/02` | 20.54 | 7.52 |
| `ППК26111` | `JD012603/02V` | **15.16** | 7.04 |
| `ППК26112` | `FB012603` | 20.83 | 7.04 |
| `ППК26110` | `FB012603V` | **18.29** | 6.36 |

Same strain, same issue date, same laboratory, batch strings differing by a single trailing
character — and results five points apart. The suffix is load-bearing.

**The register handles this correctly**: rows 235/236, 246/248 and 240/242 are separate and
each carries the right numbers. But rows 235 and 236 both read `JD112501` in the batch column,
because the asterisk was dropped while the `V` was kept. Any lookup keyed on the batch string
alone merges two distinct analyses, and `ingestion/common/batch_id.py` — whose job is exactly
this — would fold `JD112501` and `JD112501*` together. The certificates give no definition of
either suffix.

## F. Five spellings of one strain, and two impossible dates

`Cup Junky` (`ППК25052`, `ППК25367`), `Cupjunkie` (`ППК25280`), `Cup Junkie` (`ППК25281`),
`Cap Junkie` (`ППК25321`, `ППК25322`), `Cap Junky` (`ППК26002`, `ППК26003`, `ППК26007`). One
laboratory, nine certificates, five spellings; `ППК25280` and `ППК25281` were issued on the
same day, for two lots of the same batch, spelled two ways.

Two certificates print a `Дата на завршено испитување` that cannot be right, both in the
January 2026 series where the siblings all print `16.01.2026`:

| Certificate | Prints | Sample delivered | Certificate issued |
|---|---|---|---|
| `ППК26002` | `16.01.2025` | 08.01.2026 | 21.01.2026 |
| `ППК26004` | `16.12.2026` | 08.01.2026 | 21.01.2026 |

One a year before the sample existed, one eleven months after the certificate was signed.
Neither is a value the register records — its Date of issue column takes the `Скопје, …` header
date, which is correct on both — so nothing needs correcting. They are worth knowing about
because a pipeline that reads "analysis completed" from these pages will read two impossible
dates, and neither is out of range in any way a format check can see.

`ППК25118` carries a hand-written overwrite in the серија field (`MB0824_` then a manuscript
`04`), and three stability certificates print the sample lot with a letter `O` where their
siblings print a zero — `PO50022` against `P050022`, `PO50202` against `P050202`. The register
has the digit on all of them.

---

## Method

Per certificate: fetch from Drive — the result lands on disk and never enters context, which is
what makes 73 documents affordable — render at 200 DPI with `pdftoppm`, crop to 0.10–0.82 of
page height so the `Број на главна контролна книга: ППКnnnnn` line and the issue date survive
alongside the whole results table. A crop that cannot name its own certificate cannot be checked
against the document it came from.

`ППК26127` was re-rendered a second time, uncropped below the table, once the first read showed
a ЗАКЛУЧОК heading running off the bottom edge. That second render is where the failure was
found.

Every reading was then put through two independent gates before being accepted: the register
comparison, and R4 against the certificate's own footnote formula. Both are in
`deliverables/qc_gap_analysis/compare_cnp_reads.py` and can be re-run from the committed
`review/cnp_page_reads_2026-08-31.json` and `review/cnp_register_extract_2026-08-31.json`.

Two comparison rules were added during the work, and neither is laxity. `0.10` and `0.1` are
the same measurement — the page keeps the laboratory's two decimals, the register drops a
trailing zero — so numbers are compared as numbers. And `BLQ (below limit of quantification)`
in the register is the page's `BLQ` plus the footnote that defines it: the register being more
informative than the page, exactly as with Farmahem's `< LOQ (<0.20)`.

Classical OCR is not used and is forbidden by `scripts/policy_check.py` rule 1.

## Verification coverage of the register

| | |
|---|---|
| Populated result values in the register | ~1 295 |
| Verified against a document before this week | ~30 (~2%) |
| After microbiology (40 certificates) | 146 |
| After IPH physico-chemical (44) | 403 |
| After Farmahem (63) | 571 |
| After dates of issue (266 rows) | 797 |
| After this pass (73 certificates) | **~993 (~77%)** |

(About six values are counted twice: `ППК25117` and `ППК25139` were read on 30.08 and are
inside this pass's 202. The figure is rounded down accordingly.)

What remains unverified is no longer a family. It is the residue: the microbiology and
contaminant columns on rows whose certificates were read for other parameters, the 41 in-house
PP CoAs, the two NGP documents and the phytosanitary reports — the Class B documents the
ingestion plan set aside because they have no fixed layout to validate against.
