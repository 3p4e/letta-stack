# One spelling per assertion, and a verdict the desk could not read — 11.09.2026

The owner asked for the v22 workbook to be checked "in terms of the parameter
values and references". Twenty-one result columns and 1,193 references were read
cell by cell, against each other, against `Batch Dates`, the `iCoA Register` and
the `Mikro CoQ Parameter` sheet. This is what it found and what was done.

## What was already sound

Nothing in the reference layer was broken. 965 external references parse as
`CODE, (DD.MM.YYYY) [LAB]` and 228 iCoA formulas all resolve against the
register — **0 broken keys**. No document code carries two dates or two
laboratories. **0 references are dated before their lot's manufacturing date.**
Pairing is exact: 0 results without a reference, 0 references without a result,
0 results without a ✓/✗/○ mark, 0 marks without a result.

## The one that mattered

**FB032601's foreign matter was printing a pass against a certificate that says
it fails.**

CNP's ППК26127 of 21.07.2026 reports `0.08% (Не одговара)` — *does not conform*.
The figure passes the gravimetric ≤ 2.0 % limb, so CNP is failing it on another
limb of Ph. Eur. 2.8.2, leaf and stem size. The desk never saw the verdict,
because of one regex:

```python
if re.search(r"одговара|отсутн|отсуств|absent", v, re.I):
    v = "absent"
```

`Не одговара` **contains** `одговара`. The laboratory's non-conformity was being
folded into `absent`, and every judge downstream reads `absent` as a pass. The
negation is now tested first, `nonconforming()` is a named predicate with its own
doctests, and `over_limit()` gained a second limb:

> a laboratory writing *Не одговара* has already done the judging, against the
> limb of the criterion it applies, and its verdict outranks anything the desk
> can compute from the figure alone.

FB032601 now reads **OOS** on #7 and its certificate cell is **BLOCKED —
declared out of specification by the laboratory**. It cannot print `Conforms`.

## A correction to the audit itself

The first pass reported "13 results breach their acceptance criterion, all marked
✓". That was a misreading of the sheet and is withdrawn. **✓ is a coverage mark** —
a certificate is on file and its result is on the desk — not a verdict; out of
specification is carried by red bold on the result. All 13 were already flagged
correctly: 5 TYMC counts red (above 2 × 10⁴ under Ph. Eur. 5.1.4), 4 amber in the
undetermined band, and the 4 CBN values over 1.0 % are **stability timepoints**,
which the desk excludes from release judgement and names separately in STATUS.
The enforcement was right; the reading of it was not.

And the delta-HCH finding is withdrawn on the owner's confirmation: IJZ 2994/2025
reports delta-HCH at `< 0.01` mg/kg against a maximum of 0.3, the other 28
residues `н.д.`, and the page's own verdict is **ОДГОВАРА**. The result is
correctly transcribed. What survives is that the column's stated criterion is
`≤ LOQ`, which is not the Ph. Eur. 2.8.13 test — that is OI-15.

## One assertion, nine spellings

The ND ruling of 10.09.2026 had been applied to the export path and never to the
desk that feeds it, so the workbook still carried every original spelling. And
the same disease ran through five more families:

| assertion | spellings in v22 | now |
| --- | --- | --- |
| not detected | `n.r.` ×115, `н.д.` ×36, `Н.д.` ×17, `Н.Д.` ×6, `N.D.` ×1 | `ND` |
| absent | `absent`, `Одговара`, `Odgovara`, and 9 Cyrillic forms | `Absent` |
| below quantitation | `<LOQ`, `< LOQ`, `<LOQ**`, `BLQ`, `BLQ ᴰ`, … | `< LOQ` |
| conforms | `Conforms`, `Одговара`, **`Confirms`** (a typo, ×7) | `Conforms` |
| a counted colony | `×`, ` x `, `·`, `и`, `and`, `10^2` | `1.6 × 10⁴`, `< 10² and > 10` |
| a mass fraction | `0.02 ᴰ` beside `0.02 % ᴰ` | the column states the unit |

`result_vocabulary.canon()` is the single definition, applied in `values_of()` —
the one funnel every result passes through into the workbook — and on the export
path, so the workbook, the certificates and the PDFs inherit one spelling from
one place. It takes the **determination number**, because `Одговара` means
*conforms* in the identity columns and *absent* in the Salmonella and E. coli
columns and only the column can tell them apart.

It rewrites notation and nothing else. Digits, footnote markers, the ᴿ and ᴰ
markers, residue glosses and parenthetical LOQ values all survive, and a
laboratory's own verdict is preserved *as* a verdict.

**Result:** 0 non-canonical not-detected spellings remain on the tracker or the
Mikro sheet, absence collapses from 12 spellings to 3 in the workbook and **from
4 to 1 on the certificates**, and 390 printed results now come from the
controlled vocabulary.

Two things the desk was doing to itself, also fixed:

* it generated `n.r.` **itself** for a sub-determination a certificate does not
  report — the owner's reserved notation, used for something that is not a
  result. Writing `ND` there would assert the analyte was measured and absent,
  which is the one thing the cell knows to be untrue. It now says
  **`not reported`** and the notation is left to results;
* `NO-DOC-CODE (Report of Analysis)` was cited directly on Identification A and
  foreign matter for GG1024, HPA1024 and OPM1024 — an in-house result referenced
  without an iCoA, which the standing ruling forbids. All six cells now carry the
  register's own `iCoA — at issue (…)` form. **0 literal in-house references
  remain.**

## Three lots that were one lot to every join

`P160012`, `P160022` and `P160032` each printed the cultivation batch as
`— not recorded —`, so `batch_key` collapsed all three to a single key. Any join
made on the printed cultivation batch silently picked one of the three — which is
exactly what was happening between the tracker and `Mikro CoQ Parameter`, where
three parameter blocks "disagreed" that were never the same lot.

The label now names the P number inside it. The cultivation batch stays
unrecorded rather than invented (OI-10 asks for it).

**80 rows → 80 distinct keys** on the tracker and on Batch Coverage, where both
were 78. Mikro against the tracker: **0 differing parameter blocks**, from 3.

## Batch Coverage: two questions, two pairs of columns

`Certificates (n)` and `Labs present` came down from v6 and were *incremented* by
every pass that touched a lot, so they counted documents the tracker does not
cite and could not be reconciled with it — 22 rows whose count exceeded the
references (JD012603 said 7, the tracker cites 2) and 26 naming a laboratory that
appears in no reference on the lot.

The count was not wrong so much as answering a different question: it included
the 09.09.2026 documents the desk has not recorded. So the two questions now get
two pairs of columns, both derived here from the tracker rather than carried
forward:

| | |
| --- | --- |
| `Certificates (n)` · `Labs present` | what the tracker actually cites |
| `On file, not recorded (n)` · `Labs on file, not recorded` | the 09.09 documents the desk has not recorded |

**Labs present: 26 disagreements → 0.** Certificates (n): 22 → 3, and all three
are explained and recorded — GRC102501 carries two P batches in one cell (OI-11),
JD112501 and its ＊ sub-lot share three documents (OI-12), and BSS052501's DFL
report is on file twice, once per language (OI-09).

## The Open Items sheet

Fifteen findings across this session and the last are the owner's to settle, and
they were living in chat messages. `open_items.py` is the standing register —
**20 items, 17 awaiting a ruling, 3 marked on the certificate** — and it drives
both the **Open Items** sheet of the workbook and `OPEN_ITEMS.md`. Each says what
was found, what the desk did with it, precisely what is being asked, and the
evidence behind it, because *"there is a problem with the specifications"* is not
a question anyone can answer and OI-01 is.

## Reproducing

    python3 deliverables/qc_gap_analysis/result_vocabulary.py
    python3 deliverables/qc_gap_analysis/open_items.py --md
    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=23 --icoa --cells \
        --mikro=deliverables/qc_gap_analysis/tracker/CoQ_Analysis_Master_v13.xlsx \
        --build-date=11.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026
    python3 deliverables/qc_gap_analysis/tracker/verify_workbook.py \
        deliverables/qc_gap_analysis/tracker/CoQ_Analysis_Master_v23.xlsx
    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_live_instrument.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_coq_drafts.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv \
        --chromium /opt/pw-browsers/chromium-1194/chrome-linux/chrome

**v23 verifies with 0 findings**, and the deeper pass compares **5,287 printed
results** against the certificate records with 0 findings.
