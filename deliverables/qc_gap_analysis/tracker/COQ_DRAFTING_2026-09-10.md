# Drafting the Tranche 1 and Tranche 2 certificates — 10.09.2026

## What was asked

Whether every placeholder a Certificate of Quality needs is held, and if so
whether the Tranche 1 and Tranche 2 sets can be drafted.

## The short answer

The **header** of the certificate can be filled for every lot in scope. The
**results table** cannot be filled for any of them. Twenty-two drafts exist and
are in `../drafts/`; not one is complete, and the missing lines are named per
lot in `../drafts/coq_draft_gaps.csv`.

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
Measured on the compiled pages at A4 width, 72 result lines across the 22 drafts
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

**168 blank printed lines across 22 drafts.** By determination:

| line | blank on | why |
| --- | --- | --- |
| #1 Identification A, appearance | 21 of 22 | the result lives on the in-house iCoA and was never transcribed to the tracker |
| #2 Identification B, microscopy | 21 of 22 | same |
| #7 Foreign matter | 21 of 22 | same |
| #6 Total CBN | 17 of 22 | not carried on the cited certificate |
| #10.1 Aflatoxin B₁ · #10.3 Ochratoxin A | 22 of 22 | the certificate reports the sum, not the single analytes |
| #9.1–9.5, #10.2, #11.1–11.4, #12 | 4 of 22 | GG012603, J31102501, JD112501 and KC102501 — the certificates that cover these were added to `eCoA_DATABASE` on 09.09.2026 and the tracker has not absorbed them |

The last row is the important one: those four lots are clean on the evidence and
blank on the document, purely because the desk's own record is behind the
certificate folder. Absorbing the 155 certificates added on 09.09 closes 44 of
the 168 blanks without any new testing.

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

    python3 deliverables/qc_gap_analysis/live_instrument/build_live_instrument.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_coq_drafts.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv
