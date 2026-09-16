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

## 3 · The three corrections of 16.09.2026

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
