# Draft Certificates of Quality — Tranche 1 and Tranche 2

Nothing in this folder is a certificate. Every document here is a **draft**:
watermarked DRAFT, unsigned, with the conformity statement unticked. None has
been issued and none may be filed or sent as though it had.

## What the compiler writes, and what it must not

The owner's master is the document. This compiler fills **six things and nothing
else**, and a check in the build proves it: the batch number, the strain, the
date of manufacture (the harvest date), the packaging date, the 21 result values
in section 02, and the laboratory cross-reference in section 03. Every parameter
name, every method, every acceptance criterion and the whole of sections 01 and
04 are the master's and are left exactly as it prints them.

`rowdiff.py`-style verification on every build: master 24 rows, draft 24 rows,
**0 differences in the parameter, method and criterion columns**, 21 differences
in the result column — which is the value, and the only thing there to change.

A result the desk holds nothing for prints as `[—]` in red, so it cannot be read
as the muted `N.D.` it used to share a colour with. That is the one marker left,
and it sits in the result column, which is a field this compiler is asked to
fill.

**Fields that still print the master's worked specimen**, because they are not on
the list of what may be written and are the owner's to rule on: the document ID
(`CoQ-PP-2026-0005`), the issue date, the product code, the potency range and
Spec. Ref., the phenotype and processing chips, the headline potency placeholder,
the two approvers' names, the packaging construction and net fill weight, and the
page `<title>`. On a Grape Pie certificate several of those still read
*Amsterdam Amnesia* and *P060052*.

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
