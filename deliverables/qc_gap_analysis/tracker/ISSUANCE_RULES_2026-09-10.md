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
