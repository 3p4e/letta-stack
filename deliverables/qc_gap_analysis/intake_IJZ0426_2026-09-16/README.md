# The April-2026 IJZ release panel — intake of 16.09.2026

Eighteen certificates of the Institute of Public Health on the nine lots sampled on
**21.04.2026** — the release testing of the spring-2026 packaging:

| laboratory | numbers | received | issued | what they carry |
| --- | --- | --- | --- | --- |
| IJZ-MB (microbiology) | `304/0548/26` … `312/0556/26` | 22.04.2026 | 28.04.2026 | TAMC, TYMC, bile-tolerant gram-negative bacteria, *E. coli*, *Salmonella* — Ph. Eur. 5.1.8 Kat. C |
| IJZ (contaminants) | `2357/2026` … `2365/2026` | 21.04.2026 | 29/30.04.2026 | total aflatoxins (AflaTest, fluorometric), Pb, Cd, As, Hg (МКС EN 17851:2023), the 29-line pesticide panel (МКС EN 15662:2020) |

The lots: CC112501 (P060272), FB112501 (P060292), GG112501 (P060252), SCR112501 (P060282),
FB012601/1 (P060322), JD112501 (P060212) **and its starred second sample JD112501\***,
GG012601\* (P060302), JD012601\* (P060312). The scans are in the owner's `eCoA_DATABASE`,
named `<ddmmyy>_<code>_IJZ[-MB]_<batch>-<P lot>.pdf`; `reads_IJZ0426.json` names each with
its Drive file id.

## Why this intake exists

Seventeen of the eighteen have been in the ingested corpus since 04.09.2026
(`ingestion/ecoa_runner/records_corpus.json`) and **all eighteen are on the Head of QC's own
tracker** (`tracker/v8_values.json`). **Not one is a row of the release register**, which is
the one source the certificates of quality are compiled from. So the eight release
certificates of quality of these lots print

    not tested — no certificate covers it

for #9 microbiology, #10 mycotoxins and #11 heavy metals, and take #12 pesticides from the
owner's 09.09 resolution pass alone — with the documents on file, dated five weeks before the
certificates. `CoQ-PP_26-057` (JD112501 / P060212, issued 06.06.2026) prints "not tested"
eleven times while `307/0551/26` and `2361/2026` sit in the corpus with every value read
twice. It is the gap the IJZ-MB intake of 16.09.2026 closed for the August campaign, one
sampling earlier — the same class: ingested, tracked, never a row of the register.

The audit of 16.09.2026 (`tracker/FLEET_FINDINGS_2026-09-16.md`) found that this is the
nearest edge of a wider gap — 44 laboratory scans on Drive that no desk record holds at all,
20 of them IJZ contaminant reports and 22 IJZ-MB reports of other lots. Those are not in the
corpus and need their own reads; this intake takes the eighteen whose reads exist.

## The gate

Every certificate carries **two independent reads** and `apply_IJZ0426.load_reads()` refuses
to write anything if any certificate disagrees on a determination the register has a column
for. `build_reads.py` assembles the file:

* **Reads A and B** are the eCoA runner's two vision reads of the page rendered at 300 DPI
  (`records_corpus.json`, `raw.A` / `raw.B`).
* **`310/0554/26`** (GG012601\*) was never read by the runner. Its read A is the RAGflow OCR
  of 30.08.2026 (`ingestion/ragflow/cache/all_cert_texts_2026-08-30.json`), its read B the
  Head of QC's own transcription on the tracker (`tracker/v8_values.json`,
  `GG012601＊|310/0554/26`); the Drive OCR is its third and confirms the three lines whose
  characters survived OCR. A and B agree on all five.

**Four disagreed on a value**, and each was settled by a **third read of the page on
16.09.2026** (`read_C`, its source named beside it; the texts are in `third_reads/`,
verbatim — Google Drive's OCR of the scan, cross-checked with the RAGflow OCR of the same
scan):

| certificate | line | read A | read B | the page |
| --- | --- | --- | --- | --- |
| `307/0551/26` | bile-tolerant GNB | `< 10¹ – 10² CFU/g` | `< 10³ и >10² CFU/g` | **`<10³ и>10²`** — B |
| `304/0548/26` | bile-tolerant GNB | `< 10^2 CFU/g` | `< 10² и >10 CFU/g` | **`<10² и>10`** — B |
| `305/0549/26` | bile-tolerant GNB | `<10³ x10² CFU/g` | `< 10³ и >10² CFU/g` | **`< 10³ и >10²`** (RAGflow) — B |
| `2361/2026` | pesticide lines | 29, all н.д. | 28, all н.д. | **29** (26 on page 2, 3 on page 3) — A |

Three of the four are the bile-tolerant line with one read stopping at one bound where the
page carries the range — **OI-36's class, with three more instances** (the IJZ-MB intake found
four). The Head of QC's tracker holds two of those lines as "held for review"; the third read
settles them. On `305/0549/26` the Drive OCR itself dropped an exponent ("< 10 и>10²", which
no page can say), and the RAGflow OCR and read A's digits carry it — recorded, not hidden.

Everything else the two reads differ on is **notation** — a unit written or not, "отсутна"
against "отсуство" against "отсуства", a superscript against a caret, "JDD12601\*" against
"JD012601\*" on a batch line whose page prints `JD012601*` — and `_fold` reads those as one
assertion, which is the standing vocabulary ruling of 11.09.2026, not a new judgement.

## What was written

**17 rows into existing blocks, one empty row filled in place, no block opened.** The owner
had opened a row for `305/0549/26` in the SCR112501 block — the laboratory number in column W,
"/" in every result column, no date — and that row is the certificate's row: it is filled,
not skipped or duplicated.

The row shapes are the register's own:

* **IJZ-MB row** — J…N: TAMC, TYMC, bile-tolerant GNB as the page prints them (`2,6×10³`,
  `< 10³ и > 10²`), `Одговара (absent)` for *Salmonella* and *E. coli*, the shape the
  IJZ-MB intake of 16.09.2026 wrote. One spelling across the eighteen: a caret exponent
  becomes the superscript the page prints, a bound is set off from its number.
* **IJZ row** — O…V: `<2` for total aflatoxins, `not tested` for aflatoxin B1 and ochratoxin A
  (the fluorometric total does not report them), the four metals as text with a decimal point
  (`0.022`), `N.D.` for a panel that is н.д. on every line — exactly as the register's IJZ
  rows of 2025 (`752/2025`, `2157/2025`) carry them.

`/` in every other column, the laboratory number in the register's own spelling, the date of
issue, `IPH — Institute of Public Health`, `Open`.

Blocks are found by the batch the page names, by the P number the scan's file name carries,
and — for the three starred spellings — by the star-stripped label the register uses.

## The starred sample

`306/0550/26` and `2365/2026` print the batch **`JD112501*`**. Under the Head of QC's ruling of
16.09.2026 a starred cultivation batch is a **second sample of the same packaged lot**, real
data that never certifies. They go into the JD112501 block beside `ППК26065`, exactly as the
owner's own register already holds that certificate, and `testing_series.EXPERIMENTAL` names
them, so:

* the values are in the register, on the tracker and in every statistic;
* no certificate of quality cites them — `CoQ-PP_26-057` takes `307/0551/26` for #9 and
  `2361/2026` for #10–#12.

**One consequence the Head of QC should see.** The 09.09 resolution pass cited
**`306-0550-26`** — the starred sample's microbiology (TAMC `1 × 10⁴`) — for JD112501's #9,
and `2361-2026` (the unstarred sample) for #10–#12. The ruling of a week later says the
starred sample does not certify, so the desk now cites `307/0551/26` (TAMC `2,6 × 10³`) for
#9. Both results conform. It is recorded on OI-12; one word reverses it.

GG012601\* and JD012601\* are **not** that case: each is the only spelling its lot has, with
its own P number and no unstarred twin sample (`identity_decisions.tsv`, 16.09.2026). Their
documents go into the blocks the register labels GG012601 and JD012601, beside the 227-К and
the campaign IJZ-MB certificates of the same lots that the intakes of 15 and 16.09.2026
already placed there.

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_IJZ0426_2026-09-16/build_reads.py
    python3 deliverables/qc_gap_analysis/intake_IJZ0426_2026-09-16/apply_IJZ0426.py --register <register> --out <copy>

The apply is idempotent; the reads file is committed so the gate's verdict is reviewable
without the corpus.
