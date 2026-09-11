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

---

# Third revision, 10.09.2026 — the master is the document

The owner ruled that the CoQ template may not be modified in any way. The
compiler may replace **parameter values** and **the laboratory reference
section**, and the **batch number, strain, packaging date and date of manufacture
(the harvest date)**. It may not touch the parameter names, the acceptance
criteria column, or anything else.

Two of the previous revision's changes were straightforwardly wrong under that
rule and are reverted.

**Section 02 was being rebuilt row for row from the desk's own schedule** — not
just the results, but the parameter column, the method column and the acceptance
criteria. Measured against the master, that reworded 18 criteria and 16 methods,
and it **dropped the asterisk from "Assay — Total Δ⁹-THC\*", "Total CBD\*" and
"Total CBN\*"** — the asterisk the footnote beneath the table refers to, so the
footnote pointed at nothing. The compiler now walks the master's own 24 rows and
writes the **result cell only**, in the master's own `<span class="r-val">` shape.
Every build verifies it: 24 rows against 24, **0 differences in the parameter,
method and criterion columns**, 21 in the result column.

**Everything the last revision marked outside those fields is reverted** — the
document ID, the issue date, the headline potency, the product code, the potency
range, Spec. Ref., the phenotype and processing chips, the approval block, the
packaging lockup, the appended footnote sentence, and the marking of a value that
misses its band. The only marker left is `[—]` for a result the desk holds
nothing for, which sits in the result column.

Two things were kept because they are on the owner's list. The **laboratory
cross-reference** in section 03 resolves the desk's short codes, so `CNP` and
`IJZ` print as the accredited institutions they are rather than as bare
abbreviations. And the **batch number in the section 04 disposition label** is
written, because a batch number is a field the compiler is asked to fill; both
tick boxes stay as the master ships them.

## What this leaves printing the specimen's data

Reverting is the right answer to the instruction and it has a cost, which is the
owner's to weigh. On a Grape Pie certificate for P050022 the master still prints:

| field | prints |
| --- | --- |
| document ID | `CoQ-PP-2026-0005` |
| issue date | `05.06.2026` |
| product code | `AA_THC28.5:CBD1` |
| potency range · Spec. Ref. | `27.00 – 30.00 %` · `QCSP_001_AA-I_v.01` |
| phenotype · processing | `☒ Hybrid Indica dom.` · `☒ Machine` |
| headline potency | `XX.XX%` |
| approvers | `Blagoj Nikolov` · `Jovana Romevska Cvetkovski` |
| packaging | `… 300 × 500 mm · net. 400.0 g ±3%` |
| page `<title>` | `… CoQ-PP-2026-0005 — Amsterdam Amnesia (AA) — Grade I — Batch P060052` |

The `<title>` is the one with a consequence beyond the sheet: it is what a
browser prints in the page header and what a PDF carries as its `/Title`, so the
archived file is indexed under a certificate number that was never issued.

Each of these is one line of code to fill from the desk. None is filled, because
none is on the list.

---

# Fourth revision, 10.09.2026 — the owner's README, and the two potency figures

The owner supplied `CoXTemp` (Drive `1JtunFDx-2sgOr1bEFv-Ktis9rB5hNrGw`): the CoQ
master, `cox.css`, and `ISSUE_COQ_README.md`. **The template in that folder is
byte-identical to the one already vendored here** — verified by md5 — so nothing
about the master changed. The README is vendored beside it as
`live_instrument/templates/ISSUE_COQ_README.md`; it is the specification for what
may be written into the master, and it is broader than the previous revision
assumed: batch number, cultivation batch, strain, grade, class, potency range,
product code, specification doc code, manufacture date, packaging date, the Total
Δ⁹-THC assay result, issue date and the iCoA reference code.

Two rulings arrived with it, and both are now implemented.

**The banner and the assay are one number, and it is the certificate's.** The
README says the gold figure beside the strain is the actual Total Δ⁹-THC assay
result, not the grade nominal; the owner's ruling of 10.09.2026 settles that it
comes from the certificate — the same value the row-4 result carries. Before it,
the banner carried the master spec's figure and row 4 the certificate's, and
**they disagreed on all 22 drafts**, by up to 3.76 points (CJ052501/01 printed
24.05 % beside 20.29 %). All 22 now agree, verified draft by draft.

**The acceptance range is a placeholder.** It is supplied separately, so the two
places that print it — the Section 01 "Potency" field and the row-4 acceptance
criterion — carry it bracketed until it is settled. That is the single
acceptance-criteria cell this compiler touches, and the build check counts it.

The build check is the guarantee behind all of it: 24 master rows against 24
draft rows, **0** differences in the parameter and method columns, **1** in the
acceptance-criteria column, 21 in the result column. The identification criteria
that an earlier revision had rewritten now read the master's own "Conforms to
monograph" again, and the asterisks on Total THC, CBD and CBN — which tie those
rows to the footnote — are back.

## The date of issue comes from the register

Owner, 10.09.2026: the date of issue is the one stated in the CoQ analysis master
workbook, and the certificate prints that date.

`CoQ Register` holds it per lot as `Issue date (planned)`, beside the code the
certificate will carry. Both are formulas, so `tracker/extract_coq_register.py`
recalculates the sheet through LibreOffice and lifts the computed values to
`coq_register_2026-09-10.csv`; `export_coq_artifact_data.py` reads that, so the
desk, the artifact page and the compiled certificates take the date from one
place. The register keys itself on the P lot where a lot has one and on the
cultivation batch where it does not, so both are indexed, through
`batch_id.batch_key` rather than by string — the register writes `GG012601＊`
where the schedule writes `GG012601`.

**72 of the 164 CoQs** now take their issue date from the workbook, including
**all 22** in these drafts: 21 on 27.05.2026 and J31102501 on 07.07.2026. It
prints in the three places a certificate carries it — the header and the date
under each of the two signatures — and they agree on every draft.

A lot the register cannot issue yet has no date there and keeps the schedule's
SOP floor, written `≥ 11.05.2026`. That is a rule, not a date, so it prints as the
controlled blank the master ships rather than being silently stripped of its `≥`
— which is what the header used to do.

---

# Fifth revision, 10.09.2026 — the pills come from the specification

Owner, 10.09.2026: *"the phenotype and the processing pills need to be selected
according to the specification for the product strain."*

Until this revision every draft printed the master's worked specimen —
`☒ Hybrid Indica dom.`, `☒ THC`, `☒ Machine` — on all 22 lots, and the packaging
line under it. Those are not laboratory results and they are not the desk's to
guess. They are product attributes, and the document that states them is the
**issued QCSP 001 specification the certificate already names in Spec. Ref.**

## Reading a tick that is not a tick

The specification does not print a ballot box. It prints all the options and sets
the selected one in cream on a filled pill, the rest in muted olive on the
ground — so a selection is a *colour*, and hard-coding which colour would let a
restyle silently invert every certificate. `spec_attributes.py` calibrates on the
document instead:

* the phenotype band prints three options and exactly one is selected, so the
  colour that appears **once** is the selected one;
* that reading is accepted only if the once-colour is the **lighter** of the two
  — cream on dark, never the other way round. Two ticked options would also
  produce a once-colour, and this is what catches it;
* the colour so derived is what selects in the two-option chemotype and
  processing bands, which cannot calibrate themselves.

A document whose phenotype band does not resolve that way is refused whole, the
same discipline `cell_resolution.py` applies to a result.

The specifications are PDFs generated from the company's own HTML, so they carry
a real text layer and this reads that layer — `pdftohtml -xml`, from
`poppler-utils`. **No page image is looked at**: the policy chain in
`AGENT_MODEL_POLICY.md` is untouched and no classical OCR is invoked.

## What it found

**257 issued specifications** read across `BASE_SPCs` and the six tranche
folders, with **no disagreement** between two copies of one document code.

| band | |
| --- | --- |
| phenotype | HYBRID 165 · INDICA 86 · SATIVA 6 |
| chemotype | THC 253 · CBD 4 |
| processing | MACHINE TRIMMED 257 |
| primary packaging | **one** distinct value across all 257 |

So on the 22 drafts: **18 lots take a phenotype from their own specification** —
6 Indica, 2 Sativa, 10 Hybrid — and the master's specimen was right on only some
of them. The processing pill was right everywhere, and is now evidenced rather
than assumed.

## The dominance sub-label

The master's Hybrid pill carries a dominance sub-label, `Indica dom.` on its
specimen. That is a claim about the strain, and the specification is where it is
made: under its own HYBRID pill it prints a ratio (`INDICA 70 : SATIVA 30`), a
word (`INDICA-DOMINANT`), or its own controlled blank, `TO BE DETERMINED` —
which **135 of the 165 issued hybrid specifications** say. Where it resolves the
sub-label is set in the master's idiom; where it does not the certificate prints
the specification's own words, bracketed and red. A certificate may not be more
certain than the document it cites.

## The packaging line was never the specimen's

All 257 specifications print the same primary packaging, and it is what the
master prints. So the line is **left exactly as the master sets it** — and
checked rather than assumed. The two documents typeset it differently (the
specification writes `Триплекс Aлу Kеса` with a Latin A and K and separates with
commas; the master is lowercase Cyrillic and separates with middots), so the
comparison is on the figures alone — bag construction, dimensions, fill weight —
which is exactly what a change to the packaging would change.

## Four lots whose specification is not on file

`QCSP_001_GP-THC18_v.01`, `QCSP_001_GP-V_v.01`, `QCSP_001_CJ-IV_v.01` and
`QCSP_001_OPM-V_v.01` are named by P050152, P050322, P060032 and P060242 and are
in none of the specification folders. On those four drafts **every pill is
unticked with its box marked, and the packaging line is bracketed**: the desk
cannot cite a document it does not have. These are the same four lots already
recorded as citing a different grade's specification.

## How the pills are written

In place. The class swaps between `chip-sel` and `chip-un` and the ballot glyph
between ☒ and ☐; **the master's own chip text is never rewritten** — rebuilding
the row is what dropped "Indica dom." and "Машинска" the last time this was
touched. `rowdiff` still reports 24 master rows against 24 draft rows, **0**
differences in the parameter and method columns and **1** in the
acceptance-criteria column, and the selection row still fits: the widest case
(`[TO BE DETERMINED]`) leaves 131 px spare on an A4 sheet.

## Two repairs alongside

1. **A controlled blank in the identification band printed a bare em dash.** On
   this document an em dash is a measured result — a non-detection — so `Prod.
   Code`, `Spec. Ref.`, `Prod. Batch №`, `Manuf. Date`, `Pack. Date` and the
   issue date now print the bracketed marker when the desk holds nothing, like
   every other unheld field.
2. **The gap report's band check had been reporting `0` because nothing marked
   it any more.** It measured a mark the compiler stopped making when the master
   became the document, so it read "0 results outside their printed band" — which
   is not the same statement as "none was checked". The comparison is now made in
   the **report**, never on the certificate, and it declines two criteria rather
   than guess at them: the master marks its powers of ten up as `<sup>`, so
   `≤ 10⁵ CFU/g` reads as `≤ 105` through `textContent` and every microbiological
   count would report as a failure; and the row-4 range is the owner's
   placeholder, so there is no band to be outside of yet. Against what remains —
   loss on drying, mycotoxins, heavy metals — **0 of the 22 drafts carries a
   result outside the criterion printed beside it.**

## Reproducing

    python3 deliverables/qc_gap_analysis/spec_attributes.py --csv
    python3 deliverables/qc_gap_analysis/export_coq_artifact_data.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_live_instrument.py
    python3 deliverables/qc_gap_analysis/live_instrument/build_coq_drafts.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv \
        --chromium /opt/pw-browsers/chromium-1194/chrome-linux/chrome

`spec_attributes.py` needs `poppler-utils` (`pdftohtml`); everything else is
already in the container.

---

# The mycotoxin sub-parameters — 10.09.2026

Owner: *"the QC laboratory is referencing the mycotoxins separately but they all
follow under one general mycotoxins parameter, and the sub-parameters are
Ochratoxin A, Aflatoxin B₁ and total Aflatoxins — and nonetheless you transcribe
the correct and corresponding parameter value into the certificate of quality
accordingly."*

**This corrects a claim made earlier in this note.** It said the certificate
"reports the aflatoxin sum, not the single analytes", and offered that as the
reason #10.1 and #10.3 are blank on every draft. That is true of the release
certificates and of no others, and it was written as though it were the
laboratory's practice generally. It is not.

| laboratory | what it reports | what the desk does |
| --- | --- | --- |
| Farmahem `197-…-М/26` (re-analysis) | all three, separately, in register columns O, P and Q | transcribes each to its own line — **21 of 21 retest certificates carry all three** |
| IJZ / IPH (release) | the three sub-parameters as one block, `n.r.; <2; n.r.` — one reported | maps the reported value to Total Aflatoxins (#10.2) |

The mapping on the release certificates rests on the slot's position in the
block, which matches both the certificate's own order and the register column the
value was recorded in. It does **not** rest on a printed analyte name.

## Two findings

**The desk prints a blank where the source prints `n.r.`** Determinations 10.1 and
10.3 come out as the bracketed marker on the release drafts, and the source says
*not reported*. A line the desk holds nothing for and a line the laboratory did
not determine are different statements, and on a certificate of quality they must
not look the same.

**The reading decides pass or fail on four lots.**

| lot | document | reported |
| --- | --- | ---: |
| CLE072501 | 5700-2025 | 2.2 µg/kg |
| OPM092501 | 87-2026 | 2.2 µg/kg |
| OPM1024_03 | 3636-2025 | 2.1 µg/kg |
| OPM122501 | 1627-2026 | 2.2 µg/kg |

Read as **Total Aflatoxins** against ≤ 4 µg/kg they pass. Read as **Aflatoxin B₁**
against ≤ 2 µg/kg they fail. The desk reads them as the sum. Nothing here settles
it: the page has to be read before any of those four is signed.

## One notation for a not-detected result

Owner, 10.09.2026: *"we should have one use of any derivation of 'n.r.' and we
will use ND everywhere."*

The desk carried **eight spellings of one assertion** on the certificates alone —
`ND`, `N.D.`, `Н.д.`, `Н.д. (not detected)`, `н.д.`, `ND ᴰ`, and two more carrying
a residue gloss — and six further ones in the 09.09 pass, including `n.r.` and
`Н.Д.`. A results column that spells one assertion eight ways invites a reader to
think it means eight things.

`result_notation.nd()` is the single definition. It rewrites **the notation and
nothing else**: the unit stays, the footnote marker stays, the residue gloss
stays, and anything that is not a not-detected result comes back untouched —
including `Standard`, `Conforms and complies` and `2nd sample`, which contain the
letters and are not results. **119 printed results rewritten**; the certificates
now carry `ND`, `ND mg/kg — all 25 residues`, `ND ᴰ` and `ND — all 13 residues`,
which is one notation with its units and references intact.

It is applied where the desk stores a printed result, so the certificates, the
Quality Desk and the PDFs all inherit one spelling from one place.

**A note for the record, because the ruling settles the question rather than
dissolving it.** *Not reported* and *not detected* are not the same statement:
one says the analyte was measured and absent, the other that it was not measured.
The owner's ruling is that in these documents `n.r.` is stated as a parameter
result and means what `n.d.` means, so both print `ND`. That is a QC ruling on
the company's own documents and it is recorded here as one.
