# Drafting the Tranche 1 and Tranche 2 certificates — 10.09.2026

## What was asked

Whether every placeholder a Certificate of Quality needs is held, and if so
whether the Tranche 1 and Tranche 2 sets can be drafted.

## The short answer

The **header** of the certificate can be filled for every lot in scope. The
**results table** cannot be filled for any of them. Twenty-two drafts exist and
are in `../drafts/`; not one is complete, and the missing lines are named per
lot in `../drafts/coq_draft_gaps.csv`.

**Revised 10.09.2026**, after the owner's v20 workbook was reconciled into the
desk (`V20_RECONCILIATION_2026-09-10.md`). The drafts were recompiled from the
reconciled record: **168 blank printed lines became 147**, Total CBN and the
pesticide panel closed entirely, and the reason the identity determinations are
blank turned out to be worse than the one given below when this note was first
written. Both corrections are carried through in the two sections that follow.

## Scope — 22 of the 50 batches delivered in Tranches 1 and 2

A CoQ is issued per **production (P) lot**, not per delivered cultivation batch,
so the delivery list had to be resolved to P lots first. The scope is recorded
batch by batch, with the reason for every exclusion, in
`coq_draft_scope_2026-09-10.csv`.

| | Tranche 1 | Tranche 2 |
| --- | --- | --- |
| batches delivered | 21 | 29 |
| clean on the 09.09 readiness assessment | 14 | 9 |
| drafted | **13** | **9** |

The one clean lot that could not be drafted is **CJ062501/2 · P050212** — see
finding 3.

The readiness assessment used is the `CoQ Readiness 09.09` sheet of
`CoQ_Analysis_Master_v20.xlsx`, which recomputed coverage against the full
387-certificate `eCoA_DATABASE`. It is not the same answer as the
`Delivery T1–T3` sheet in that same workbook, which is a v13-era sheet that was
never recomputed: the two disagree on **14 of the 50 batches** — 11 the delivery
sheet calls ready and the readiness sheet blocks (mostly on the 25/26.08.2026
Farmahem retest), and 3 the delivery sheet calls short which the 09.09
certificates have since covered (GG012603, J31102501, KC102501). The newer sheet
was used, and the delta is carried in the scope file so the choice is auditable.

## Finding 1 — numbered was being printed as issued *(fixed)*

`fillCoq()` decided draft-or-final on `c.issued`. That flag means the lot carries
a CoQ **number** in the owner's issuance plan — the desk's own tail line calls
those "numbered", against "predicted", and the register sheet heads the column
"Issue date (planned)". Nothing in the baseline has ever been issued: all 61
numbered CoQs carry an issue date of the form `≥ 11.05.2026`, the SOP floor.

The header then printed that floor as a definite date by stripping the `≥`, and
because the document was not a draft it also ticked **CONFORMS TO SPECIFICATION**,
dated both signature lines and carried no DRAFT watermark. Every certificate the
desk could print for a numbered lot came out looking issued and approved while
six to seventeen of its result lines were blank.

Fixed in `live_instrument/script.js`: a document is a draft unless the desk holds
an actual issuance record (`deskIssued`, written from `OV.issue` when a number and
date are entered on the desk). `docIssued()` now gates the rendering, the document
title and the file name. `c.issued` keeps its meaning — numbered — everywhere it
is used as a count or a filter.

## Finding 2 — 72 printed results run off the sheet *(owner's decision)*

`table.results` is `table-layout:fixed` and `.r-val` is `white-space:nowrap`, so a
result wider than its column does not wrap. The result column is the last one, so
what it overflows into is the page margin and then the edge of the paper.
Measured on the compiled pages at A4 width, 76 result lines across the 22 drafts
end past the edge of the sheet:

- `Conforms | Соодветствува` — 48 px past the edge, on 22 lines;
- `Conforms — cannabinoids identified and quantified by HPLC | Соодветствува …`
  — **518 px** past the edge, on 3 lines (determination 3). The same value is
  recorded on 35 lots in all;
- `Одговара (absent)`, `Odgovara (Absent)`, `Н.д. (not detected)` and the counted
  microbiology ranges — 11 to 58 px, on the remainder.

This is the same class of decision the owner already took on 31.08.2026, when the
identification criterion was compacted to one line because a three-line criterion
pushed the signature block off the page. It is not for the desk to shorten a
verbatim result, so nothing was changed: either the result column is allowed to
wrap (the row grows, and the signature block has to be re-measured), or the
recorded results are shortened at source. Every affected line is listed in
`../drafts/coq_draft_gaps.csv`.

## Finding 3 — CJ062501/2 is clean and undraftable

The readiness sheet lists **CJ062501/2 · P050212** as clean. The desk cannot draft
it: it holds the lot as `CJ062501-2` with **no P number**, as a *predicted* initial
release, and spells the strain **"Cap Junkie"** — a third spelling, against the
Head of QC's ruling of 07.09.2026 that the correct wording is **Cap Junky**. Its
sister lot `CJ062501/1 · P050222` is held correctly. Until P050212 is attached to
the record and the spelling corrected, this lot has no certificate to draft.

## What is still missing before any of these can be signed

**147 blank printed lines across 22 drafts**, after the 09.09 evidence was
absorbed. By determination:

| line | blank on | why |
| --- | --- | --- |
| #1 Identification A, appearance | 21 of 22 | **the iCoA that carries it has not been issued** — see below |
| #2 Identification B, microscopy | 21 of 22 | same, and the microscopy was never performed |
| #7 Foreign matter | 21 of 22 | same, and no percentage was ever printed |
| #10.1 Aflatoxin B₁ · #10.3 Ochratoxin A | 22 of 22 | the certificate reports the aflatoxin sum, not the single analytes |
| #9.1–9.5, #10.2, #11.1–11.4 | 4 of 22 | GG012603, J31102501, JD112501 and KC102501 — the 09.09 pass holds these as an unlabelled list of analyte values, and three lots prove the order cannot be assumed |

**Eighteen of the 22 drafts now carry exactly five blank lines**, and all five are
in the first two rows of that table.

Two classes closed when the 09.09 pass was absorbed and are gone from the list:
**#6 Total CBN**, which was blank on 17 of 22, and **#12 pesticide residues**.
Sixty-nine result cells across the whole schedule now come from that pass, and
nothing the desk already held was overwritten.

### Why the identity determinations are blank — the first version of this note was wrong

It said the results "live on the in-house iCoA and were never transcribed". They
do live there, and transcription is not the problem. **118 of the 600 cells of
Tranches 1 and 2 cite an in-house `iCoA-PP_26-nnn` whose issue date is PLANNED**,
on 40 of the 50 batches: the certificate has not been issued, so there is nothing
to cite. And of the five in-house documents that do exist, appearance is the
single word "Confirms" with no description, **foreign matter is "Confirms" with
no percentage printed** against a gravimetric < 2.0 % specification (Ph. Eur.
2.8.2; EudraLex Vol. 4 Ch. 6 §6.7 requires the result), and **microscopy was not
performed on any of them**. Three further documents carry no document code at all
(EudraLex Vol. 4 Ch. 4 §4.9) and this build refuses to cite them.

Issuing the iCoAs is necessary and not sufficient: the microscopy has to be done
and the foreign-matter percentage has to be printed.

## What still has to be ruled before these are printed

Both of these print on the face of the certificate.

**Strain name.** Six of the 22 carry a name the register spells two ways and
rules neither: PM092501 (Permanent Marker / Permanent Market), WC082501 (Wedding
Crusher / Wedding Crasher), JD112501 (Jelly Donuts / Jelly Donutz), KC102501
(Kush Crasher / Kush Krasher), SJ092501 (Sleepy Joe / Sleepy Joy), CLE072501
(Clemosa / Clemosa a bud). A seventh, GG012603, the delivery list calls **GG4**
and the desk calls **Gorilla Glue**. The drafts print the desk's spelling.

**Potency against the delivery bracket.** Two lots conform to the specification
the desk assigns them and contradict the bracket they were delivered under:
OPM122501 reads 8.09 % against a delivered 10–13 % bracket, and GG012603 reads
17.59 % against a delivered 13–16 % — and 17.59 % is exactly the upper limit of
its own class. Only the QP can settle which is right.

## Reproducing

    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_live_instrument.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_coq_drafts.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv

---

# Marking what is not held — 10.09.2026 (second revision)

The owner asked for the unfilled parameters and placeholders to print in square
brackets and in red, so that what still has to be changed is obvious on the page.
Doing it meant first finding *everything* that is unfilled, and the sweep turned
up three fields that were not blank at all — they were the master's worked
specimen printing as though it were this batch's data.

## The convention

**Anything in red inside square brackets is not held by the desk and must be
completed or confirmed before issue.** Each draft now carries that sentence in
its own footnote, next to a bracket swatch, so the page explains itself.

Three deliberate choices behind it:

- **The brackets carry the meaning, not the colour.** There is no
  `print-color-adjust` anywhere in this master, so a colour a printer treats as
  decorative simply disappears; a greyscale photocopy of these drafts still shows
  every marker. The declaration is now added anyway, so the red prints too.
- **The red is not the document's other red.** `#9B2C2C` is the DRAFT watermark
  and, on the sibling iCoA, the FAIL status. A field still to be completed is not
  a failing result, so the marker is `#E02B20` and nothing else on the page uses
  it.
- **A blank result prints `[—]`, never `[ ]`.** An empty bracket pair in a column
  of `<10`, `<2`, `< LOQ (<0.20)` and `N.D.` reads as concentration notation. The
  em dash cannot be read as a number.

The marker is **not** draft-only on result cells. An issued certificate with a
blank result is a defect that should be visible on its face, not rendered
quietly — and until now a blank printed in the same muted grey as a measured
`N.D.`, in the one column where those two mean opposite things.

## Three fields that were printing the specimen's data

| field | printed on all 22 drafts | now |
| --- | --- | --- |
| `<title>` | `… CoQ-PP-2026-0005 — Amsterdam Amnesia (AA) — Grade I — Batch P060052` | **set from the batch** |
| the two approvers' names and credentials | `Blagoj Nikolov` / `Jovana Romevska Cvetkovski`, with their qualifications | marked |
| `Cont. Pack.` | `TRIPLEX ALU BAG · … · 300 × 500 mm · net. 400.0 g ±3%` | marked |

The title is the serious one and it is fixed rather than marked: it is not
visible on the sheet, it is what a browser prints in the page header and what a
PDF carries as its `/Title`, so every draft was being **archived under a
certificate number that was never issued and a batch it does not describe**.
Nothing else on the document could correct that, because nothing else on the
document showed it.

The other two are marked rather than deleted. The names are almost certainly the
right officers and the packaging is probably a fixed product attribute — but the
desk holds neither, no field feeds them, and `setLk` cannot even reach the
packaging lockup because that value sits in `.attr-val` rather than `.lk-val`.
Confirming them is a person's job.

## One more repair: the laboratory that printed twice under two identities

Section 03 exists to attribute each result to an accredited laboratory. `LAB_META`
was keyed on long names only, so a citation filed under the desk's **short** code
fell through to a bare abbreviation with no accreditation and no address: `CNP` on
17 of the 22 drafts and `IJZ` on 4 — while the very same institutions printed in
full, with their ISO/IEC 17025 numbers, on the rows above. A partly-populated
field that looks legitimate is worse than a blank. The short codes now resolve,
from `tracker_data.LABNAME`.

## Left for the QP, not marked

**On all 22 drafts the headline potency disagrees with the Total Δ⁹-THC assay in
the results table of the same document** — by up to 3.76 points (CJ052501/01
prints 24.05 % in the banner and 20.29 % in row 4). On **13** of them the banner
value is on another certificate the desk holds for that determination, so the two
numbers are two real measurements of one lot and the page does not say so. On the
other **9** the banner value is on no certificate the desk holds at all.

It is not marked, because it is not a blank: it is a figure from the owner's own
`PP_Potency_MASTER_Spec`, and choosing between two measured values is a QP
decision, not a compiler's. It is recorded here and belongs on the Work Order
beside the other potency contradictions.

## The criterion that was never enforced

Determination 4 is the only line on the certificate whose acceptance criterion is
a **two-sided band** — `21.60 – 26.39 % (grade III, class THC 24, nominal 24.00 ±
2.40)`. Nothing ever judged it. `status_of` in `build_coq_schedule.py` tests
`got > limit.value` and has no lower bound, and `tracker_data.over_limit` only
fires on a criterion carrying `<`, `≤` or `max`. An assay **below** its band was
therefore never flagged anywhere in the instrument.

**19 lots corpus-wide print a Total Δ⁹-THC outside the range printed beside it,
every one of them recorded as `covered`.** Three are in the Tranche 1 and 2
drafts:

| lot | prints | against |
| --- | ---: | --- |
| CJ052501/01 · P050162 | 20.29 % | 21.60 – 26.39 % |
| GP072501/2 · P050302 | 19.81 % | 16.20 – 19.79 % |
| PM092501 · P060062 | 14.06 % | 10.80 – 13.19 % |

The widest in the corpus are FB012602 (24.09 % against 16.20 – 19.79 %),
JD012603/02 (20.54 % against 12.60 – 15.39 %) and PM112501 (13.33 % against
9.00 – 10.99 %).

These are **marked, not failed**. Whether an assay below its band is an
out-of-specification result or a lot sitting in the wrong grade band is a QP
decision — the material may be perfectly good and simply graded wrong — and this
compiler does not make it. What it will not do is let the figure print unmarked
beside the range it misses, and the section 04 disposition tick "Conforms to
Specification" on issue over the top of it.

The same family of disagreement is already on the Work Order at the delivery
level, where a batch was sold in a bracket its own certificate contradicts.
