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

## The universe around the 61 — the owner's ruling of 31.08.2026

Three corrections from the owner, later the same day, that extend — without
contradicting — everything above:

- **The 48 packaged lots are Tranche 01 and Tranche 02 only** — 19 + 29 — not the
  whole of production, which now stands at more than 80 batches. **Every batch on
  record gets one initial CoQ, first to last**; batches past Tranche 02 have no
  packaged lot, grade or number assigned yet, so their CoQs are carried as
  *predicted* — a CoQ number is copied from the issuance record at issue, never
  computed in advance.
- **The 12-month cannabinoid + mycotoxin retest programme is universal, and every
  batch gets a CoQ reissue** — starting from the beginning of Tranche 01/02: the 13
  numbered additional-testing CoQs (`0027 … 0039`) are the ones already due; the
  remaining 35 of the 48 are predicted at packaging + 12 months, and every later
  batch at release + 12 months. (Per the convention above, none of these is labelled
  "retest" — each is an ordinary sequential CoQ.)
- **The CoQ SOP has been in use since 11.05.2026, and no iCoA or CoQ may print an
  earlier issue date — nor a later one than the day it is signed.** The window is
  two-sided: nothing could have been issued before the SOP came into use, and a
  document is never post-dated, so every printed issue date lies in
  [11.05.2026 … the day of issue]. The plan's per-CoQ dates are **packaging dates** — the basis of the
  numbering series (`CoQ-PP-2025-…` is the 2025 *packaging* series) — never issue
  dates. The schedule therefore shows, per CoQ, the basis date and the earliest
  permissible issue date: the SOP date, the newest document the CoQ cites, or (for an
  additional-testing CoQ that cites nothing yet) the 12-month due date, whichever is
  latest. QC sets the real date at issue.

Two register identities resolved on the way: six release-register blocks keyed by a
packaged-lot P-number (`P060152, P060212, P060242, P060352, P060382, P060402`) are the
Farmahem 197-series re-analyses **of plan lots** (`J31102501, JD112501, OPM122501,
FB012602, SCR012603, GG012603` — matched by the plan's own packaged-lot numbers), not
separate batches; their results fold into the lot. `P160012/22/32` and `P060332`
match no plan lot and stand as their own entries on the record.

**Corrected on adversarial review, the same day.** The in-house certificate count
first published for this universe (137) was wrong three times over — a dedup key on the
packaged lot, which a predicted CoQ does not have; an is-this-a-reissue test that sent
predicted *initial* releases down the retest route; and release-time CNP coverage being
allowed to excuse the same determination on a reissue a year later. **The routing
requires 224 in-house certificates: 71 Ident A + B and 153 foreign matter.** Full
account in `review/COQ_SCHEDULE_2026-08-31.md`.

And one finding the extension exposed: **five issued additional-testing CoQs —
`0029` (GG1024), `0033` (OMP1024_01), `0036` (GP0824_03), `0037` (OPM1024_03),
`0039` (MB0824_05) — cite no 197-series certificate on file.** The plan records their
retest dates; the certificates never reached the file. Same defect class as GG1024's
initial testing: locate the physical certificates, scan, upload. Conversely, 12
batches are re-analysed already — the 197-series pair is on file — which certifies the
cannabinoid and mycotoxin half of their reissue and **nothing else**: a 197-К carries
Total Δ⁹-THC, CBD and CBN, its М sibling the six mycotoxins, and identity and foreign
matter are outstanding on every one of them. Under this folder's own rule — *a CoQ must
never carry a result or a conformity assertion that has not been certified* — they are
first in the queue, not issuable. A thirteenth lot, **P060332**, has the same pair on
file but is not in that queue at all: its cultivation batch, `CC012601/1`, appears in no
register and no plan, and a certificate of quality cannot be issued for material whose
identity is unresolved.

## Three further conventions from the owner, 31.08.2026 (evening)

- **The only certificates that legitimately carry 2025 issue dates are the old
  QCCoA 001 v.01/v.02 in-house CoAs** — the pre-SOP documents, with their own
  document codes and issuance dates. Each is **superseded** by the corresponding
  CoQ, whose doc code and issue date are assigned only from 11.05.2026 onward —
  after SOP v.03 came into use — in chronological order. No iCoA or CoQ ever
  prints a 2025 date.
- **CoQs may be issued in batches.** When the parameters missing from the
  outsourced certificates finally arrive, every CoQ they were holding up is
  issued together: **one date, sequential numbers, in chronological order** of
  the basis dates. The live instrument's batch-issuance desk computes the ready
  set (every determination in scope certified, dating window open), refuses a
  date outside any member's window, and assigns the sequence in one attributed
  operation.
- **Four per-scope iCoA masters** (from `ACME_SOP/QC_SPCs/pipe`, 31.08.2026)
  supersede the Variation F master for in-artifact compilation:
  `iCoA_P01-02_Appearance_Identification_AB`, `iCoA_P03_Identification_C_Chromatographic`,
  `iCoA_P07_Foreign_Matter`, `iCoA_P09_Microbiological_Purity`. Each master is a
  worked specimen: a compiled document blanks every cell that is the worked
  batch's measurement data (observations, retention times, masses, counts) to a
  controlled `—` — bench observations belong to the analyst's worksheet, the
  desk holds only the overall disposition — and strips the handwritten
  signature scans; criterion and method columns are specification text and
  stay. Notably, the P09 master itself prints the Ph. Eur. 5.1.8 **category C**
  criteria — TAMC ≤ 10⁵, TYMC ≤ 10⁴, BTGNB ≤ 10⁴ CFU/g, absences /25 g and
  /1 g — one more primary-document confirmation of the category-C ruling.

## Identification citation and the CNP full form — owner rulings, 31.08.2026 (night)

- **Identification criteria print the full monograph citation**, exactly as the
  house documents do: *Conforms to the monograph for Cannabis flos
  (07/2024:3028) in Ph. Eur. 11.0 | Согласно монографија за Cannabis flos
  (07/2024:3028) во Ph. Eur. 11.0* — determinations 1, 2 and 3, everywhere the
  schedule, workbooks and generated documents print an identification
  criterion. The 07/2024 monograph version is technically the 11.5 supplement
  of the 11th Edition; **Ph. Eur. 11.0 is the house edition label and is kept
  verbatim** (owner's choice over the technically-precise 11.5).
- **The CNP full Ph. Eur. form certifies identity and foreign matter, and the
  receipt register must say so.** Twelve CNP certificates print
  Идентификација (Макроскопија · Микроскопија) and Страни материи in their own
  results table (ППК26110–26119, 26127, 26128 — verified in the documents'
  table text; the routing already credited them). Because the release register
  has no column for identity or foreign matter, a column-derived "parameters
  reported" list read these documents as potency-only; the receipt register
  now appends *Ident A + B* and *Foreign matter* for exactly those documents.
  Page sampling across the rest of the series (ППК25050 release form,
  ППК26057 stability form) confirms the other CNP forms genuinely carry no
  identification — their batches correctly owe the in-house iCoAs.

## Batch disposition and amendment at the desk — 01.09.2026

Two QC acts were added to the Quality Desk. Both write to the overlay, attributed
to the operator and dated, and neither touches the baseline register.

- **Batch disposition** — *Released · Quarantined · Rejected · Under
  investigation*, recorded on the batch card with the person who decided it, the
  date and an optional note. A disposition is **not a certificate**, so the
  11.05.2026 SOP floor does not apply to it; a batch quarantined in 2025 was
  quarantined in 2025. What does apply is that **a decision is dated the day it
  is taken**: the desk refuses a post-dated disposition. A disposition is a
  standing state, not a number — it may be updated as often as the facts change,
  and each update is logged.

- **Amendment is for desk entries only.** A value typed at the desk — an attached
  result, a remediated reading — may be corrected: the desk asks for a written
  reason, keeps the superseded value with its own author and timestamp, and marks
  the chip *amended* so the correction is visible on the row, not buried in the
  log. A value **read off a certificate page is never amendable**, because the
  page is the record and the desk is not; where the desk disagrees with a page it
  says so in a note. Issued CoQ numbers, assigned iCoA references and their dates
  stay final under the same rule as before — a correction there is a new
  document, not an edit.
