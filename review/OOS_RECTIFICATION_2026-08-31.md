# The acceptance criteria were read wrong, and four batches were flagged that conform

31.08.2026 · rectification of the out-of-specification determinations in the eCoA
register documents, the workbooks and the published artifact.

---

## What was wrong

Nine TYMC cells in the release register were amber-flagged as exceeding their limit.
**Five of them do. Four of them do not**, and they had stood in a release register
flagged as failures.

Everything on this register that has needed correcting has had one shape: a value that is
right, sitting in a column that asks a different question. The Farmahem U column held
mercury under arsenic. Two date cells held the receipt date under a heading that says date
of issue. Row 260 holds a foreign-matter percentage twenty-five times inside its limit on a
batch the laboratory failed, because the operative half of that limit is not a number.

This is the same defect in the code that checks the register.

`magnitude()` in `ingestion/ragflow/validate_ecoa_limits.py` answers one question: *what
number is this measurement.* On `4,2 × 10⁴ CFU/g` it answers 42 000, and it is right. It
was then asked for the **acceptance criterion** as well — and an acceptance criterion
answers a different question, *what is the largest result that still conforms.* For a
microbial enumeration criterion written as a bare power of ten those two numbers are not
the same:

> Ph. Eur. 5.1.4, in identical PDG-harmonised wording USP <1111>, and again in the
> "Interpretation of results" text of Ph. Eur. 2.6.12 / USP <61>:
>
> *"The following interpretation should be applied: 10¹ CFU: maximum acceptable count = 20;
> 10² CFU: maximum acceptable count = 200; 10³ CFU: maximum acceptable count = 2000, and so
> forth."*

**×2 per decade.** `10⁴ CFU/g` means a maximum acceptable count of **20 000**; `10⁵` means
**200 000**. The factor exists because the criteria are order-of-magnitude limits and plate
counting is intrinsically imprecise — a rounding convention on the log scale, not a margin
to be stacked with anything else. It governs enumeration criteria only (TAMC, TYMC,
bile-tolerant Gram-negative bacteria in CFU/g) and never the "absence in 1 g / 25 g"
criteria for specified micro-organisms, which are absolute.

## Three multipliers were in play at once

| Where | Reads `10⁴` as | Authority |
|---|---|---|
| The register's specification row, `≤ 10⁴ (max 50 000)` | 50 000 (×5) | none found |
| Ph. Eur. 5.1.4 / 2.6.12, USP <1111> | **20 000 (×2)** | the harmonised interpretation note |
| `validate_ecoa_limits.py`, and every review document | 10 000 (×1) | the literal power of ten |

**The ×5 is not a transcription slip and it is not this campaign's.** `≤ 10⁵ (max 500 000)`
and `≤ 10⁴ (max 50 000)` are byte-identical in all twelve workbooks in the correction
chain, **including the owner-supplied baseline** `PP_Batch_Release_QC_Register_CORRECTED.xlsx`;
no correction script has ever touched row 5. The same figures are printed on the **Purely
Plant in-house CoA form itself** — `<10^5, max 500 000 CFU/g` and `<10^4, max 50 000 CFU/g`
on the GG1024, HPA1024 and OPM1024 in-house release CoAs, transcribed verbatim in
`ingestion/coa_track/letta-imb-coas/add_gg1024_rows.py`.

So the register faithfully copied a company document, and the company document is wrong.
**Correcting the in-house CoA form is a QA action, not a register edit** — and it is the
one item on this page that cannot be closed from here.

## The determinations, restated

Nine TYMC results, all page-verified twice, all against a printed criterion of `10⁴`, all
on certificates that concluded **ОДГОВАРА**:

| Row | Batch | Certificate | TYMC | Count | vs 20 000 | Determination |
|---|---|---|---|---|---|---|
| 21 | `GG1024_01` | `320/0587/25` | 4,2 × 10⁴ | 42 000 | 2.10× over | **out of specification** |
| 101 | `CJ062501-2` | `1032/1851/25` | 4,9 × 10⁴ | 49 000 | 2.45× over | **out of specification** |
| 83 | `GP052501` | `946/1684/25` | 3,6 × 10⁴ | 36 000 | 1.80× over | **out of specification** |
| 72 | `OPM052501` | `904/1589/25` | 3,3 × 10⁴ | 33 000 | 1.65× over | **out of specification** |
| 88 | `HPA052501` | `948/1686/25` | 2,6 × 10⁴ | 26 000 | 1.30× over | **out of specification** |
| 35 | `GG1024_02` | `472/0863/25` | 1,9 × 10⁴ | 19 000 | inside by 5 % | conforms — flag withdrawn |
| 75 | `CJ052501-1` | `949/1687/25` | 1,7 × 10⁴ | 17 000 | inside | conforms — flag withdrawn |
| 38 | `HPA1024_01` | `587/1066/25` | 1,5 × 10⁴ | 15 000 | inside | conforms — flag withdrawn |
| 57 | `GP0824_03` | `628/1129/25` | 1,2 × 10⁴ | 12 000 | inside | conforms — flag withdrawn |

A tenth, `163/0271/25` (`BG1024`, exactly 1 × 10⁴), conforms on every reading and was never
flagged.

**Row 35 is the closest call on the register.** 19 000 against a maximum acceptable count of
20 000 is inside by 5 %, on a value the laboratory reports to two significant figures. It
conforms as reported; confirming it against the raw plate count before releasing on that
margin is cheap and worth doing. The cell comment says so.

**Five batches still need a deviation record** — not ten. The finding that a laboratory
concluded ОДГОВАРА over its own printed criterion survives in full for those five, and it
is a finding about the laboratory's review step as much as about the batches.

## What the correction does *not* undo

**The superscript corrections of 30.08 stand.** Five certificates were recorded an exponent
too low, so a result over the limit read as one under it, and every one of those was
confirmed on the rendered page. Four of the five still turn a pass into a fail under the
correct arithmetic:

| Certificate | Register held | Page reads | Under ×2 |
|---|---|---|---|
| `320/0587/25` | 4.2×10³ | **4,2 × 10⁴** | out of specification |
| `904/1589/25` | 3.3×10³ | **3,3 × 10⁴** | out of specification |
| `946/1684/25` | 3.6×10³ | **3,6 × 10⁴** | out of specification |
| `1032/1851/25` | 4.9×10³ | **4,9 × 10⁴** | out of specification |
| `628/1129/25` | 1.2×10³ | **1,2 × 10⁴** | conforms |

The fifth is still a real transcription correction — the page says 10⁴ and the register
said 10³ — it simply does not change that batch's disposition. A register that records what
the certificate says is worth having whether or not the value happens to fail.

**Row 122 is untouched.** `1220/2171/25` reports TYMC 200 against a limit of `10²` printed on
its own certificate under `производителска спецификација` — a manufacturer's own tighter
specification, which the compendial ×2 reading does not automatically govern. If that
specification document does not itself invoke the Ph. Eur. interpretation, `10²` there is an
absolute 100 and 200 fails. **That is a judgment on the wording of a document this register
does not hold**, and it stays open.

**The four CBN cells are untouched, and they were never mis-stated.** Rows 53, 59, 95 and 97
are accelerated 40 °C / 75 % RH stability timepoints on which Δ9-THCA has decarboxylated and
the neutral cannabinoids have oxidised on to CBN. They are amber rather than red, and each
comment already said that whether an accelerated-condition sample must meet a release limit
is a question for the stability protocol. What was wrong was not the register but the two
places that read it — the validator reported them beside genuine release failures, and the
published page rendered them in the same red.

## What changed, where

### The register workbook
`deliverables/qc_gap_analysis/apply_acceptance_criterion_corrections.py`,
`PP_Batch_Release_QC_Register_LINKED_2026-08-31.xlsx` → `…_AC_2026-08-31.xlsx`

- `J5` `≤ 10⁵ (max 500 000)` → `≤ 10⁵ CFU/g (max 200 000)`
- `K5` `≤ 10⁴ (max 50 000)` → `≤ 10⁴ CFU/g (max 20 000)`
- `L5` `≤ 10⁴ CFU/g` → `≤ 10⁴ CFU/g (max 20 000)` — the column previously stated no
  maximum at all, so adjacent columns used two conventions
- four amber flags withdrawn, each with a comment saying what it was and why it went
- five amber flags confirmed, each with a comment saying the count, the maximum acceptable
  count, the ratio and the laboratory's verdict. **They previously carried no comment at
  all** — a flag that states nothing is only slightly better than no flag
- `K101` `4.9×10^4` → `4.9×10⁴`; notation only, same value
- two legend lines stating the interpretation rule

Idempotent, and it refuses a workbook whose cells differ from what was verified.

### The validator
`ingestion/ragflow/validate_ecoa_limits.py`

- new `acceptance_limit()` with the ×2 rule, the authority in its docstring, and doctests.
  It returns the compendial value and reports the register's own contradicting parenthetical
  in a `conflict` field rather than silently overriding it — the wrong number on the paper
  stays visible
- `magnitude()` is no longer used for limits anywhere
- **new rule R3**: a result above the criterion on a sample the register's own
  `Stability Testing Programme` sheet lists is reported separately and is *not* a release
  failure. Which certificates those are is read off the workbook, not hard-coded
- **R2 had two false-positive classes and now has neither.** It tested `"10" in text`,
  which is a substring test on a decimal and matched `0.10`, reporting four CBD percentages
  as suspect superscript misreads; and it read `< 10³ and > 10²` — a statement that a count
  lies between 100 and 1000 — as a measurement, when `magnitude()` sees only its first
  bound. R2 also now compares against the criterion's **printed exponent** rather than the
  maximum acceptable count, because R2 is about notation and notation is 10ⁿ

R1 findings on the register: **13 → 5**, with 4 moved to R3 and 4 withdrawn.
R2: **23 → 15**.

### The published artifact
`https://claude.ai/code/artifact/083f3abb-a6d3-469c-a8bd-7f52c9ddbe0b`

- `acceptanceLimit()` added, mirroring the Python; `overLimit()` uses it
- `magnitude()` gained the prose guard the Python already had. Without it, cell O218 —
  `COMPLIES (numeric value not present in captured source excerpt for report 1625/2026 — see
  Bundle cross-reference)` — parsed to **1625** and rendered as 406× over an aflatoxin limit
  of 4, on a cell whose first word is COMPLIES
- `overRelease()` distinguishes a stability timepoint from a release result; those four CBN
  values now read *stability timepoint* in amber instead of *over* in red
- the detail view names the maximum acceptable count a value was judged against
- the page now carries the register's cell comments — the verification audit trail — which
  it previously did not

Measured in the browser, before and after: **"Over own limit" 13 → 5**, batches showing an
exceedance **11 → 5**, zero page errors.

### And the artifact became rebuildable
`deliverables/qc_gap_analysis/build_register_artifact.py` +
`register_artifact_template.html`

The page was previously assembled from a JSON file that existed only in a scratch
directory. It could be read but not rebuilt — **and a page that cannot be rebuilt cannot be
corrected.** Everything it needs was already in the repository: the workbook, the five
`review/*_page_reads_2026-08-31.json` files that record which certificates were read in
which pass, and the iCoA CSV. It now reads them.

The rebuilt data reproduces the published page exactly — 80 blocks, 285 rows, 232
page-verified, 81 iCoA entries — differing only in the corrections above.

## Open, and owned elsewhere

1. **The Purely Plant in-house CoA form** states a maximum acceptable count 2.5× the
   compendial one. It needs correcting at source. Three in-house CoAs carry it (GG1024,
   HPA1024, OPM1024), and it is what the register's specification row was copied from.
2. **Five deviation records** — rows 21, 72, 83, 88, 101.
3. **Row 35's raw plate count**, before releasing on a 5 % margin.
4. **Row 122** — whether `производителска спецификација` `10²` is absolute.
5. **The bile-tolerant GNB column is looser than the documents under it.** It says `≤ 10⁴`
   where certificates `1220/2171/25` and `1221/2172/25` print `≤ 10²` and the in-house CoA
   prints `<10² CFU/g`. Which applies to a release is a QC decision.
6. **`Ph. Eur. 5.1.8` category.** The in-house CoA labels its microbiology "Ph. Eur. 5.1.8,
   category C" while printing TAMC 10⁵ / TYMC 10⁴. Noted, not resolved here — it is a
   question for the specification, not for a transcription pass.
