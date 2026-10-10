# The figures the Head of QC marked by hand, 18.09.2026

Five certificates of quality came back photographed, with figures written in blue ink
beside cells the page prints as `[NT]` — not tested. This is what was done with them.

The desk does not print a figure because someone wrote it on a page. It prints a figure
because a laboratory's certificate carries it, and it prints that certificate's code, its
date of issue and the laboratory beside it. So every handwritten figure went through the
two-read gate:

* **first read** — the photographs, cropped to the result column and enlarged;
* **second read** — `cell_resolution_2026-09-09.tsv`, the Head of QC's own reading pass
  over the scans, which names the document, its issue date and the laboratory for each
  determination.

## What was entered

Three lots. For each of them the two reads agree figure for figure and the resolution pass
names a citable document, so the values are printed on both the release certificate and
its twelve-month reissue — **54 result cells over six certificates**.

| Lot | Det. | Document | Issued | Laboratory | Now printed |
| --- | --- | --- | --- | --- | --- |
| P060182 · GRC102501/2 | 9 | 136/0233/26 | 06.03.2026 | IPH Skopje | 2.3 × 10² · 1.3 × 10² · < 10 · Absent · Absent |
| P060182 · GRC102501/2 | 11 | 1060/2026 | 09.03.2026 | IPH Skopje | ND · ND · 0.0013 · ND |
| P060412 · JD012603/02 | 9 | 405/0788/26 | 24.06.2026 | IPH Skopje | 6.3 × 10³ · 4.4 × 10³ · < 10 · Absent · Absent |
| P060412 · JD012603/02 | 11 | 3660/2026 | 22.06.2026 | IPH Skopje | 0.085 · 0.044 · 0.042 · 0.042 |
| P060422 · JD012603/02V | 9 | 406/0789/26 | 24.06.2026 | IPH Skopje | 5.1 × 10³ · 4.7 × 10³ · < 10 · Absent · Absent |
| P060422 · JD012603/02V | 11 | 3662/2026 | 22.06.2026 | IPH Skopje | 0.06 · 0.03 · 0.045 · 0.013 |

The certificates are CoQ-PP_26-054 and 26-120 (P060182), CoQ-PP_26-078 and 26-123
(P060412), CoQ-PP_26-076 and 26-124 (P060422).

**The defect this closes is the desk's, not a laboratory's.** Every one of these values was
read on 09.09.2026 and recorded in the resolution pass. None of them reached the
certificate, which has been printing `[NT]` over results that were on file the whole time.

One figure the photograph could not settle — the lead value on P060412, whose middle digit
is not legible — is taken from the resolution pass, which reads `0,085`. That is the gate
working rather than a guess, and it is the reason the gate exists.

## What was held, and why

Two lots carry handwritten loss on drying, heavy metals and pesticide residues for which
there is no document anywhere.

| Lot | Handwritten | The record |
| --- | --- | --- |
| P060372 · CC012603 | LoD 6,42 · Pb 0,006 · Cd 0,007 · As 0,006 · Hg 0,001 · pesticides 0 | resolution pass: NOTHING ON FILE for #8, #11, #12 |
| P060362 · JD012603/01 | LoD 6,95 · Pb 0,008 · Cd 0,011 · As 0,01 · Hg 0,002 · pesticides 0 | resolution pass: NOTHING ON FILE for #8, #11, #12 |

Checked again on 18.09.2026 rather than taken on trust: the Drive lot folders
`CC012603_P060372` and `JD012603_P060362` hold the Farmahem potency pair
(220-29-К/26 and 220-29-М/26; 220-16-К/26 and 220-16-М/26) and the microbiology
certificate (363-0693-26; 365-0695-26), and nothing else. Their two siblings have IJZ
panels 3660/2026 and 3662/2026 of 22.06.2026, and 3661/2026 of the same day belongs to
FB012603 / P060432 — so no certificate of that run is unaccounted for.

The figures are recorded in `intake_handmarked_2026-09-18/reads_handmarked.json` and are
**not printed**. A value with no document behind it is what assertion A15 refuses, and it
is what the whole citation discipline of this set rests on: all 172 certificates currently
pass the citation check with zero findings. One scan into eCoA_DATABASE closes it. This is
**OI-57**.

## What was rebuilt

Everything the corrected data reaches: 172 HTML documents, 172 A4 PDFs and the four merged
PDFs, the six tranche merges, 172 Word documents, the four tranche archives and the eight
Word-only archives. Verified afterwards — the printed page, the PDF text layer and the
archive members all carry the new figures.

`word_archives.py` had its package date written down as a literal `2026-09-17`, so the
first repackaging after it found no archives, produced nothing and emptied `dist/word`
without saying so. It now discovers the date from the archives in `dist/`. Reading the
membership back out of the package was meant to stop exactly this kind of drift; a
hard-coded date was the same drift wearing a different hat.

**Not rebuilt: the master workbook.** `tracker/build_tracker_v8.py` stops with
`NameError: name '_F_' is not defined` at line 2432, where a module-level statement calls
helpers defined inside a function several hundred lines earlier. The break is in `HEAD`,
predates this work and has nothing to do with it, but it means `CoQ_Analysis_Master_v45`
cannot be produced until it is repaired. v44 stands, and is now behind the certificates on
these 54 cells. This is **OI-58**.

---

# A document code with a note on it still cites

**18.09.2026, later the same day.** The Head of QC asked whether Farmahem is cited on the
five certificates in the photographs. It is — every one of them is a reissue, and each
carries a Farmahem row for identification C, Total THC, Total CBD, Total CBN and the
mycotoxins (`220-14/16/17/18/29-К/26` and the matching `-М/26`); P060182 takes its loss on
drying from Farmahem too, on `051-6-ГС/26`. The photographs are simply cropped above that
row.

A sweep of the whole set then confirmed the general case: across all 172 certificates
there is **no** laboratory with a printed result and no row in Section 03. Farmahem
appears on 94, the Institute on 144, the Center for Natural Products on 116, Purely Plant
on 149 and the Phytosanitary Laboratory on 2.

The sweep did turn up one certificate, and it has been fixed.

## What was wrong

`CoQ-PP_26-062` (J31122501) credits five microbiological determinations to the Institute's
`231/0394/26 (Racno trimiran cvet)`. The citation filter rejected any document string
containing a bracket — the rule that keeps OCR prose out of the CoA Doc. Code column — and
so the whole citation was dropped. The five results fell to the red **Certificate to be
located · Work Order** row while the Institute was already cited on the same page for
parameters 10, 11 and 12.

The parenthetical is not prose. It names **which product** the certificate covers, and
that is the distinction OI-39 turns on: the laboratory's own pages give J31122501 two
products, *Рачно тримиран цвет* against *Тримиран цвет*. Throwing it away was not an
option, and neither was letting it suppress the code.

## What changed

`coq_build.js` now tests the **code**, not the raw string. `docCode()` strips a trailing
parenthetical and `docNote()` keeps it; `codeShaped()` applies its existing guards —
length, `n/a`, `in-house`, a bracket anywhere else — to what `docCode()` returns. Section
03 prints the code and sets the note beneath it in the reference column's own face, so the
citation reads as a code and the product qualifier is still on the page.

Checked against the strings the filter is there to refuse: `n/a — Purely Plant in-house
CoA (see route)` is still rejected, and so is the OCR sentence *identity by the HPLC
cannabinoid profile on this certificate*. `231/0394/26 (Racno trimiran cvet)` is the only
document in the whole set the old rule was rejecting.

## Result

`CoQ-PP_26-062` now credits the Institute with parameters **9, 10, 11, 12** and carries no
Work Order row. Every format rebuilt and checked, on the page and in the PDF text layer.
Nothing else moved: of 172 documents, 171 differ only by the one new style rule.
