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

## One more, found while checking the PDFs

39 faces in the Tranche 1 PDF and 27 in Tranche 2 embedded as **Type 3 glyph
procedures** rather than outlines — all of them Montserrat Medium Italic, while
the same family embedded as TrueType elsewhere in the same document. The count
was identical in the previously committed PDFs, so it predates this work.

The cause is one weight. `.ap-cred` sets `font-weight:600; font-style:italic`,
and the font request asked for italic at 400, 500 and 700 only. Chromium took
the nearest real italic and emboldened it, and a synthesised face has no
outlines to embed, so Skia rasterises it. Pinning the variable axes — the fix
that removed Type 3 the first time — fixed the faces the page asks for by name;
it could not fix one the page never asked for.

`1,600` is now in the request. The rule that avoids the next one: **when a rule
sets an italic weight, that weight belongs in `FAMILIES`.**

## The boundary of the ND ruling — 11.09.2026, second ruling

> *"since they're not tested, those sub-parameters are not going to enter inside
> the certificate of quality at all."*

The initial testing of a batch often runs only part of a parameter's panel:
mycotoxins assayed for **total aflatoxins alone**, with Aflatoxin B₁ and
Ochratoxin A not tested. The retest of the same batch then runs all three.

The certificate was printing a bracketed blank for each untested analyte, which
in a results column reads as a finding still to come. Before the ND ruling was
scoped it would have been worse — `n.r.` mapping to `ND`, asserting the analyte
was measured and absent.

So this is the boundary of that ruling, and both halves matter:

* `n.r.` printed **by a laboratory, as a result**, means what `n.d.` means → `ND`;
* an analyte **absent from the panel** is not a result at all → no line.

`fillCoq()` removes the row from the compiled copy. It applies **only to a
sub-determination inside a parameter that was tested** — where nothing in the
group has a result the parameter itself is missing, and that is a gap the
certificate has to show, not hide. The master file is untouched; this is the
compiled copy, the same latitude `addFitStyle` and the marker colour take. Each
compiled document records what was removed in `data-untested` on its `<body>`,
so the omission is on the page's own record rather than only in this note.

**36 rows removed across the 22 drafts — every one of them Aflatoxin B₁ or
Ochratoxin A, on the 18 release certificates whose initial panel was total
aflatoxins alone. Blank printed lines 87 → 51.**

Verified on one batch through `fillCoq` in headless Chromium, both ways:

| BG1024 | mycotoxin rows printed |
| --- | --- |
| initial release, 06.06.2026 | `Aflatoxins ∑ = < 2` |
| retest, 12-month, 17.08.2026 | `Aflatoxin B₁ = ND` · `Aflatoxins ∑ = ND` · `Ochratoxin A = ND` |

## One Macedonian word for one assertion — 11.09.2026, third ruling

> *"use Conforms | Одговара, and use the formatting convention that is set for
> the rest of the CoQ text formatting regarding ENG and MK parts."*

The results column carried **two different Macedonian words for the same
assertion**, and the page disagreed with itself:

* the desk printed **Соодветствува** on 131 results — a word that appears
  **nowhere in the master template** and on no laboratory certificate in the
  record. `build_coq_schedule.py` introduced it in two hard-coded strings;
* the master's own conformity declaration, three rows below on the same page,
  reads **"Одговара на спецификацијата"**, and every laboratory writes
  **Одговара** (and **Не одговара** for a failure — the word whose negation the
  desk had been folding away).

Соодветствува is gone from the desk. **0 occurrences remain** in the certificate
data.

And the column printed 152 results in English only beside 131 bilingual ones.
Every conformity result is bilingual now — **375 paired**. A measured number is
not translated: `20.29`, `< 2` and `ND` print as they are.

### The convention was already in the master

This is the part worth writing down. The formatting convention the owner asked
for is not a house style to be reconstructed — the master **already sets it for
this exact cell**, and nothing had ever used the rule:

```css
.r-conform .mk { display:block; font-size:6.8px; color:#5f8f74 }
```

The Macedonian belongs on its own line beneath the English, a shade smaller, in
the muted green of a conforming result. So the halves are **stacked**, not joined
by the `.bisep` pipe the master keeps for inline pairs like `TAMC | Вкупен
аеробен микробен број`. The pipe is for a label sharing a line; this cell has its
own rule. The export pairs the halves with `" | "`, `fillCoq()` splits on it, and
the master does the styling:

```html
<span class="r-val r-conform">Conforms<span class="mk">Одговара</span></span>
```

The absence rows are the one term the owner did not name: they assert absence,
not conformity. They print **`Absent | Отсутна`** — CNP's own most-used form
(`отсутна/25 g`), capitalised, rather than a term translated afresh for a
controlled document. That is **OI-23**, and it asks for confirmation.

## The page was never measured with the fonts it prints in

Pairing 375 results with their Macedonian is a line of extra height on four rows
of every certificate, and that is when the A4 page turned out never to have been
checked properly.

**"One A4 page" had been verified by reading `scrollHeight` on the page itself.**
`div.page` clips with `overflow:hidden`, so that reading returns the *clipped*
height and always answers zero. The check could not fail. Measured the only way
that means anything — inside an A4 frame, with the subset fonts the PDF embeds —
the baseline was:

| | |
| --- | --- |
| before any of today's certificate work | **5 of 22 past the bottom of the sheet, worst 72 px** |
| P060152 | printing **one** of its two approvers' signature dates; the second was off the sheet |

So this was not a regression to undo but a defect to fix. Four changes, all in
the compiled copy, none touching the master:

* **the Identification C result shortened.** It read *"Conforms — cannabinoids
  identified and quantified by HPLC"*, restating the METHOD column two cells to
  its left on the same row. That single cell stood **85 px** tall against 18 px
  for a normal row. A redundant gloss is not worth a signature (OI-24);
* **a short paired result is held on one line.** The wrapping rule exists for the
  long verbatim results; left to itself it broke `Conforms | Одговара` across two
  lines, and that second line put 15 documents that had fitted over the edge;
* **Section 03's leading closed up.** It grows one row per laboratory, and the
  lot citing four was the last one over;
* **the parameter column's leading closed up** — its two stacked lines set the
  height of every row in the table.

**5 of 22 losing content → 0.** Twenty-one fit outright; the twenty-second has a
few pixels of trailing box space past the edge with **no element beyond it**.

And the builder now measures this on every run and names any document that
overflows, because the page has very little slack left: the next thing that adds
a line will need the check. It says what it measures, too — the HTML drafts carry
no embedded fonts, so its own figure is a fallback-metric approximation and the
rendered PDF is the verdict.

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

---

# v24 — the standing register carries every internal certificate, 11.09.2026

The ruling of 10.09.2026, in the owner's words:

> **The register encompasses every internal certificate that exists or ever
> will**, not only what the drafted lots need. **106 certificates over 80
> batches** — one per testing round, which is exactly the number of certificates
> of quality, because a round that needs a certificate of quality needs the
> internal certificate behind it.

The desk had recorded that as an open question (OI-27) rather than as a ruling to
implement. It is a ruling. This builds it.

## What the sheet was carrying

The iCoA Register sheet printed **60 of the series' 95 certificates**. The
numbering was not the problem — where both carried a row they agreed, which
`verify_workbook.py` had been checking since the morning. The **row set** was the
problem, and a check that compares the codes of the rows a sheet happens to carry
cannot see a row that is not on the page.

| | absent from the sheet |
| --- | ---: |
| retest certificates | 26 |
| release certificates withheld as "not needed" | 9 |
| **total** | **35** |

**No retest certificate appeared at all.** The sheet's retest rows are one per lot
per sampling campaign — "Tranche 1 (sampled July 2026)", "re-analysed", "not yet
sampled" — so GP062501, which has four retest rounds and four internal
certificates, had **one row standing for four documents**. Rounds 2 and up were
not merely unnumbered; they were unaddressable, because the row key `<lot>|R`
named "some retest" and there was only one of it.

**Nine release certificates were withheld on a rule the owner has replaced.**
"Where a CNP certificate reports all three, no iCoA is needed" is the note of
05.09.2026. The ruling of 10.09.2026 is *"identification A, identification B and
foreign matter, **always**"* — they are performed in house on the packaging date
whatever an external laboratory also reports, so the certificate exists, and a
register of every certificate that exists carries it. Which document the
certificate of **quality** cites for those three determinations is a separate
question, decided by `cell_resolution`, and nothing here touches it: the 22
drafted certificates are **byte-identical** before and after.

## What it is now

The sheet **renders `icoa_register.py`** — one row per testing round, 95 codes
printed and numbered, in the order of issue. The series is the definition; the
sheet is a view of it. That is the same repair as the one made to the number
itself in the morning, applied one level up: the number had been a function of a
row's position, and the row set had been a second opinion about which
certificates exist.

Keys are round-specific for the first time. **Retest 1 keeps the bare `|R`** that
the iCoA Issuance sheet, the CoQ Register and the tracker's own in-house cells
already cite, so no lookup changes what it resolves to; rounds 2–5 take `|R2` …
`|R5`. A release round keeps its formulas — testing date from `Batch Dates`,
issue date the later of that and the SOP day — so the workbook stays live. A
**retest is dated at its own sampling, which no sheet holds**, so the series'
dates are written as literals rather than guessed by a formula over a value the
workbook does not have.

| | v23 | v24 |
| --- | ---: | ---: |
| series codes on the sheet | 60 of 95 | **95 of 95** |
| retest certificates registered | 0 of 26 | **26 of 26** |
| rows | 157 | 166 |
| addressable rounds per lot | 1 release + 1 retest | every round |

## Three defects in the desk's own checks, found by fixing the sheet

1. **The register check could not see a missing row.** It compared the code of
   every row the sheet carried and passed at 60 of 95. It now checks
   **coverage** — every certificate in the series appears on the sheet exactly
   once, and no code appears that the series does not issue. Run against v23 it
   reports the 35 that were absent, which is how a gate is shown to bite.

2. **`|R` meant "whichever retest the issue order put first".** The verifier
   built its map with `setdefault` on a bare `|R`, so GP0824_03's `|R` resolved
   to its retest **2** and the sheet's retest 1 was reported as disagreeing with
   the series it had just been taken from. The key names the round now, on both
   sides.

3. **"A legacy iCoA not on the legacy day" did not say which round it meant.**
   A legacy lot is one packed before the SOP, so its *release* certificate is
   back-dated to the SOP's day — but its *retest* is sampled in July or August
   2026 and is issued then, which is the ruling, not a breach of it. The retest
   rounds only reached this sheet today, and the check had never had to be
   precise before. It is scoped to the release round.

   A fourth, smaller one: `table()` recognised a sheet's footnote by its opening
   words — "Head of QC", "Chronological", "These corrections" — so rewriting a
   note fed its own text to `int()` as a row number. A footnote is now recognised
   by its shape: one long string spanning the table's width with nothing beside
   it.

## What it could not fix, and why

**Seven lots have no internal certificate at all** — GG1024, BSS1024_01/2,
WED102501, GRC102501, GG012601, JD012601 and SCR012601*. The cause is the
**star**. The company writes `GG012601*`; the testing record writes `GG012601`;
and `batch_id.batch_key` keeps the mark deliberately, its own docstring saying
that whether a starred lot and its unstarred namesake are the same batch *"is NOT
a question this function may answer: it is a fact about the floor"*. So the
testing record attaches to one spelling and the register row to the other, and
neither can see the other.

That is the whole of the difference between the sheet's 83 release rows and the
series' 76. The seven sit on the register unnumbered, each saying the series does
not carry it, and the question is **OI-28**: for each pair, is the starred lot
the same batch? A ruling goes in `ingestion/ecoa_runner/identity_decisions.tsv`,
which is where `batch_key` says such a ruling belongs, and the seven certificates
then issue by themselves.

## Reproducing

    python3 deliverables/qc_gap_analysis/open_items.py --md
    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=24 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=11.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026
    python3 deliverables/qc_gap_analysis/tracker/verify_workbook.py \
        deliverables/qc_gap_analysis/tracker/CoQ_Analysis_Master_v24.xlsx
    python3 deliverables/qc_gap_analysis/tracker/extract_artifact_data.py \
        deliverables/qc_gap_analysis/tracker/CoQ_Analysis_Master_v24.xlsx \
        deliverables/qc_gap_analysis/tracker/v24_data.json "CoQ Parameter Tracker v24"
    python3 deliverables/qc_gap_analysis/tracker/build_artifact_page.py \
        deliverables/qc_gap_analysis/tracker/v24_data.json

**v24 verifies with 0 findings**, the deeper pass compares **5,341 printed
results** against the certificate records with 0 findings, and the 2,330
recalculated formulas produce **0 error values**.
