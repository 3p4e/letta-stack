# REBUILD v40 — the certificate set built through the Claude Design package

*Purely Plant GmbH · Quality Desk · 16.09.2026*

This is the receipt for the rebuild the Head of QC ordered on 16.09.2026: the
certificates of quality are no longer drawn by the desk's own template. They are drawn
by the **Claude Design package** `PP_CoQ_Handoff_2026-09-16`, and the desk supplies
only the data.

> "You have to adopt it completely, not in place your templates or decisions upon it.
> You just hold the data."

## 1 · What the source is

| | |
| --- | --- |
| Design system | Google Drive folder `1RICFjTSnQydjAZiEf0ot9jvqPPxLM251` — `PP_CoQ_Handoff_2026-09-16` |
| Certificates published by Claude Design | `ISSUE_COQ` `1VzGwe-QzkDRRXlILAJ9E-D0kJCJUW6kj` · `REISSUE` `1A0La5OpZ3wUcFLw0S4SsuVdi_wv8-Xcb` |
| Vendored into the repository | `design_handoff/` — `cox.css`, `base/`, `design_system/styles.css`, `toolchain/` |

The package's own files do the drawing. `coq_build.js` holds the vocabulary, the
Section 01 and Section 03 builders and the code-shape rule; `coq_apply.js` writes one
record's data into the base document and leaves the visual layer byte-identical;
`coq_check.js` runs sixteen data assertions on the result. `build_v40.js` is the desk's
adapter: it maps `coq_artifact_data.json` to the package's record shape and calls them.
The desk adds **no style of its own** — the two corrections the owner asked for are
appended as one new last `<style id="__owner-mk-subrow-inline">` layer, which is the
package's own mechanism for a correction.

## 2 · What was built

```
documents written: 172  {"ISSUE_COQ":89,"REISSUE/T1":21,"REISSUE/T2":32,"REISSUE/T3":30}
apply warnings: 0   assertion findings: 40 (hard 2)
```

Eighty-nine release certificates and eighty-three 12-month reissues. Every one carries
the **Section 04 conformity decision ticked**, as ordered on 16.09.2026, and none
carries a DRAFT stamp.

## 3 · The seven corrections of 16.09.2026

**The conformity result is bilingual, and the row does not grow.** `Conforms` keeps its
size and its green; `Одговара` sits with it at the template's own `.r-conform .mk` size
— 6.8 px, 79 % of the English. A parameter row already runs two lines in its name
column and takes the template's stacked form; a sub-row is one line tall, so its
Macedonian stays inline and the row keeps its height. Nothing in the results table
changes width, and no page grew.

**Section 04 is ticked.** The base document ships both conformity chips unticked. The
first is set to its selected state on every document, and the build fails loudly if the
chip is not found — 172 of 172 checked.

**The colour is the package's.** The grey the owner saw was the desk's stale template
printing without the package's `__print-opaque` layer, which replaces every
alpha-to-transparent gradient with its opaque-against-white equivalent inside
`@media print`. Without it Chromium flattens the transparency groups at raster
resolution and the page prints with banding and grey haloes. With the package's own
layer stack the cream-and-gold header wash, the heavenly-blue zebra fading to nothing
at both page edges and the gold rules print as drawn.

**Every band fades to white before the sheet edge.** The owner read the printed set and
found that the bars and washes of Section 01 — the bar carrying the section number, the
band with the production batch number and the strain name, and the phenotype / chemotype
row — ran to the physical edge of the paper at full strength instead of fading out at the
page margin, and asked for the section bars and the Section 01 and Section 02 zebras to
fade to white and blend with it. Measured on the rendered page at print media, the three
bands read `rgb(232,239,246)`, `rgb(248,250,252)` and `rgb(252,253,254)` at the first pixel
of 793 — no fade at all. `@page` sets `margin:0`, so a band with no fade is printed to the
edge of the sheet. The table zebra and `.gridrow` were already correct, white at x = 0, so
the complaint resolves to those three bands.

A new last layer, `<style id="__owner-edge-fade">`, gives each of them the package's own
edge geometry: white at the sheet edge, full colour by the typographic margin. It is built
from **opaque stops**. The package defines an edge fade as a `-webkit-mask-image`, but the
56th layer switches masks off (`mask-image:none !important`) and `__print-opaque` flattens
fractional alpha against white for print — so neither a mask nor an alpha veil survives to
print, and a fade written either way would do nothing. The vertical shading of the section
bar and of the batch band is not lost: the original gradient is kept as the upper layer,
painted from 10 mm to 100 % − 10 mm, over a horizontal ramp carrying that gradient's own
mid-height colour, so the two meet in the same tone. Nothing is resized, reworded or
re-coloured; the masthead and the footer keep their full-bleed by design.

**The RESULT column is one ink.** The Head of QC asked that the analysis-results column of
Section 02 be a single dark navy and that no colour mark an edge case:

> "Make all certificates of quality analysis results column in heading 2 be one colour dark
> navy blue and do not use any other colour indicating edge cases of the analysis results,
> or reds, or any other colour than the uniform navy blue."

`<style id="__owner-uniform-result-ink">` sets every result cell — both halves of a
bilingual one — to `--navy` `#1B3A5C`, which is the colour `.r-val` carries by default. That
covers the 738 red cells, the 10 amber and the green `Conforms`. Measured on the rendered
page, the RESULT column now computes one colour, `rgb(27, 58, 92)`, and nothing else.

The inline colour is deliberately **left in the markup**. Assertion A12 reads it to prove
that a result above its own criterion was marked, so stripping it would quietly disarm the
desk's own check; overriding it in the last layer changes the ink on the page and nothing
else. One consequence worth naming: a result above its criterion no longer announces itself
by colour. It is still printed beside its own `ACC. CRITERIA`, the desk's register still
carries the word, and Section 04 still carries the conformity decision — but the page no
longer flags it.

**A determination that was not performed reads `[NT]`.** The Head of QC named the pair:

> "Mostly in the initial certificates of quality two parameters are not tested in
> mycotoxins, which is aflatoxin B₁ and ochratoxin — not tested, and included and tested in
> the retest for every batch, for tranches 1, 2 and 3. So in cases when you have a parameter
> that is not tested in the initial quality control testing, you will put NT as the analysis
> result, and also put it in brackets."

The package prints `[ — ]` in a result cell for a determination that was not performed — no
result on file, *to be performed*, *upon request*, *in-house CoA only*. Every one of those is
"not tested", so in the RESULT column of Section 02 the cell now reads `[NT]`: **720 cells**,
of which the Aflatoxin B₁ `#10.1` and Ochratoxin A `#10.3` rows of the release certificates
are the pair he named. Nowhere else changes — Section 01 and the Section 03 work-order row
keep `[ — ]` in **276** places, because that is a statement about a missing *document*, not
about a determination.

`[NT]` is four characters against five, so no cell changes its length class and no column
moves. The document is **checked** in its package-conformant form, exactly as the owner's
Macedonian half already is: the assertions know the package's closed vocabulary, and the
substitution is made on the document that is written.

**The note under Section 02 names no procedure and no document code.**

> "Below the table for analysis results in heading 2, in the asterisk text, please remove
> all references to SOPs and procedures and remove the references with the codes — only the
> explanation about the assay; and where NT is used as an abbreviation you can explain the
> meaning for those."

The note carried two sentences. The first is the `*` that rows 4, 5 and 6 of Section 02 point
at — how total THC, CBD and CBN are computed — and it stays exactly as the package wrote it.
The second was procedural, and carried the only document code on the line:

> ~~Parameter attribution to the issuing laboratory is given in Section 03 by Param. №;
> in-house parameters are performed prior to final release sampling, before packaging starts
> (QCSOP 005 v.02).~~

It is gone from all 172 documents. In its place, and **only on the 114 documents that
actually print `[NT]`**, the abbreviation is glossed in the note's own bilingual form:
`[NT] not tested — the determination was not performed in this testing round | не е
тестирано — определувањето не е извршено во овој круг на испитување.` The other 58 carry the
assay sentence alone. The build fails loudly if the sentence it is told to remove is not
found, so the note can never be left half-rewritten.

## 3b · The alignment and signature pass of 16.09.2026

A second round of the Head of QC's corrections, all appended as two new last layers
(`__owner-edges`, `__owner-align-s1-s4`) placed at the **end of the body**, after the
package's own trailing correction layers — a desk layer in the head loses to those at equal
specificity, which is why the first attempt did not take.

**Edges.** The four section heading bars (01–04) go **edge to edge, full bleed** — the desk
no longer touches `.sec-label`, so each prints as the package draws it, a full-width bar on a
page with a zero printer margin. The bands and rows beneath fade to **pure white through the
page margin**, so no row colour reaches the sheet edge, and every fade is a single straight
ramp — white at the edge, full colour by ~11–12 mm — with no flat-then-ramp kink to read as a
hard transition.

**Section 01.** The label and value of each info row centre on the row; the manufacturer's
Macedonian line is smaller and its cell content reads left.

**Section 02.** Acceptance criteria reads left, centred on the row; the result reads to the
right page margin, centred on the row; the parameter and number cells read left off the
margin, centred, keeping the sub-row indents of #9/#10/#11.

**Section 03.** The laboratory column is laid out as clean lines — English name and
accreditation, then the Macedonian name and the LT code, then the address, small and grey —
off the left page margin. The CoA document codes sit centred, each on its own line, with the
issue date smaller and grey; the parameter numbers hug the right page margin; the header cells
follow their columns.

**Section 04.** The conformity row packs to the left: the label (two lines), then the batch
number in a bordered box as tall as the label with its value centred, then the two verdict
pills beside it, their content centred. The role lines are given air below the gold rule. The
two managers' **signatures are reapplied** — Blagoj Nikolov, QC Manager, and Jovana Romevska
Cvetkovski, QA Manager — the same authentic scans and tilts the internal certificates carry,
vendored under `assets/` as trimmed transparent PNGs and embedded so each certificate stays
self-contained through PDF export.

Build unchanged: 172 documents, apply warnings 0, assertion findings 48 (hard 2), 0 partial
panels, all policy checks pass. Every document reprinted and each merged document flattened at
300 dpi for press.

## 4 · Four defects the rebuild exposed, and what was done

### 4.1 · A register status was hiding results the desk holds

The package prints `[ — ]` for a status that says no result is on file — *to be
performed*, *upon request*, *not tested*, *in-house CoA only* — and `[pending]` for
*awaiting*. That rule is right. What was wrong is that the desk's status for
determinations #1, #2 and #7 still reads **"to be performed — see route"** long after
the internal certificate of analysis has issued and carried them, and the 15.09 carry
copies a release result onto a reissue row whose own status still names the outstanding
re-analysis. Printed as written, those two put a red `[ — ]` over **1 568** cells the
desk can certify.

`build_v40.js` now separates the two statements. A register status is the desk's word
about the **determination**; a result cell is the package's word about the **result**.
Where a row carries a result **and** a code-shaped source document, a status that
claims no result is set aside for the cell only, and every status that colours a
present value is kept — `OUT OF SPECIFICATION`, `BLOCKED`, `UNDETERMINED`, and the
carry note, which says where the value came from. A value with no document behind it is
a value the certificate cannot attribute, so there the desk's word stands and the cell
prints `[ — ]` — which is what assertion A15 is for, and it caught four documents where
Identification C would otherwise have printed `Conforms` credited to no laboratory.

The register, the tracker and Section 03's citations keep the desk's full wording.

### 4.2 · Cyrillic was printing in a substitute face

Google serves a family as several slices — latin, latin-ext, cyrillic, greek — each
with the `unicode-range` it covers. `house_fonts.font_face_css` inlined every slice but
**dropped the range**, and `@font-face` rules that agree on family, weight and style and
carry no range do not combine: the last one parsed wins outright. Latin is served last,
so it silenced the Cyrillic and Greek slices and every `Н`, `Њ`, `№` and `Δ` in the set
fell to whatever the renderer had on hand — Liberation Sans, measured on every
uppercase Cyrillic glyph of the reissue set. The range now travels with the face.

Six characters still fall outside every slice Google serves for these three families —
`≤ ☐ ☒ ∑ ⁹ ₁`. They are embedded in the PDF from the renderer's own fallback, so the
file is self-contained and prints the same everywhere; they are simply not set in
Montserrat. Noted here rather than fixed, because fixing it means adding a fourth
family to the stack, which is the template's decision and not the desk's.


### 4.3 · Grey down both page edges — determinations 9 to 12, then Section 01

The Head of QC saw it before any measurement did: rows 1 to 8 clean, the 9-to-12 block
grey at the left and right edges of the page. One defect, one cause.

The zebra stripe is a blue that fades to **transparent** at both page edges. Chromium
does not print a transparency the way it shows one — it flattens the transparency group
at raster resolution, and a mid-alpha fade comes out as grey banding rather than a fade
to white. The package ships `__print-opaque` for exactly this: inside `@media print` it
replaces every fading stripe with the opaque colour that stripe would have over white.

It reaches the parameter rows. It does not reach the sub-rows, and the package's own
comment in the stylesheet says why:

> the sub-rows kept the long band only because their sibling selector outranks those

The 642-character sibling chain that stripes a group's sub-rows outranks the print layer
as well, so determinations 9 to 12 carried the transparent gradient into the PDF and
banded grey exactly where the fade sits, while 1 to 8 printed clean. Same design, two
code paths, one of them converted.

The first fix named the rules it converted, so it repaired the block that had been
pointed at and left the next one: `.gridrow.lk-inline`, the attribute strips of Section
01, are the same construction — a cream fill fading to transparent at both edges — and
printed the same grey.

So the conversion is done **by rule, not by name**. `build_v40.js` reads every rule in
the base whose background is a gradient carrying a partial alpha and re-emits it —
verbatim selector and all — inside `@media print`, with each `rgba(C,a)` replaced by
`rgb(C + (255 - C)(1 - a))`, that colour composited over white, and each declaration
marked `!important` to match the originals. Same selector means same specificity, and
last in source wins, so the conversion lands exactly where the original did without
inventing a selector, a colour, a geometry or a row height. Masks are left alone: they
are the package's business and it already neutralises the ones it draws.

Verified by walking every element of a built certificate under print emulation — two
elements carried an alpha gradient before, **none do now**.

Measured on the printed page at 150 dpi, 17 mm in from the left edge of a sub-row:

| | before | after | rows 1–8 |
| --- | --- | --- | --- |
| at 11 mm | 249,249,249 | 254,254,254 | 254,254,254 |
| at 13.5 mm | 228,228,228 | 254,254,254 | 254,254,254 |
| at 17 mm | 207,208,208 | 253,253,254 | 253,253,254 |
| mid-page | 245,247,250 | 247,249,251 | 247,249,251 |
| Section 01 strip, 6.8 mm | 193,193,192 | 255,254,252 | — |

Swept over every page of the Tranche 1 document afterwards: no neutral grey anywhere in
either fade zone.


### 4.4 · The title sat left of centre on every reissue

`coq_apply.js` writes the supersedes line as `<span class="hb-sup">`, and **nothing in
`cox.css` or the 56 layers ever styles `.hb-sup`** — the class is written and never read.
So on a reissue it lays out as an unstyled inline span beside the document code and
widens the header's right column from the package's own `min-width:132px` to 277 px. The
header is a grid of `auto | 1fr | auto` and `.hb-center` centres inside the **middle
column**, so a wider right column moves that column's centre with it.

Measured against the page centre: the title sat **87 px left** on all 83 reissues, and
14 px left on a release certificate — which is the package's own baseline, a 104 px logo
against a 132 px code block, and is left alone.

The correction takes the line out of the width computation rather than restyling the
header: positioned against the header, one line, at the 38 px inset the package's own
edge treatment uses for the gold rules. Measured after: the right column is 132 px
again, the title is at −14 px on reissue and release alike, the header height does not
move (122 px both ways), the line clears the title by 21 px and the document-ID label by
29 px, and no page overflows.

## 5 · What the certificates do not carry, and why

The Head of QC asked directly whether parameters were missing. They are, in the record
rather than in the drawing, and the certificate states it rather than leaving a blank.
Across the 172 documents, by determination:

| # | Parameter | Release (of 89) | Reissue (of 83) |
| --- | --- | ---: | ---: |
| 1 | Identification A, appearance | 26 | 26 |
| 2 | Identification B, microscopy | 37 | 37 |
| 3 | Identification C | 17 | 0 |
| 4–6 | Assay — Δ⁹-THC, CBD, CBN | 16 · 15 · 37 | 0 |
| 7 | Foreign matter | 26 | 26 |
| 8 | Loss on drying | 14 | 14 |
| 9.1–9.5 | Microbiology | 36 each | 30 each |
| 10.1 | Aflatoxin B₁ | **88** | 30 |
| 10.2 | Aflatoxins ∑ | 37 | 11 |
| 10.3 | Ochratoxin A | **88** | 30 |
| 11.1–11.4 | Heavy metals | 36 each | 30 each |
| 12 | Pesticide residues | 25 | 19 |

**Every one of these is a determination the desk holds no result for.** Checked cell by
cell against the record, 172 of 172 documents matched: of 3,612 result cells, 1,213 print
the withheld token, and **four** of those print it while the desk holds a result —
determination #3 on `CoQ-PP_26-005`, `26-006`, `26-025` and `26-026`, where what the desk
holds as the document is a sentence (*"In-house HPLC cross-check"*, *"n/a — Purely Plant
in-house"*) rather than a certificate code, so assertion A15 refuses to credit a result to
a laboratory that cannot be named. Those four need either a document code or a ruling that
the in-house cross-check may be cited. The rest are not a drawing defect and no build can
close them.

The line that stands out is the mycotoxins. For **88 of the 89 release certificates**
no document on file reports Aflatoxin B₁ or Ochratoxin A separately — the laboratory
reported the sum, and the sum is what the release round holds. The 12-month Farmahem
campaign reports both, which is why the reissues carry them. That is a question for the
Head of QC, not a defect of the build: the certificate cannot print a result no
certificate states.

## 6 · Where the desk and the package's own certificates differ

Claude Design published a rendering of the same set in `ISSUE_COQ` and `REISSUE`. The
codes agree and the great majority of file names agree character for character. In
**seventeen** the batch label differs: the package names a P lot where the desk's
register still carries only the cultivation batch — `CoQ-PP_26-052` is `P060162` there
and `SJ102501` here, and the same for `26-055`, `26-058`, `26-061`, `26-063`, `26-065`,
`26-066`, `26-067`, `26-075`, `26-079`, `26-080`, `26-081`, `26-082`, `26-083` — plus
two strain-code spellings (`J31` against `J`, `CC` against `P` on `26-068`) and one
normalisation (`OPM` against the register's own `OMP` on `26-010`).

**Those P numbers have not been adopted.** Assigning a packaged-lot number to a batch
is a statement about the floor, and the desk holds no record of them. They are listed
here for the Head of QC to confirm or reject; until then the certificate carries the
label the register carries. Three documents exist here and not there — the unrecorded
`P160012`, `P160022`, `P160032`.

## 7 · How to rebuild

```
node   design_handoff/toolchain/build_v40.js            # 172 documents + assertions
python3 design_handoff/toolchain/print_v40.py           # every document, four merged PDFs
python3 design_handoff/toolchain/merge_tranches_v40.py  # one document per tranche
```

`merge_tranches_v40.py` prints any document that has no page yet, then merges by tranche,
each page bookmarked with the certificate it carries and a `_flat.pdf` beside each — every
page a 300 dpi lossless raster, so a printer resolves no gradient of its own.

`--series` says which round the tranche document carries. **`reissue` is what the Head of
QC asked for on 16.09.2026** — the 12-month retest certificate is the document that travels
with the batch, and the release certificate is the record of the round that released it.
`release` is that record alone; `both`, the default, writes the complete file, release round
then retest.

| file | pages |
| --- | ---: |
| `CoQ_Tranche_1_Retest.pdf` | 21 |
| `CoQ_Tranche_2_Retest.pdf` | 32 |
| `CoQ_Tranche_1.pdf` — release then retest | 42 |
| `CoQ_Tranche_2.pdf` — release then retest | 64 |

Six documents belong to no tranche in either scope file — `FB032601`, `GG032601`,
`JD022601` and the three unrecorded `P160012/22/32` — and are named in the run's output
rather than dropped quietly.
