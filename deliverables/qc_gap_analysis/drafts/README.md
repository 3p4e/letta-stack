# Draft Certificates of Quality — Tranche 1 and Tranche 2

Nothing in this folder is a certificate. Every document here is a **draft**:
watermarked DRAFT, unsigned, with the conformity statement unticked. None has
been issued and none may be filed or sent as though it had.

## The red brackets

**Anything printed in red inside square brackets is not held by the desk and has
to be completed or confirmed before the document is issued.** Every draft says so
in its own footnote, so the page explains itself away from this README.

Two different things carry the marker, and the second is the one worth knowing
about:

- **a controlled blank** — the desk holds no result for that line, so it prints
  `[—]`. Before, a blank printed as a bare em dash in the same muted grey as a
  measured `N.D.`, in the one column where those two mean opposite things;
- **a value the desk cannot stand behind** — the packaging construction and net
  fill weight, and the two approvers' names and credentials. Nothing in the
  compiler ever wrote those, so every draft was reprinting the master's worked
  specimen as though it were this batch's. They are marked rather than deleted:
  they are probably right, and confirming them is a person's job, not the
  compiler's.

The brackets carry the meaning on their own, so a greyscale photocopy loses
nothing; the red is emphasis. It is deliberately not the red of the DRAFT
watermark or of a failing result — a field still to be completed is not a
failure.

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
| `coq_draft_gaps.csv` | every blank line and every result that runs off the sheet |

`coq_draft_gaps.csv` is the working list. A blank is not a compiler fault: it is
the desk stating it holds nothing it may print on that line. **147 printed lines
are blank across the 22 drafts**, so no draft here is complete, and a further 76
printed results run past the edge of the sheet and would be cut off in print.

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
