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

---

# v25 — the workbook says what has been ruled, 11.09.2026

The Read Me sheet's own VERSION HISTORY stopped at v11 and its RULINGS IN FORCE stopped at
05.09.2026 — nine versions and six days of built, verified, pushed work that the workbook
never wrote down about itself. A person opening `CoQ_Analysis_Master_v25.xlsx` cold, reading
only its own Read Me, would not learn that the register is standing, that an analyte never
tested does not appear on a certificate, or that a laboratory's own non-conformity is read as
one. Extended through v25, both sections, from primary sources: the git history for what each
version actually built, `ISSUANCE_RULES_2026-09-10.md` and `VOCABULARY_2026-09-11.md` for the
rulings' own wording.

## Two findings that were written down once and then left

Auditing for rulings not reflected in the workbook surfaced two findings that exist in this
folder's own prose but never reached the standing register:

* **OI-30 — the Loss on Drying method line is uniform across every lot.** The ruling of
  10.09.2026 says the certificates should attribute the method each lot was actually tested
  by (German pharmacopoeia, < 10 %, before the Ph. Eur. cannabis monograph 3028; the Ph. Eur.
  method, ≤ 12 %, after). The printed method line has always been the latter, for all 80
  lots. The one lot whose own numeric result sits where the two criteria disagree —
  J31122501, 10.30 % — was already investigated and resolved on 31.08.2026: the certificate
  prints its own limit as `< 12`, so `≤ 12.0 %` is that certificate's own specification, not a
  substitution. What remains unverified is the method TEXT on the other ~94 lots, because no
  certificate's own method paragraph is in the desk's record — only its number.
* **OI-31 — six batches are silently filed under one strain name.**
  `DELIVERY_RECONCILIATION_2026-09-07.md` records, and never closed, that the desk files GG4
  (GG012601, GG012603, GG112501) and Gorilla Glue (GG1024, GG1024_01, GG1024_02) under one
  strain name while the delivery sheet keeps them apart — unlike its six siblings in the same
  finding, which all print on the Work Order as "strain name unruled." Today's iCoA Issuance
  sheet prints all six as `Gorilla Glue`, a merge nobody ruled on. No certificate is wrong
  today because none of the five non-`GG1024` lots carries a specification at all (OI-03) —
  but the day one is filed under either name, the merge decides the other five by default.

Neither is fixed by guessing. `strains.py`'s own rule is to repair a missing space (decides
nothing) or list a letter-for-letter disagreement for a ruling (decides nothing either) — not
to merge two names that differ in their letters, which GG4 and Gorilla Glue do.

## One item shortened, not because it closed by ruling

OI-14 named three placeholders; Identification C's document sourcing is built —
`_pick(4, False) or _pick(3, False)` resolves it on all 22 drafts, 0 falling back to the
unresolved message — so the clause is folded out rather than left to read as still open. The
other two (the approvers' names, the potency range) are still the master template's specimen
and still open.

## Reproducing

    python3 deliverables/qc_gap_analysis/open_items.py --md
    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=25 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=11.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026
    python3 deliverables/qc_gap_analysis/tracker/verify_workbook.py

**v25 verifies with 0 findings**, the deeper pass compares **5,341 printed results** against
the certificate records with 0 findings — unchanged from v24, because nothing here touches a
certificate: `coq_artifact_data.json` and every drafted certificate are byte-identical before
and after.

# v26 — seven tabs, not sixteen, 14.09.2026

The owner, 14.09.2026: "Do we need all of those chips? I really need just these" — Batch
Coverage, the tracker, iCoA Register (with iCoA Issuance inside it), Batch Dates, CoQ
Register, Parameters — "or you can put all those formula calculating misc in one sheet?"

## What moved

The **iCoA Issuance** sheet is gone. It was one row per batch and round, which is exactly what
the iCoA Register is, so its eleven columns that the register did not already carry (basis
date, harvest, packaging, planned CoQ issue, the three in-house results, identification C's
eCoA, the retest assay and mycotoxin eCoAs, carried-forward) are now register columns. Nothing
looked the issuance sheet up by formula — the register was always the lookup target — so no
key changed. The register's `Key` column moved from P to AA; `REG_KEY_COL` is now asserted
against `REG_COLS` at build time, because a formula matching the wrong column would resolve
silently to the wrong certificate.

Ten sheets — Read Me, Delivery T1–T3, ImB Register, Mikro CoQ Parameter, Reconciliation
09.09, Credit Audit, Credit Corrections, Work Order, Open Items, Summary Dashboard — are now
sections of one **Reference** sheet (817 rows), each under its own title in capitals. Nothing
was deleted: none of them is a formula source, but they are the audit trail.

## Where a section ends is recorded, not guessed

The first fold marked section boundaries by a two-row blank gutter, and the reader looked for
that gutter. Reconciliation 09.09 separates its *own* sections with the same gutter, so the
reader stopped at the first inner one and the sheet lost its last section — "CLOSURES THAT
FOUND NO ROW", eight rows — silently. `fold_reference_sheet` now writes a defined name
`_fold_<slug>` per section with its exact row range, and `reference_sections.py` reads that.
Every consumer (verify_workbook, verify_prose, extract_artifact_data) goes through
`sheet_or_section`, which returns the sheet if it still exists and a view onto its section if
it does not, so no check had to learn where its table went.

## Eleven false sentences found by running a checker that had never run

`verify_prose.py` — the third pass, what the sheets *say* — defaulted to v11 and was not in
CI, so it had been checking a workbook that stopped shipping on 09.09. Pointed at v25 it
reported eleven findings, all also in v24. Three were the workbook's:

* The CoQ Register note said the legacy series is issued on **27.05.2026**; the rows issue on
  06.06.2026 (`--legacy-coq`, the owner's date). The note was a literal. Both register notes
  now take their day from the same value the rows do.
* An uncredited in-house reference on the tracker read `iCoA-PP_26-004, (11.04.2025) [PP]`
  with no "on file, not credited" — the register-lookup formula dropped the suffix that
  every literal reference carries. The grey fill and the STATUS count were right; the text
  was not. Four lots.

Eight were the checker's. It judged coverage by whether a reference opened with an em dash,
which is the shape of every in-house result (`— at issue —, (16.02.2026) [PP]`) — so it
uncounted identification A, B and foreign matter on every lot and read the STATUS cell as
undercounting when the cell was right. It now reads the fill, which is the tracker's
definition and `verify_workbook.py`'s. It compared the legacy day against a literal of its
own (15.05.2026) rather than the note, so it held a third copy of the date; it found the
note by its opening words, so the register's rewritten note returned "" and every check on it
passed on an empty string. Both fixed; the check is in CI.

Two more of the same shape, found on the way out. The register **Status** strings said
"issued 27.05.2026" and "issued with the legacy series on 15.05.2026" — literals again, on
rows that issue on 06.06 and 03.06; they take the series' day now, and `verify_prose` holds
every Status that names a day to the row's own issue date. And `build_delivery_package.py`'s
`STAMP` was `"2026-09-11"`, so a rebuild on the 14th overwrote the 11th's archive under the
11th's name; the archive is stamped with the build date the workbook states about itself.

## Truth check of the fold, 14.09.2026 afternoon

The owner asked for another truth check. The three gates were green; the question was what
they do not test — whether the fold and the register merge preserved everything. An
independent pass compared v25 to v26 cell for cell: every folded sheet is identical in value,
style, merged range and formula result at its place on Reference; no formula anywhere names a
folded sheet; every value the old iCoA Issuance sheet carried is on a register under the same
batch and round (its CoQ plan reference on the CoQ Register, its own row number nowhere —
that was a position, not a fact). Four things it found that the gates could not:

* **The registers never asked `strains.py`.** `apply_strain_rulings` covered Batch Coverage and
  the Delivery sheet and nothing else, so both registers printed the certificate register's
  own spelling — `Cup Junky` and `Cap Junkie` on eight lots against the Head of QC's ruling of
  07.09.2026, `GorillaGlue`, `FatBastard`, `GrapePie` unspaced. The one sheet that printed the
  ruled spelling was iCoA Issuance, and folding it away took the ruling out of the workbook
  with it. Both registers and the preliminary registers workbook now go through the rulings;
  every strain on the register is canonical, and the unruled pairs print on the Work Order.
  `strains.py` repairs a missing space only for names on its known list, which had
  `GorillaGlue` and not `CashCow` or `JellyDonutz`; both added — a space repair decides
  nothing, and Jelly Donuts / Jelly Donutz stays an unruled conflict on the Work Order.
* **One register row said "not needed".** JD012603/01 (P060362) printed `not needed — CNP
  covers A, B and foreign matter`: the note of 05.09.2026 that the ruling of 10.09.2026
  ("identification A, B and foreign matter, always") replaced. The row exists because the
  plan of 31.08.2026 schedules its certificate; the series does not carry it because the batch
  has no entry in the owner's release register, so `icoa_register.py` has no testing history
  to number — packed 23.05.2026, a CoQ planned with 21.01 % THC, and absent from the register
  it should be in. Nothing on either register says "not needed" now; a row the series does
  not carry says why, and this one says that.
* **The preliminary registers workbook said two false things** on its Read Me — built "on
  05.09.2026" (a literal; it now states the build date) and sourced from "sheets iCoA
  Issuance and Batch Dates".
* **The Read Me's version history stopped at v25**, and OI-31 still described the iCoA
  Issuance sheet. Both brought forward. **OI-32** added: the thirty Tranche 3 Farmahem
  227-K/26 potency retests on file and in no record, twenty-five prepared and not written,
  five held on batch identity — a finding that had been living in chat.

What the fold does lose, and cannot help: each folded sheet had its own frozen header row and
six had an autofilter. One sheet has one of each, so the Reference sections have neither.

## Reproducing

    python3 deliverables/qc_gap_analysis/open_items.py --md
    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=26 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=14.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026
    python3 deliverables/qc_gap_analysis/tracker/verify_workbook.py
    python3 deliverables/qc_gap_analysis/tracker/verify_prose.py

**v26 verifies with 0 findings**, the deeper pass compares **5,341 printed results** with 0
findings, the prose pass compares 430 Mikro cells with 0 findings; 36,373 recalculated cells,
0 formula errors. `coq_artifact_data.json` and every drafted certificate are byte-identical
before and after — nothing here touches a certificate.

Still not in v26: the Tranche 3 Farmahem `227-K/26` retest results. Their register write is
blocked on permission and five of the thirty are held on batch identity (OI-28).

# v27 — the Tranche 2 mycotoxin certificates, 14.09.2026

Thirty-two Farmahem reports of analysis, `220-1-М/26` … `220-32-М/26`, read directly from
the rendered pages at the owner's request and cross-checked page by page against an
independent Gemini read (32 of 32 agree); every result ND. Everything about the intake —
the reads, the placement, the two writes (`apply_220M.py` into the release register,
`instances_220M.py` into `new_instances.json`), the two definition gaps the first build
exposed, and the numbers v27 shows — is in `intake_220M_2026-09-14/README.md`.

What matters for the vocabulary: **a certificate's family label and its retest status are
one definition.** `family()` used to name the 197- series alone while `is_reanalysis()`
knew 220- too, and the tracker files a retest by the label — so the 32 certificates
reached the schedule and the registers and never the tracker. The label now derives from
`REANALYSIS_SERIES`, which also carries the 227- potency series (owner, 12.09.2026).

And one latent defect closed, with a gate for it: eight lots' in-house cells keyed another
lot's internal CoA because the at-issue placeholder names its lot in a parenthetical that
`nkey()` strips. `verify_workbook.py` check 7b fails v26 on 27 cells and passes v27.

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/apply_220M.py
    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/instances_220M.py
    python3 deliverables/qc_gap_analysis/build_coq_schedule.py
    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py
    python3 deliverables/qc_gap_analysis/open_items.py --md
    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=27 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=14.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026
    python3 deliverables/qc_gap_analysis/tracker/verify_workbook.py
    python3 deliverables/qc_gap_analysis/tracker/verify_prose.py

The first of those writes the owner's register, which this environment may not do on its
own (refused twice on 14.09.2026), so v27 was built from a copy of the tree with the two
writes applied, and the repository still carries the v26 workbook, on which the new check
7b reports the 27 cells above until the register is written and v27 built in place.

# v28 — the retest sampling dated, the retest series issued, 15.09.2026

Four rulings of 15.09.2026, and what each one is in code:

* **The retest campaigns were sampled on dates the owner set.** `sampling_dates.py` is the one
  definition: Tranche 1 on 21–24.07.2026 (Tuesday to Friday of the week 25.07 falls in,
  6/5/5/5 by certificate number; Farmahem received the samples 27/29.07), Tranche 2 on
  12–14.08.2026 (11/11/10; received 17.08), Tranche 3 on 19–21.08.2026 (10/10/10; received
  24.08). A campaign's internal certificates are all issued three days after its last sampling
  day: 27.07, 17.08, 24.08.2026. A batch's sampling day follows its certificate's running
  number, a fact the certificate carries.
* **A re-analysis certificate is never release testing.** `testing_series.rounds()` places every
  197-, 220- and 227-series certificate in a campaign round of its own, after the rounds the
  rest of the record makes; the release round may be empty. `REANALYSIS_SERIES` and
  `is_reanalysis()` moved there from `build_coq_schedule.py`, which imports them — one
  definition. Sixteen batches whose register block holds nothing but a campaign certificate
  now have a retest round, and seven Tranche 1 lots under a P-number-only block have theirs.
* **Identification A, B and foreign matter are performed on every batch, and every CoQ cites
  the internal certificate for them.** `icoa_register.py` emits a release row for every batch
  (an empty release round included) and numbers a round whose packaging date the list does
  not hold, with the testing date not stated. A campaign round is tested on the sampling day
  and issued on the campaign's day; the tracker's internal-certificate day is now the same
  arithmetic (it was "5 working days after packaging complete" there alone).
* **A reissue prints every parameter.** `build_coq_schedule.py` carries the initial
  certificate's row — result, document, date, laboratory, and its status — for every
  determination outside the retest scope (`ST_CARRIED`); the export re-cites the release
  round's internal certificate where the carried row rests on an in-house record, and a
  carried row neither dates the reissue nor lifts its 12-month floor.

And the reissue is numbered by the same rule as the release certificate: 7 days after the
last certificate it cites, never before its internal certificate, in date order with the
release series, once the retest assay, the mycotoxins and the internal certificate exist.
Tranche 1's 21 reissues take CoQ-PP_26-083 to -103 on 17.08.2026; Tranche 2 waits for its
potency certificates and Tranche 3 for its mycotoxin certificates, and the CoQ Register says
so per lot. A tracker row holding several P lots reads its campaign per lot from the series,
not from the document pool the lots share, and a reissue needs its assay and mycotoxins
from ONE campaign.

`cnp_methods.py` reads off every CNP certificate which pharmacopoeial method it reports:
DAB (Deutsches Arzneibuch 2018) on every certificate from ППК25050 (26.02.2025) to ППК26069
(11.05.2026), Ph. Eur. 3028 from ППК26110 (30.06.2026). A CoQ row citing a DAB certificate
for #3–#6 or #8 prints the DAB reference (`mth` in the export), and the Parameters sheet says
so. `receipt_dates.py` reads the date each external certificate says the laboratory
admitted the sample — 335 certificates, from the certificate texts and the page reads — and
`coq_references.py` carries it beside every cited certificate, with the sampling day, and
paints every `n/t` cell red with a list for the owner's check.

One defect found on the way: the export consulted `issuance_schedule.py` and
`icoa_register.py` on the PREVIOUS build's `coq_artifact_data.json`, so an intake numbered
and dated nothing until the build after it. It now writes a preliminary export first and
reads that.

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/apply_220M.py
    python3 deliverables/qc_gap_analysis/intake_220M_2026-09-14/instances_220M.py
    python3 deliverables/qc_gap_analysis/intake_227K_2026-09-15/apply_227K.py
    python3 deliverables/qc_gap_analysis/intake_227K_2026-09-15/instances_227K.py
    python3 deliverables/qc_gap_analysis/cnp_methods.py
    python3 deliverables/qc_gap_analysis/receipt_dates.py
    python3 deliverables/qc_gap_analysis/build_coq_schedule.py
    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py
    python3 deliverables/qc_gap_analysis/icoa_register.py --csv
    python3 deliverables/qc_gap_analysis/issuance_schedule.py --csv
    python3 deliverables/qc_gap_analysis/open_items.py --md
    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=28 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=15.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026
    python3 deliverables/qc_gap_analysis/tracker/extract_coq_register.py \
        deliverables/qc_gap_analysis/tracker/CoQ_Analysis_Master_v28.xlsx
    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py      # the register codes
    python3 deliverables/qc_gap_analysis/coq_references.py --out deliverables/qc_gap_analysis/intake_227K_2026-09-15/CoQ_references_v28
    python3 deliverables/qc_gap_analysis/tracker/verify_workbook.py
    python3 deliverables/qc_gap_analysis/tracker/verify_prose.py

# v29 — the references table inside the workbook, 15.09.2026

The owner asked for the references table and its n/t list "inside the v28 workbook". A
workbook with two more sections is a new build, so it is v29; nothing else changed. The
`CoQ References` tab is `coq_references.py` run inside the build (`build_rows` /
`fill_sheet`), with the CoQ code taken from the `CoQ Register` tab of the same workbook —
keyed to its rows — rather than from the export's copy of an earlier register, so the two
tabs cannot disagree. Every n/t cell is red, and `Not Tested Review` is a section of Reference
listing them (certificate, batch, series, determination, the cell as printed). The
`Potency Grades` tab (owner, 15.09.2026: "include this information inside the workbook")
renders `potency_grades_2026-09-15.csv`, which `potency_grades.py` parses off the Head of
QC's potency specification of 15.09.2026 (`potency_grades_2026-09-15/`): one row per strain
and grade — nominal, tolerance, specification window — with the measured results each page
rests on. The
standalone files `intake_227K_2026-09-15/CoQ_references_v29.{csv,md,xlsx}` and
`CoQ_references_v29_nt.md` are the same table written by the same code from the command
line, after `extract_coq_register.py` has lifted the v29 register into the export.

    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=29 --icoa --cells \
        --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=15.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026

Two more columns groups on the `CoQ Register` in the same build (owner, 15.09.2026): a reissue
names the **initial certificate it supersedes** by the register's own code, looked up by Key
so it follows a renumbering (n/a on an initial certificate); and every certificate carries
its **potency grading** — the Total THC result it prints and the certificate it comes from,
the grade of the potency specification of 15.09.2026 whose window it falls in (nominal ±
tolerance, grade numeral from the highest nominal down), and the product code
`{ABBR}_THC{nominal} : CBD1` and specification document code `QCSP_001_{ABBR}-{numeral}_v.NN`
generated from it. `potency_grading.py` is the one definition: the strain from the batch
code's letters (else the strain name through the rulings), the window as printed, and the
version rule — v.01 cited where a specification with that product code is issued, "to issue"
where none is, v.02 where the numeral is issued for another nominal, because the
specification of 15.09.2026 changed the grade set of several strains. A result in no window
is graded to the nearest window and the Grading note says so.

**Correction the same day (owner, 15.09.2026): every grade, nominal, tolerance and range already in
the issued specifications, the issue plan and the certificates is old and potentially wrong; the
potency specification of 15.09.2026 is used exactly, everywhere.** `build_coq_schedule.py` no
longer takes the Total THC criterion, grade, product code or specification document code from
the issue plan or the issued QCSP 001 v.01: each certificate's criterion is the window its own
Total THC result falls in (the release result on the release certificate, the re-analysis on the
reissue), and the product code and the specification code are generated from it. The v.01
document is cited only where it carries the same product code and the same window; a numeral
issued with any other content takes v.02 and the status says what it supersedes; a numeral never
issued takes v.01 (to issue). The issued v.01 document is recorded beside the generated code
(`issued_spec`, `spec_conflict`), not used. The specification attributes — phenotype, chemotype,
processing, packaging — are the strain's and are read off any issued specification of the same
strain. The desk artifact and the 22 draft certificates were recompiled from the new export;
v29 was rebuilt in place.
