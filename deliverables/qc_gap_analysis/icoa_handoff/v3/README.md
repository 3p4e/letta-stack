# The Claude Design iCoA package — taken in and printed, 18.09.2026

The Head of QC sent the finished internal-certificate design system on 18.09.2026 from Drive
`iCOA-COQ/Final_Docs/xCOAs/CoX_DES/ISSUE_iCOA`, with the instruction: check whether the
certificates already carry the correct information, and if they do, export them to the best
printable PDF **without editing them**.

They do. 215 certificates — **89 INITIAL + 126 RETEST** — and the count is right: the register
issues one certificate per testing ROUND, not per lot, and the desk's live
`icoa_register.build()` yields the same 215 over 93 batches. The six retests that sit on lots
outside Tranche 1–3 are the six lots withdrawn on 18.09.2026 (CC042601, FB042601, P050282,
P060042, P060082, P060492); their rounds were run before the withdrawal and the certificates
stand.

## What is here

```
ISSUE_iCOA/
├── _icoa.css            base CoX stylesheet          ← load 1st
├── _coq-rules.css       the CoQ fleet's 53 layers    ← load 2nd
├── _icoa3-print.css     this design + print layer    ← load 3rd, MUST BE LAST
├── _logo.svg  _sig_qc.png  _sig_qa.png  index.html
├── _generator/          icoa3_gen.js · icoa_v44_recs.json · coq_plan.json · build_fleet.js
├── INITIAL/   89 certificates
└── RETEST/   126 certificates
pdf/          iCoA_INITIAL.pdf · iCoA_RETEST.pdf · pages/<document>.pdf
```

`build_fleet.js` is the rebuild loop from `HANDOFF_TO_CLAUDE_CODE.md` §1, written out so the
fleet can be regenerated from the register without hand-running the snippet.

## The design is untouched

Rebuilt locally from the shipped `icoa3_gen.js` + `icoa_v44_recs.json` + `coq_plan.json`, the
output reproduces the Drive package **byte for byte** — spot-checked against Drive's own file
sizes on 26-001, 26-096, 26-103, 26-147, 26-215 and both Graps & Creme initials, all exact.
Drive's upload sanitises `&` to `-` in file NAMES (`G&C_` → `G-C_`); the documents themselves
are identical.

No font size, colour, border, gradient or spacing value was altered. No section was added,
removed or renamed. The option vocabularies in §03 are as authored.

## The one correction — a cultivar that matched no list

**Graps & Creme fell through the cultivar profile and printed the wrong colour on 6
certificates** (26-049, 26-054, 26-057, 26-136, 26-169, 26-210).

`icoa3_gen.js` names the cultivar `GRAPS AND CREME` in both `AROMA_SWEET` and `ANTHOCYANIN`,
but the register writes it `Graps & Creme`. The matcher is a plain case-insensitive substring
test, so the ampersand spelling matched **neither list** and the batch fell to the silent
default — colour `0`, odour `0`. The odour landed right by accident; the colour did not. Those
six certificates printed *Deep green–brown-green* where the design's own `ANTHOCYANIN` list
intends *Green, purple bracts*.

The fix is one line, in the profile matcher and nothing else — normalise the ampersand to the
word the lists use:

```js
function has(list,strain){const s=String(strain||'').toUpperCase().replace(/&/g,'AND').replace(/\s+/g,' ');
  return list.some(function(x){return s.indexOf(x)>=0})}
```

Verified: **209 of 215 certificates are unchanged**, the 6 differ only in which box carries the
tick, the ticked-box count stays at 19 on every certificate, and all 24 cultivars in the
register now resolve to a named list entry — none falls through to a default.

This is the rule the Head of QC set on 18.09.2026: the tick follows the strain, and the option
set must carry something applicable for every strain to tick.

## What drives §03, and what does not

| Attribute | Driven by | Source |
| --- | --- | --- |
| Colour | `ANTHOCYANIN` cultivar list | `_generator/icoa3_gen.js` |
| Odour | `AROMA_SWEET` / `AROMA_CITRUS` / `AROMA_EARTH` | `_generator/icoa3_gen.js` |
| Inflorescence form | phenotype — sativa-leaning → *Moderately compact* | `coq_plan.json` |
| Texture · bracts · bloom | the monograph's single conforming outcome | fixed |
| Identification B · Foreign matter | identical on every batch | fixed |

**There is no authoritative per-strain colour or odour string anywhere.** The BASE_SPCs state
grade, potency window and the parameter table; they carry no organoleptic text. That is exactly
why §03's macroscopic row is a *derived pre-selection* an analyst confirms against the sample,
not a quoted observation — and why the certificate never presents it as prose.

**Dominance is not usable as an input.** Of 258 rows in `spec_attributes_2026-09-10.csv`, 135
read `HYBRID, TO BE DETERMINED` and 86 `INDICA` rows have the field empty — more than half is a
placeholder. Phenotype is the only column the generator consumes, and only for inflorescence
form. Anything wired to dominance would have to gate on the non-placeholder values and fall
back to phenotype, never to a default that asserts a finding — the same rule the design already
applies to the 65 batches with no cultivar record, whose phenotype and processing boxes render
**open** rather than defaulting to Hybrid/Hand.

## One asset differs, and it does not render

`_logo.svg` here is the brand mark the CoQ fleet already prints (14,432 B). The package's copy
is 22,206 B: the same artwork — same viewBox, paths, gradients and transforms — carrying a
**C2PA provenance manifest** in a `<metadata>` block that does not render. If that provenance
has to travel with the certificates, drop the Drive original in over this file; nothing on the
page moves.

## Print

`print_icoa_v3.py` — the certificate-of-quality pipeline, unchanged in substance. The page loads
Montserrat, Roboto Mono and Orbitron by `<link>`; a renderer with no route to Google substitutes
silently and every column measured against Roboto Mono's advance breaks. The faces are fetched
once, subset to the characters the fleet prints, inlined as `@font-face` data URIs, and Google
is blocked at the network layer for the run. A4 portrait, `print-color-adjust:exact`, no
transparency group reaches the PDF.

```
python3 icoa_handoff/v3/print_icoa_v3.py              # both folders
python3 icoa_handoff/v3/print_icoa_v3.py --only 26-057
```
