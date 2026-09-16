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

## 4 · Two defects the rebuild exposed, and what was done

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

`merge_tranches_v40.py` prints any document that has no page yet, then writes
`CoQ_Tranche_1.pdf` and `CoQ_Tranche_2.pdf` — the release certificates in register
order, then the reissues in register order, each page bookmarked with the certificate
it carries — and a `_flat.pdf` beside each, every page a 300 dpi lossless raster so a
printer resolves no gradient of its own. Six documents belong to no tranche in either
scope file and are named in the run's output rather than dropped quietly.
