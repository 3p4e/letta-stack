# The sweep of 21.09.2026, and the signed print that follows it

## What the owner ruled

> *"There will be no empty space in the certificate of quality nor the certificate of
> analysis — all parameter results must be filled in, especially in the certificate of
> quality. The only exclusion is from the initial certificates of quality for the
> parameter mycotoxins: only one sub-parameter mycotoxin has been tested; the other two —
> the complete panel of mycotoxins has been tested during the recent [campaign] for
> reissue for those CoQs."*

Two further decisions of the same day, both to keep what the desk has: the internal
certificate's signatories stay Cekikj → Romevska Cvetkovski → Nikolov, and the document
codes stay in the short `CoQ-PP_26-013` form. Both are recorded as divergences from the
`FIN_SP-COA-COQ` design system rather than changed (OI-61, OI-62).

## The reading, and one correction the desk made against itself

Fifteen documents went through the two-read gate in `intake_sweep_2026-09-21/`. Ten were
read by two vendors. For the other five, Google's free tier retired a key mid-run — one
key came back *"reported as leaked"* — so the desk read the pages itself at 300 dpi, as
it did on 16.09 and 18.09.

That desk pass was then found wanting, by the desk: its crops covered the parameter table
and the letter line but **not** the lab-number line or the signature block, and it had
filled `cert_code`, `batch_canonical` and `date_of_issue` from the **file name**. A file
name is not a page. The header and footer were re-cut and read, and every one of those
fields is now a reading:

| document | certificate | batch | issued | receipt line |
|---|---|---|---|---|
| 403/0786/26 | 403/0786/26 | SCR022601 | 24.06.2026 | 18.06.2026 |
| 408/0791/26 | 408/0791/26 | FB012603 | 24.06.2026 | 18.06.2026 |
| 434/0848/26 | 434/0848/26 | FB032601 | 10.07.2026 | 02.07.2026 |
| 475/0927/26 | 475/0927/26 | **P050022** | 04.08.2026 | 28.07.2026 |
| 76/0119/26 | 76/0119/26 | GRC102501 | 09.02.2026 | **02.02.2025** |

One field changed on the reading: `475/0927/26` prints **`Серија: P050022`**, not the
cultivation batch `GP0824-02` the file name carries. The rest confirmed what the first
pass had assumed — which is not the same as having read it, and is why it was re-read.

**The gate now holds nothing**: 15 documents read twice, 98 values agreed by both
readers, 6 settled by a third read with its crop region recorded, 0 held.

## Two defects found on the laboratory's own pages

Neither is the desk's to repair, and neither is guessed at.

* **OI-64 · `434/0848/26`** prints *Примерок за тестирање: Сув цвет од медицински канабис
  **Gorilla Glue**, 33,34 g* and, two lines below, *Серија: **FB032601***. FB is this
  record's Fat Bastard prefix and GG its Gorilla Glue one, so the page names two different
  lots, both of which exist. `433/0847/26` — the preceding number, same day — names Fat
  Bastard, carries FB032601 and already fills #9.1–#9.5 on CoQ-PP_26-081, with different
  counts, so the two reports are two samples. CoQ-PP_26-082, the Gorilla Glue lot, is the
  one of the pair with an empty panel. Nothing is applied from this page until the
  Institute says which lot it certifies.
* **The receipt year**, same letter: `75/0118/26` and `76/0119/26` both print *Дата на
  прием: 02.02.**2025** год.* while their laboratory numbers end `/26` and both are signed
  **09.02.2026**. The year is out by one on both pages of that pair.

## The signed print

Both fleets were rebuilt with `PP_SIGNATURES=1` and printed to vector PDF — 172
certificates of quality and 172 internal certificates, initial and retest, each one A4
page. The committed HTML stays the **unsigned** set, as it has since 17.09; the signature
is a build switch, not an edit to a settled document.

## Verification

| check | result |
|---|---|
| `tracker/verify_workbook.py` | 5,018 printed results compared · **0 findings** |
| `tracker/verify_prose.py` | **0 findings** |
| `verify_panels.py` | certificates printing a partial panel: **0** |
| `verify_icoa_citations.py --html` | **344/344** citations name their own lot |
| `coq_check.js` | 2 hard findings, both the pre-existing OPM1024 `"< 10² > 10³ CFU/g"` |
| Batch Coverage ○ | **0** |
| internal certificates cited by a CoQ | **172 of 172**, 0 printed uncited |

## What still carries a marker, and on which certificate

The owner's declared exception — #10.1 aflatoxin B1 and #10.3 ochratoxin A on the
**initial** certificates, 176 cells, the panel carried by the reissue campaign — is
excluded from this table. #9.6 *P. aeruginosa* and #9.7 *S. aureus* are not rows of
the printed skeleton and print nothing either way; they are the next task.

**272 cells over 38 certificates**, and the sweep of today closed ten of them: CoQ-PP_26-079 (FB012603, Fat Bastard) from `408/0791/26` and CoQ-PP_26-080 (SCR022601, Scrambler) from `403/0786/26`, two complete microbiology panels that had printed *not tested* while the pages sat on Drive.

| certificate | lot | P lot | strain | round | cells | determinations |
|---|---|---|---|---|---:|---|
| CoQ-PP_26-084 | JD042601 | P060492 | Jelly Donuts | initial | 16 | #3 #4 #5 #6 #8 #9.1 #9.2 #9.3 #9.4 #9.5 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-167 | FB042601 | — | Fat Bastard | initial | 16 | #3 #4 #5 #6 #8 #9.1 #9.2 #9.3 #9.4 #9.5 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-166 | CC042601 | — | Cash Cow | initial | 16 | #3 #4 #5 #6 #8 #9.1 #9.2 #9.3 #9.4 #9.5 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-021 | BSS1024_01/2 | P050142 | Blue Sunset Sherbet | initial | 16 | #3 #4 #5 #6 #8 #9.1 #9.2 #9.3 #9.4 #9.5 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-050 | GRC102501/1 | P060142 | Grapes And Cream | initial | 16 | #3 #4 #5 #6 #8 #9.1 #9.2 #9.3 #9.4 #9.5 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-071 | JD012603/01 | P060362 | Jelly Donuts | initial | 11 | #3 #4 #5 #6 #8 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-070 | FB012602 | P060352 | Fat Bastard | initial | 11 | #3 #4 #5 #6 #8 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-072 | CC012603 | P060372 | Cash Cow | initial | 11 | #3 #4 #5 #6 #8 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-074 | SCR012603 | P060382 | Scrambler | initial | 11 | #3 #4 #5 #6 #8 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-068 | P060332 | — | Cash Cow | initial | 11 | #3 #4 #5 #6 #8 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-073 | SCR012601 | P060342 | Scrambler | initial | 11 | #3 #4 #5 #6 #8 #10.2 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-125 | JD042601 | P060492 | Jelly Donuts | retest | 11 | #8 #9.1 #9.2 #9.3 #9.4 #9.5 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-172 | FB042601 | — | Fat Bastard | retest | 11 | #8 #9.1 #9.2 #9.3 #9.4 #9.5 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-171 | CC042601 | — | Cash Cow | retest | 11 | #8 #9.1 #9.2 #9.3 #9.4 #9.5 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-082 | GG032601 | — | Gorilla Glue | initial | 9 | #9.1 #9.2 #9.3 #9.4 #9.5 #11.1 #11.2 #11.3 #11.4 |
| CoQ-PP_26-122 | JD012603/01 | P060362 | Jelly Donuts | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-091 | FB012602 | P060352 | Fat Bastard | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-108 | CC012603 | P060372 | Cash Cow | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-105 | SCR012603 | P060382 | Scrambler | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-087 | P060332 | — | Cash Cow | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-138 | BSS1024_01/2 | P050142 | Blue Sunset Sherbet | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-160 | SCR012601 | P060342 | Scrambler | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-152 | GRC102501/1 | P060142 | Grapes And Cream | retest | 6 | #8 #11.1 #11.2 #11.3 #11.4 #12 |
| CoQ-PP_26-052 | SJ102501 | — | Sleepy Joe | initial | 5 | #10.2 #11.1 #11.2 #11.3 #11.4 |
| CoQ-PP_26-046 | WED102501 | P060102 | Wedding Cake | initial | 5 | #9.1 #9.2 #9.3 #9.4 #9.5 |
| CoQ-PP_26-004 | GG1024 | GG1024 | Gorilla Glue | initial | 4 | #3 #4 #5 #6 |
| CoQ-PP_26-162 | SJ102501 | — | Sleepy Joe | retest | 4 | #11.1 #11.2 #11.3 #11.4 |
| CoQ-PP_26-005 | HPA1024 | HPA1024 | High Pro Amnesia | initial | 3 | #3 #6 #8 |
| CoQ-PP_26-006 | OPM1024 | OPM1024 | Orange Punch Mimosa | initial | 3 | #3 #6 #8 |
| CoQ-PP_26-025 | BSS052501 | P050192 | Blue Sunset Sherbet | initial | 3 | #3 #6 #10.2 |
| CoQ-PP_26-026 | GP062501 | P050202 | Grape Pie | initial | 2 | #3 #6 |
| CoQ-PP_26-047 | PUM102501 | P060112 | Pure Michigen | initial | 1 | #4 |
| CoQ-PP_26-009 | MB0824_04 | P050032 | Motor Breath | initial | 1 | #6 |
| CoQ-PP_26-019 | OPM052501 | P050132 | Orange Punch Mimosa | initial | 1 | #6 |
| CoQ-PP_26-031 | PM072501 | P050272 | Permanent Marker | initial | 1 | #6 |
| CoQ-PP_26-058 | OPM112501 | — | Orange Punch Mimosa | initial | 1 | #6 |
| CoQ-PP_26-097 | HPA1024 | HPA1024 | High Pro Amnesia | retest | 1 | #8 |
| CoQ-PP_26-101 | OPM1024 | OPM1024 | Orange Punch Mimosa | retest | 1 | #8 |

Two of these rows are questions already put to the laboratory rather than gaps in testing: **CoQ-PP_26-046** (WED102501) waits on OI-63 and **CoQ-PP_26-082** (GG032601) on OI-64. The rest are lots for which no external certificate exists in any record the desk holds — the residue of OI-42 and OI-60.
