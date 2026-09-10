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
