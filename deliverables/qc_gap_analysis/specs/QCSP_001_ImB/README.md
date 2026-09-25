# QCSP 001 v.03 — the intermediate-bulk product specification

Fifty-seven sheets, one per specification code, each filled onto the owner's own template
(`../base/Product_Specification_ImB.html`) and printed to one A4 page.

    SHEETS/   the sheet as HTML, the editable source
    PDF/      the same sheet printed, vector, fonts embedded
    DOCX/     the same sheet as Word, made from the PDF beside it
    INDEX.json what each sheet carries, for checking without opening it

The Word sheets are not a second drawing of the specification. They carry the PDF's own
graphics as the page and every line of text as a real, editable Word run pinned to the
coordinates the sheet gives it, with the house faces embedded — the method the owner asked
for on 21.09.2026, after an HTML export came out as *"a totally different file, different
design, different structure, different everything"*. Measured against the printed sheet,
151 runs matched on `QCSP_001_AB-I`: each starts within 0.024 pt of where it belongs, sits
within 0.049 pt of its own line and ends within 0.577 pt at worst. The method and the
measurements are in `../../tracker/PDF_TO_WORD_2026-09-21.md`.

## What was filled, and what was not

Only the template's declared fields: the cultivar and its potency headline, the three tick
pills, the product code, the potency window, the specification document code, and the two
approval dates. Every anchor is asserted to match the template exactly once, so a template
that changes shape stops the build instead of being half-filled.

**Section 02 was not touched.** Its twenty-eight rows and four columns — № · Parameter ·
Method / Reference · Acceptance Criteria, with the families grouped under 9, 10, 11 and 12
— are the template's own and are carried through byte for byte on all 57 sheets. #4 keeps
the template's *Per target grade as per Section 01*; it does not repeat the window.

**The footer carries no document code.** The owner, 21.09.2026: *"the templates did not
have doc code in bottom right corner"*.

**The document is v.03.** The owner, the same day: *"the specification template is v.03 not
v.04"*. The per-sheet code keeps its `_v.01` suffix, which is what both certificate fleets
cite; bumping it would move 344 documents to say nothing new.

## The numbers

The nominal, tolerance and window come from the potency decision of **17.09.2026** — the
same figures all 172 certificates of quality print. That is the Head of QC's instruction of
18.09.2026: *"update the actual product specification that we built according to this new
and latest decisions regarding ranges."*

**One thing for the owner to note.** The sheets are signed **01.06.2026** and versioned
**v.03**, as the template has them, but the windows are the 17.09.2026 ones — which are not
the windows the v.03 signed on 01.06.2026 carried. Two documents therefore answer to the
same version and date while stating different figures. If that is to be resolved by a
version bump rather than left as it stands, it is one line in `build_qcsp_imb.py` and a
reprint.

## Attributes

Phenotype, chemotype and processing are read off the certificates that already print them;
a code whose lots disagree about an attribute stops the build rather than having one chosen
for it. The Phenotype pill carries an INDICA : SATIVA ratio only where the record states
one — 28 of the 57 are hybrids whose record gives a word (INDICA-DOMINANT, BALANCED, TO BE
DETERMINED) rather than figures, and no figures are invented for them.

## Rebuilding

    python3 specs/build_qcsp_imb.py      # 57 sheets onto the template
    python3 specs/print_qcsp_imb.py      # one A4 page each, fonts embedded
