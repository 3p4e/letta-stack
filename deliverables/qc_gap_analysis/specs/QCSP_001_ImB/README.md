# QCSP 001 v.03 — the intermediate-bulk product specification

Fifty-eight sheets, one per specification code, each filled onto the owner's own template
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

The nominal, tolerance and window come from the current grade table,
`../../potency_grades_2026-09-15.csv`. That is the potency decision of **17.09.2026**, plus the
grades set since:
- WED-II, 22.00 ± 1.40, set on the KVM4 builder on 26.09.2026;
- GRC-IV, 7.00 ± 0.70, set on 27.09.2026;
- Grapes And Cream as three ranges with no empty one (7, 10, 12), 07.10.2026. GRC-III left the table, its
  sheet is deleted, and the KVM4 builder holds the same three ranges as finished.

These are the figures the certificates of quality print. That is the Head of QC's instruction of 18.09.2026:
*"update the actual product specification that we built according to this new and latest decisions regarding
ranges."* The numeral is the table's, read off the code; it is not a rank by nominal, because numerals are
sequential by creation.

## 07.10.2026

Head of QC, 07.10.2026:
- **Grades.** GRC-IV and WED-II now have sheets, and GRC-III is gone. `build_qcsp_imb.py` reads the grade
  table, not the 17.09 JSON, which had neither grade.
- **Phenotype.** *"Don't concern yourself with tranche one and tranche 2 batches since they're already sent"*.
  A sheet takes its attributes from its Tranche 3 lots, then from the lots outside the tranches, and from
  Tranche 1/2 only when nothing else cites it.
  - So the eight BSS, GG and OPM sheets that Tranche 3 cites read Hybrid, Indica dominant, like their
    certificates (ruling of 07.10.2026 for Tranche 3).
  - A Tranche 3 hybrid whose leaning is known and whose split is not prints `· INDICA DOMINANT`, in the style
    of the split.
- **Fonts.** Montserrat now stands behind Orbitron. The Macedonian of the Orbitron labels had printed in
  Liberation Sans (Orbitron has no Cyrillic), as on the iCoA before 27.09.2026. Every letter and digit is now
  in a house face; only ≤ ☒ ☐ ∑ Δ ⁹ fall back.
- **Reprint.** All 58 sheets are reprinted with the current printer (Playwright's own browser), and the Word
  copies are remade from them.
- **Print-safe.** *"The printer is printing white pages when printing the specifications."* The design's fades
  (CSS masks and opacities) printed as transparency: 58 page-sized images, 29 soft masks and 78 transparency
  groups per sheet, which a printer short of memory drops as a white page. Each sheet is now one opaque 300 dpi
  background under its vector text, with no transparency left (`print_qcsp_imb.py`, two passes over the same layout;
  each sheet checked against the plain print). The files are a third of the size. `--vector` prints the old way.
- **One file per strain.** *"individual PDF files per strain, all grades merged into one document"*:
  `_zip/QCSP_001_ImB_by_strain_2026-10-07.zip`, 24 files, the strain's sheets in grade order with a
  bookmark per grade (`specs/merge_qcsp_by_strain.py`; the pages are joined, not reprinted).

**One thing for the owner to note.** The sheets are signed **01.06.2026** and versioned
**v.03**, as the template has them, but the windows are the 17.09.2026 ones — which are not
the windows the v.03 signed on 01.06.2026 carried. Two documents therefore answer to the
same version and date while stating different figures. If that is to be resolved by a
version bump rather than left as it stands, it is one line in `build_qcsp_imb.py` and a
reprint.

## Attributes

Phenotype, chemotype and processing are read off the certificates that already print them;
a code whose lots disagree about an attribute stops the build rather than having one chosen
for it (Tranche 3 lots first, see above). The Phenotype pill carries an INDICA : SATIVA ratio only where
the record states one. Where it gives only a word, no figures are invented: a Tranche 3 sheet prints the
leaning (INDICA-DOMINANT), and BALANCED and TO BE DETERMINED print nothing.

## Rebuilding

    python3 specs/build_qcsp_imb.py      # 58 sheets onto the template
    python3 specs/print_qcsp_imb.py      # one A4 page each, fonts embedded (or name sheets to print only those)
    python3 design_handoff/toolchain/pdf_to_docx_exact.py --batch --force specs/QCSP_001_ImB/PDF specs/QCSP_001_ImB/DOCX
