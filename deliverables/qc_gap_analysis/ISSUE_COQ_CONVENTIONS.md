# ISSUE_COQ — the owner's CoQ issuance conventions

Transcribed 31.08.2026 from `Final_Docs/xCOAs/CoX_DES/ISSUE_COQ/README.md` in Drive
(folder `1MeyZQ9ViwBtHmEm0g_qYJsgnjQ1mZpKN`), which that folder generates from
**PP_Potency_MASTER_Spec.xlsx** (Master – All Batches, 48 rows), last revised 31.08.2026.
The machine-readable issue plan sits beside this file as `coq_issue_plan.json`, copied
verbatim from the folder's `_issue_plan.json`.

These conventions are the owner's and they supersede every predicted CoQ count in this
repository:

- **`_CoQ_MASTER_Template.html`** — master copy of the approved CoQ (blank controlled
  fields), with `cox.css` and the brand mark embedded.
- **A CoQ exists per packaged lot**, not per cultivation batch. 48 packaged lots, one
  initial-release CoQ each: **`CoQ-PP-{year}-{NNNN}`, numbered sequentially by packaging
  date** — `CoQ-PP-2025-0001 … 0022`, then `CoQ-PP-2026-0001 … 0026`.
- **13 further CoQs** — `CoQ-PP-2026-0027 … 0039` — issued for the batches whose
  12-month retest fell due, each an **ordinary sequential CoQ** carrying the results of
  the additional QC testing. **A CoQ is never labelled "retest"** — it is a certificate
  of quality for the batch at its date of issue.
- Every CoQ carries an **`iCoA-PP-{year}-{NNNN}` reference**, numbered in step with its
  initial CoQ.
- **Banner potency** is the actual Total Δ9-THC assay result for the batch, not the
  grade nominal. The ± tolerance is not shown on any CoQ; the grade acceptance range
  stays on the SPC and appears in the CoQ's Section 01 "Potency" field and as the row-4
  acceptance criterion.
- **Filled from the master spec**: batch № · cultivation batch № · strain · grade ·
  class · potency range · product code · specification doc code · manufacture date ·
  packaging date · Total Δ9-THC assay result · issue date · iCoA reference code.
- **Left as controlled blanks (`—`)**: quantitative results not present in the source
  data (Total CBD, CBN, foreign matter, LoD, microbiology, mycotoxins, heavy metals,
  pesticides), the outsourced-laboratory eCoA codes, and **both conformity tick-boxes**.
  *A CoQ must never carry a result or a conformity assertion that has not been
  certified* — QC transcribes these from the actual iCoA/eCoA and ticks one box at
  issue. The 13 additional-testing CoQs carry every result cell blank, including the
  identity rows and the assay, pending their own certificates.

What `build_coq_schedule.py` adds is exactly the part the folder leaves as controlled
blanks: for each of the 61 CoQs, the result and the source document code for every
determination the release register holds, so QC transcribes from a schedule instead of
hunting 248 certificates.

One conflict is recorded rather than resolved: the issue plan's acceptance range (grade
nominal ± tolerance, e.g. P050052 `19.80 – 24.19 %`) differs from the potency range the
signed QCSP 001 v.03 product specification prints for the same lot (`21.00 – 23.00 %`).
The issue plan is newer and drives the CoQs; the schedule carries both and flags the
disagreement per lot.

## Two findings recorded after adversarial verification, 31.08.2026

**A numbering collision.** The older deliverable `deliverables/qc_register/` assigns
`CoQ-PP-2026-0005` to GP0824_01 / P050102 (Grape Pie), while this plan assigns it to
P060062 (Permanent Marker) — and this plan's rendered document exists in ISSUE_COQ.
The plan governs; the `qc_register` deliverable's CoQ numbers are superseded and must
not be issued. One number, one document, forever.

**The rendered CoQ merges two specification rows.** The issued specimen's analytical
table carries ten §01 rows, merging QCSP 001 items 1 and 2 (Identification A and B)
into one appearance/identification row. The parameter schedule keys on the
specification's 23 determinations; whoever transcribes onto the rendered form carries
determinations 1 and 2 into its merged row together.
