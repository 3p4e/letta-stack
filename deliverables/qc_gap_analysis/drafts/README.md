# Draft Certificates of Quality — Tranche 1 and Tranche 2

Nothing in this folder is a certificate. Every document here is a **draft**:
watermarked DRAFT, unsigned, with the conformity statement unticked. None has
been issued and none may be filed or sent as though it had.

## What the compiler writes, and what it must not

The owner's master is the document, and `../live_instrument/templates/ISSUE_COQ_README.md`
is the specification for what may go into it. The compiler writes the fields that
README lists — batch number, cultivation batch, strain, product code,
specification doc code, date of manufacture (the harvest date), packaging date,
issue date, the Total Δ⁹-THC assay and the CoQ number — plus the result cells and
the Section 03 laboratory cross-reference. **Nothing else.** Every parameter name,
every method and every other acceptance criterion is the master's and is left
exactly as it prints them.

A check runs on every build and is the reason to trust that sentence: master 24
rows against draft 24 rows, **zero** differences in the parameter and method
columns, and exactly **one** in the acceptance-criteria column — the bracketed
row-4 potency range, which the owner asked for.

### The two potency figures

Per the owner's ruling of 10.09.2026:

- the gold banner figure and the row-4 assay are **the same number, taken from
  the certificate** — they disagreed on all 22 drafts before it, by up to 3.76
  points;
- the acceptance **range** is a placeholder supplied separately, so both places
  that print it — the Section 01 "Potency" field and the row-4 acceptance
  criterion — carry it **in brackets**.

### The red brackets

A result the desk holds nothing for prints as `[—]` in red rather than the muted
em dash it used to share with a measured `N.D.` — the one column where those two
mean opposite things. The brackets carry the meaning and the colour is emphasis,
so a greyscale photocopy loses nothing.

**The three selection bands come from the specification** (owner, 10.09.2026).
Phenotype, chemotype and processing are product attributes, and the document that
states them is the issued QCSP 001 specification the certificate names in
Spec. Ref.; `spec_attributes.py` reads them off it, and 18 of the 22 drafts now
carry the phenotype their own specification prints — 6 Indica, 2 Sativa, 10
Hybrid — instead of the master specimen's `☒ Hybrid Indica dom.` on every lot. On
the four lots whose specification is not on file, every pill in every band is
unticked with its box marked. The Hybrid pill's dominance sub-label follows the
same document: a ratio where it prints one, and its own words, bracketed, where
it prints `TO BE DETERMINED`.

The packaging line is the specification's too, and identical on all 257 issued
specifications, so it is left exactly as the master sets it — and checked against
the specification's figures on every lot rather than assumed.

**Fields that still print the master's worked specimen**, because they are not on
the README's list and are the owner's to rule on: the two approvers' names and
credentials, and the page `<title>`, which is what a PDF carries as its `/Title`.

## Nothing runs off the sheet, and it is one A4 page

Owner, 10.09.2026: the results section must not overflow, and the certificate must
stay one A4 page.

The master gives the result column whatever is left after its four fixed columns —
83 px of 717. That holds `24.53` and `< 10`, which is what its worked specimen
prints; it does not hold what the laboratories print. `Conforms | Соодветствува`
is 124 px, `Одговара (Complies/Absent)` 134, `< 0,01 mg/kg — all 22 residues` 155,
and the identity result of three lots 594. Every one of them was cut off at the
edge of the sheet.

**No value is shortened.** The column is widened out of the slack the others are
genuinely carrying — measured by letting the table lay out at 3,000 px and reading
what each column then asks for: the number column wants 21 px of its 30, the
parameter column 287 of its 300, the method column 133 of its 146. That is 35 px
and no more, so the result column goes from 83 px to 110 and anything still too
wide **wraps** rather than running off. The acceptance-criteria column is not
touched: it is the owner's column and its width is what sets "Conforms to
monograph" on one line.

Wrapping buys width out of the page's height, and the page had none to give —
several certificates were already a few px past 297 mm before this, clipped by the
master's own `overflow:hidden`, because section 03 grows with the number of
laboratories a lot cites and nothing was watching it. Three changes pay for it, all
of them typographic and none of them touching a value: the result rows give up
their 0.5 px of cell padding (the 1.12 leading already separates them), a wrapped
result sets on 1.02 leading, and the one result that is a sentence rather than a
figure — the desk's Identification C wording, 130 characters across both alphabets
— sets at the size the document already uses for its second-language glosses.

Every one of the 22 drafts now has **no cell wider than its column, no content
below the footer, and one A4 page**; the worst case clears the footer by 5 px.
`build_coq_drafts.py` reports **0 results running off the sheet**, and the master's
24 rows still compare against the draft's with no difference in any text column.

*Standing question for the owner:* that Identification C sentence — `Conforms —
cannabinoids identified and quantified by HPLC | Соодветствува — идентификација и
квантификација со HPLC`, on 35 lots — is composed by the desk, not printed by any
laboratory, and it duplicates the method column of its own row. The other 60 lots
already print `Conforms | Соодветствува` for the same assertion. Say the word and
that cell goes back to one line.

## The two merged PDFs

`Tranche_1_CoQ_Drafts.pdf` (13 certificates) and `Tranche_2_CoQ_Drafts.pdf` (9),
one A4 page per certificate, in P-lot order, printed by
`live_instrument/print_coq_pdfs.py` from these same HTML files through the same
headless Chromium. `@page{size:A4;margin:0}` and a `.page` fixed at 210 × 297 mm
give exactly one page per document with no printer margin of its own, and
backgrounds are printed — the DRAFT watermark, the selection pills and the red of
every marked field are the document, not decoration.

**The typefaces are embedded, not linked.** The compiled HTML pulls Montserrat,
Roboto Mono and Orbitron from `fonts.googleapis.com`; a renderer that cannot reach
Google substitutes Liberation Sans, and a controlled document that changes
appearance depending on whether a third party is reachable is not one to hand a
regulator. So the faces are fetched once, **subset to the characters these 22
documents actually print**, and inlined — `house_fonts.py`, which the QCSP 001
specifications already use for the same reason — and Google is then blocked at the
network layer for the whole run, so the output is the same with or without a route
to it. 53 faces, 1,636 KB upstream, 222 KB after subsetting. The certificate needs
two things the specifications do not: **Orbitron**, which sets the banner, and the
**Greek** subset, because every sheet prints "Total Δ⁹-THC". The brand mark is
already a data URI in the master.

The ballot boxes (☒ ☐) exist in none of the three families, so they are set in the
renderer's own DejaVu — embedded in the PDF like everything else, so the file is
still self-contained.

    python3 deliverables/qc_gap_analysis/live_instrument/print_coq_pdfs.py \
        --chromium /opt/pw-browsers/chromium-1194/chrome-linux/chrome

Needs `poppler-utils` (`pdfunite`) and `fonttools==4.55.3` with `brotli==1.1.0`.

The drafts are compiled by
`live_instrument/build_coq_drafts.py`, which calls the Quality Desk's own
`fillCoq()` in headless Chromium. A document here is therefore the same document
a person gets by clicking the batch on the desk: same master
(`live_instrument/templates/_CoQ_MASTER_Template.html`), same verbatim results,
same controlled blanks.

    python3 deliverables/qc_gap_analysis/live_instrument/build_coq_drafts.py \
        --scope deliverables/qc_gap_analysis/tracker/coq_draft_scope_2026-09-10.csv

| file | what it is |
| --- | --- |
| `DRAFT_CoQ_<P lot>.html` | one A4 draft per production lot, 22 of them |
| `Tranche_1_2_CoQ_Draft_Set.html` | the same 22, one page each, print-ready |
| `coq_draft_gaps.csv` | every blank line, every result outside its band, every result that runs off the sheet |

`coq_draft_gaps.csv` is the working list. A blank is not a compiler fault: it is
the desk stating it holds nothing it may print on that line. **147 printed lines
are blank across the 22 drafts**, so no draft here is complete; 3 results fall
outside the band printed beside them; and a further 76 run past the edge of the
sheet and would be cut off in print.

Eighteen of the 22 drafts carry exactly five blanks, and all five are the same
five: identification A, identification B and foreign matter — whose in-house
certificate **has not been issued**, and whose microscopy was never performed —
plus aflatoxin B₁ and ochratoxin A, which the certificate does not report
separately from the aflatoxin sum. None of them is a transcription anyone can do
today. Read `../tracker/COQ_DRAFTING_2026-09-10.md` and
`../tracker/V20_RECONCILIATION_2026-09-10.md` before doing anything with these.

Which lots are in scope, and why the other 28 delivered batches of Tranches 1
and 2 are not, is recorded batch by batch in
`../tracker/coq_draft_scope_2026-09-10.csv`.
