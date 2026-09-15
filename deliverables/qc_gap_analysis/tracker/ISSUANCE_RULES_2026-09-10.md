# Ordering the certificates — the owner's rulings of 10.09.2026

Two modules carry these, both self-testing:
`testing_series.py` (which testing is release and which is a retest) and
`issuance_schedule.py` (what date each certificate carries).

## 1 · Release testing and retests are decided by the record, not the numbering

> "the first value of a parameter obtained would be counted as an initial quality
> control testing, and every other point of testing for any of the parameters from
> a batch will be considered as a retest."

The desk had been reading the **series a certificate's number belongs to** —
`197-` and `220-` meant post-release, everything else meant release. That is a
proxy, and it failed where the numbering did: the owner ruled on the same day that
`220-…-K/26` is re-analysis too, which the desk did not know. `is_reanalysis` is
corrected, but the classification no longer rests on it.

A result's round is now **its position in its own parameter's history**. This
matters more than it sounds: a testing period is not a single date. One release
campaign has the cannabinoids certified on one day, microbiology on another and the
metals on a third, so reading each distinct date as a period gave one batch six
certificates where it has one. Ties are release testing — a laboratory splitting a
day's work across two documents is not a second testing period.

**80 batches → 106 certificates of quality**: 80 release and 26 retests. 63 batches
were tested once and carry a release certificate only, which is the owner's own
description — *"comes a moment when production batches do not have a retest, and
the only record is the initial testing record"* — falling out of the data rather
than being written down anywhere.

| round | certificates |
| --- | ---: |
| initial release | 80 |
| retest 1 | 17 |
| retest 2 | 3 |
| retest 3 | 3 |
| retest 4 | 2 |
| retest 5 | 1 |

## 2 · The dates

| | rule |
| --- | --- |
| specification SOP | approved **01.06.2026** — nothing controlled by it is dated earlier |
| internal CoA | tested start = end = the packaging date (release) or the round's sampling date (retest); **issued that day, or 03.06.2026 if that day is before the SOP** |
| certificate of quality | **5–10 days after the last external certificate it cites**, and never before the internal CoA it references; anything landing before the SOP is issued with the backlog on **06.06.2026** |

`LAG_DAYS = 7`, because the owner gave a range and a register cannot hold one. It
is the middle of 5–10 and one constant to change.

**57 certificates of quality issue on the blanket date 06.06.2026** and **49
chronologically after it**; **68 internal CoAs issue on 03.06.2026** and **38
later**. The whole register is `issuance_schedule_2026-09-10.csv`.

This settles the conflict raised earlier in the day. Five batches would have
carried a certificate dated 06.06.2026 citing laboratory certificates issued weeks
after it — `ППК26111/113/114` on 30.06.2026 and `220-16-K/26` / `220-29-K/26` on
25–26.08.2026. The owner's answer was the rule itself: *"how can a certificate of
quality be dated on a date that is earlier than the last certificate of analysis
obtained from external lab for that batch."* Those five now issue in July and
September, after their own evidence.

## 3 · One internal CoA per testing round

Identification A, Identification B and foreign matter go on **one** internal
certificate per round, tested start = end as above. Its document code and issue
date are referenced in that round's certificate of quality, against those three
parameters.

## 3a · What the rule caught — 18 back-dated result cells

Applying the rule to the deliverables, rather than only computing it, found that
**post-release re-analysis was being printed on release certificates**. The
owner's 09.09 pass fills any cell the register block does not answer, and that
path bypassed `pick` — so while `pick` refused to let a release certificate cite
the re-analysis, the pass handed it one anyway.

Six lots, 18 result cells, including **four release assays — the figure that
prints in the banner**:

| lot | was printing | from | issued |
| --- | ---: | --- | --- |
| FB012602 | 24.09 % | 197-7-K-26 | 07.08.2026 |
| JD012603/01 | 21.01 % | 220-16-K/26 | 25.08.2026 |
| CC012603 | 14.76 % | 220-29-K/26 | 26.08.2026 |
| SCR012603 | 17.84 % | 197-21-K-26 | 07.08.2026 |

The remaining cells are Total CBD, Total CBN and Identification C on the same
lots, plus Total CBN on HPA1024 and OPM1024. All of them belong to the retest
that rests on them; where that leaves the release cell blank, the parameter was
not determined at release.

**FB012602's 24.09 % was one of the nineteen assays recorded as sitting outside
its own band.** It was never a release value, so that finding does not apply to
its release certificate.

This is also why ruling the `220-` series a re-analysis changed nothing on the
day it was made: `is_reanalysis` only ever *added* candidates to the retest
certificate, and the release certificate was being filled down a path that never
consulted it.

## 4 · Still to build

- **In-house results never appear on a certificate of quality.** They may be
  carried on an internal CoA, which must state the status of the method used. **49
  determinations across the release certificates cite an in-house document today**
  and each has to move behind an internal CoA.
- **Identification C is cited from the document that carries the qualitative and
  quantitative determination of cannabinoids**, whenever the Center for Natural
  Products did not perform Identification C explicitly in that testing period —
  same document code, same issue date. For the retest rounds that document is
  Farmahem's.
- **The internal CoA register is standing** — every internal certificate that
  exists or ever will, not only the ones these batches need.
- **Two specification options have never been exercised** and the desk should say
  so rather than leave it implied: the CUMCS-equivalency pesticide panel (every
  batch to date is tested to the Ph. Eur. panel) and the expanded microbiological
  panel (*Pseudomonas aeruginosa*, *Staphylococcus aureus*).
- **The monograph changed under these batches.** The Center for Natural Products
  first used the German pharmacopoeia method for the cannabinoids with loss on
  drying < 10 %; after the Ph. Eur. cannabis monograph 3028 it uses the Ph. Eur.
  method and ≤ 12 %. Both eras are on file and the certificates should attribute
  the method each lot was actually tested by.

## 5 · One ruling still open

The internal CoA's issue date was given twice and differently — *"date of issuance
of the internal certificate of analysis on 03.06.2026"*, then *"with issuing
date… with the date of packaging"*. Implemented as **the later of the two**: the
testing date where that falls after the SOP, and 03.06.2026 for everything before
it, so no controlled document predates the SOP that governs it. One constant
changes it if that reading is wrong.

---

# The internal certificates of analysis — built 10.09.2026

`icoa_register.py`. The owner's rulings, and what each one does:

* **The register encompasses every internal certificate that exists or ever
  will**, not only what the drafted lots need. **106 certificates over 80
  batches** — one per testing round, which is exactly the number of certificates
  of quality, because a round that needs a certificate of quality needs the
  internal certificate behind it.
* **One certificate per round, covering all the missing parameters.** Two things
  and nothing else go on it: Identification A, Identification B and foreign
  matter, always — the owner states these are performed in house on the packaging
  date for the release round and the sampling date for a retest — plus any
  determination whose only result in that round is an in-house record. A
  determination with no result at all is covered by nothing; an internal
  certificate can only certify what was tested.
* **In-house results are never referenced on a certificate of quality.** They sit
  behind the internal certificate, which the certificate of quality cites. **Four
  certificates** carry an in-house determination beyond identity and foreign
  matter — HPA1024 and OPM1024 carry thirteen each.
* **The testing date is the first day of packaging.** `Batch Dates` in the
  workbook carries `Packaging from` and `Packaging to` for 87 batches — including
  those with no P number, where the release record has a date only for the 48
  lots that have one. **26 batches were packaged over more than one day**, and
  the owner ruled on 11.09.2026 that the certificate takes the **first** of those
  dates: start and end of testing are that one day.
  `tracker/extract_batch_dates.py` lifts the sheet to
  `batch_dates_2026-09-10.csv`.
* **Document codes follow the order of issuing**: `iCoA-PP_26-001` …
  `iCoA-PP_26-106`, ordered by issue date, then by the date the work was done,
  then by batch. The backlog shares one issue date, so within it the order is the
  order the batches were packaged — the same order the certificate-of-quality
  series is numbered in. **71 issue on 03.06.2026 and 28 on eight later dates**, the
  last on 10.08.2026. **Seven take no number**: without a packaging date on file
  they cannot be issued, and a code in an issue-ordered series says a certificate
  was — BSS1024_01, GG012601, JD012601, OPM1024_01, P160012, P160022 and P160032
  are listed with that note instead. The series runs `iCoA-PP_26-001` …
  `iCoA-PP_26-099`.

## What it did to the certificates

Section 03 of every sheet now names the internal certificate by code and issue
date against the parameters it carries:

> Purely Plant — QC Department · In-house QC Laboratory · MK GMP Certified
> **iCoA-PP_26-027, 03.06.2026** · 1, 2, 7

**266 determinations now cite an internal certificate** and **150 results are
unblocked** by it. `cell_resolution` rule 1 refused those because the certificate
carrying them had not been issued; the owner has now issued, dated and coded it,
so the premise of the refusal is gone — for exactly the determinations that
certificate covers and for no others.

**147 blank printed lines → 87.** Seventeen of the 22 drafts are down to **two**,
and both are structural: Aflatoxin B₁ and Ochratoxin A, because the laboratory
certificate reports the aflatoxin sum and not the single analytes. No
transcription closes those.

## The page paid for it

The extra Section 03 row put four certificates past the footer. The cross-
reference rows gave up their cell padding, the sentence-length Identification C
result went to 6.5 px, and the footnote under the results table lost 7 px of its
own padding. All 22 clear the footer again, the worst by 5 px.

One thing was tried and reverted, and it is worth writing down: overriding
`.approval-grid { margin-top: auto }` looked like free space. It is not — that
`auto` is what pins the signature block to the bottom edge of the sheet whatever
the certificate holds. Removing it did nothing for the one crowded certificate
and would have left the other 21 with their signatures floating mid-page.

## A correction to the first build of the register

The register was keyed on the **raw batch spelling** when it looked up the
packaging date, and found one for 29 of 80 batches. The rest fell back to the
round's last external date — which put **25 internal certificates' testing date
on 10.08.2026, the Farmahem re-analysis date**, on batches packaged a year
earlier. It is the same defect as the one fixed in the exporter an hour before,
in a second place, and it is the reason `batch_id.batch_key` exists.

Three things fixed it, and the second is the one that matters:

1. The lookup goes through `batch_key`, never by string — 29 → 39.
2. `Batch Dates` replaced the release record as the source. The release record
   carries a packaging date only for the 48 lots that have a P number; the sheet
   carries a packaging date for 87 batches — 39 → 99.
3. Both the cultivation number and the P number are indexed, because the register
   keys some entries by one and some by the other — 92 → 99.

What remains is seven batches with no packaging date anywhere on file. They are
listed, noted and unnumbered rather than given an invented date.

---

# v22 — the rulings written into the workbook, 11.09.2026

Owner: *"the workbook data is the correct one regarding the packaging dates and
manufacturing dates … update that workbook and all the sheets inside with the
updated information regarding everything we configure here, especially regarding
the issue date of the certificate of analysis."*

    python3 deliverables/qc_gap_analysis/tracker/build_tracker_v8.py \
        --v9 --version=22 --icoa --cells --mikro=CoQ_Analysis_Master_v13.xlsx \
        --build-date=11.09.2026 --legacy-icoa=03.06.2026 --legacy-coq=06.06.2026

The workbook computes its registers as **live Excel formulas**, so the rulings had
to go into the formulas, not into a column of pasted values. Four changes:

| | was | is |
| --- | --- | --- |
| internal CoA issue | `15.05.2026` for a legacy row, else packaging **complete** + 5 working days | **the first day of packaging**, or **03.06.2026** where that is earlier |
| certificate rule date | `27.05.2026` floor, latest eCoA + 7 working days | **06.06.2026** floor, latest eCoA + 7 days |
| certificate issue | rule date, the internal CoA, and packaging complete rolled forward | rule date, the internal CoA, and **packaging complete** |
| the two floors | literals in three formulas | `--legacy-icoa` / `--legacy-coq`, one constant each |

The first line is the substantive one and it was wrong twice over: the workbook
dated the internal certificate from the day packaging **finished**, plus five
working days. The ruling is the day packaging **started**, with no lag.

## Two things the rebuild caught

**A certificate of quality dated before its lot was packed.** Removing the
packaging term from the issue formula — it looked redundant once the internal
certificate carried the packaging date — dated **P060482 / JD022601** on
07.07.2026 against a lot still being packed on 05.08.2026. The term is restored in
the formula *and* in `issuance_schedule.coq_issue`, which had the same hole and
which is what the certificates actually print. That lot now issues **12.08.2026**:
seven days after its own internal certificate, which is dated at packaging.

**06.06.2026 is a Saturday.** The builder refused it — `assert _d.weekday() < 5`,
the desk's own convention that a controlled document is issued on a working day.
That is a convention and not a rule from anywhere above it, so the owner's date
outranks it: the assertion now admits the date and the sheet carries a flag
saying it is a Saturday and was chosen deliberately. **57 certificates of quality
are dated on it.**

## And one in the checker

`verify_workbook.py` pinned `15.05.2026` and `27.05.2026` as literals, so a ruling
lived in two files and one of them was always the stale one. It now reads the
legacy day off the workbook and checks that the legacy rows **agree on one day**,
which is the stronger statement anyway.

**v22 verifies with 0 findings**, and the deeper pass compares 5,482 printed
results against the certificate records with 0 findings.

---

# A code allocated before its date — the owner's ruling of 15.09.2026 (evening)

The standing rule since 31.08.2026 was that a CoQ number is copied from the
issuance record at issue and never computed in advance, and the CoQ Register
numbered only what it could issue: after v30 the Tranche 3 reissues stood without
a code because their mycotoxin certificates (227-М/26) do not exist yet. The
owner's ruling:

> "for tranche three there are still missing retest parameter results, so it
> cannot be issued. But also because all of the retest parameters are performed
> in Farmahem, they will all come in one date, so practically you can even now
> allocate the certificates of quality document codes for tranche three batches.
> And after them, you should list any of the production batches that are maybe
> still under testing, under production, or that are not even included in
> tranche one and two and three."

What it is in the register (`tracker/build_tracker_v8.py`):

* **A Tranche 3 reissue whose release certificate is numbered takes its code
  now**, after the last Tranche 2 reissue, in the order the series gives rows of
  one date (cultivation batch, then P lot — the same key the Tranche 1 and 2
  reissues of one day are ordered by). Its `Issuable` reads **`allocated`**, not
  `yes`; `No.` counts it; the **planned date is the owner's** — the analyses
  complete within ten days, likely by Friday 18.09.2026, and all Tranche 3
  certificates issue on one day, *"let's say Monday next week"*: **21.09.2026**,
  passed to the build as `--t3-issue=21.09.2026` and **provisional** until the
  227-М certificates exist (the rule-date cell says so). The codes stay
  chronological: every Tranche 3 date is after the last Tranche 2 date. Nothing
  else about the row is computed in advance: the certificate it supersedes, the
  internal certificate it cites and the potency grading are the row's own.
* **The date is not a code.** The compiled certificate prints the allocated code
  in its header (the register's code, as since 15.09.2026) and is **not drafted**
  until the register dates it: `live_instrument/reissue_scope.py` marks a
  numbered-but-undated reissue not draftable and says so.
* **A reissue is never numbered before the certificate it supersedes.** The two
  Tranche 3 lots whose release CoQ the register withholds (GG012601＊ and
  JD012601＊ — no internal certificate, OI-28) keep their reissue unallocated
  with it.
* **The retest programme is the QP's, not universal.** *"For all the production
  batches that are not listed into tranche one, two, or three, those are not
  subject to a retest as of yet … They are not subject for sale, so the QP did
  not request retest for them. Only Tranche 1, 2 or 3 production batches are for
  sale and thus QP asked for retest and reissue."* `build_coq_schedule.py` gives a
  reissue only to a lot whose register block holds a campaign re-analysis
  certificate (197-, 220-, 227- series); the six batches outside every tranche
  that v30 carried with a predicted reissue — JD022601 (P060482), FB032601
  (P060452), GG032601 (P060462), P160012, P160022, P160032 — have their release
  certificate and no retest row on either register.
* **After the numbered and the allocated rows** the register lists the batches
  the tranches do not cover — under production, under testing, or on no tranche
  list — lot by lot, with the reason each is not yet issuable. None of them can
  take a code before its external results and its packaging exist (owner,
  15.09.2026: *"no CoQ code could be issued yet"*).

`verify_workbook.py` holds the sheet to it: an `allocated` row has a number and
is a Tranche 3 reissue; the allocated rows share one planned date (or none) and
it is not before any date the register has issued on; a number on any other row
that is not `yes` is a finding, as before.
