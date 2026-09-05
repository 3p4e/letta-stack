# The acceptance criteria were read wrong, and four batches were flagged that conform

> **REOPENED the same day, and the headline above is half right.** An adversarial pass over
> every determination on this page found a document no pass in this campaign had opened:
> **Purely Plant's own release specification.** `QCSP 001 v.03` — all 48 product
> specifications in `deliverables/imb_spec_pdfs/` — prints
> `TYMC | Ph. Eur. 2.6.12 cat. C | ≤ 10⁴ CFU/g` and **states no maximum acceptable count.**
> Ph. Eur. 5.1.4's own scope says the ×2 note does not automatically extend to a
> manufacturer's specification. So the four results below are **undetermined**, not
> conforming: they clear the pharmacopoeia and exceed QCSP 001 read as written. See
> **Reopened** at the foot of this page. The five confirmed exceedances are unaffected —
> they fail under every reading.

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


---

# Reopened · Purely Plant's own release specification

Written after an adversarial verification pass over all fourteen determinations above.
Twelve survived. **Two were refuted, and both refutations were checked against the
documents before being acted on.**

## 1. There is a manufacturer's specification, and no pass had opened it

The pharmacopoeial rule that governs everything above carries its own scope limit, and I
quoted it in this very file without following it: *a manufacturer's own specification means
what its own document says, and the ×2 interpretation does not automatically extend to it.*

`deliverables/imb_spec_pdfs/SPC_FINAL_ImB_PDF/**` holds **48 Purely Plant product
specifications**, `QCSP 001 v.03`, signed by the QC and QA Managers. **All 48 state the same
thing**, section 09 *Microbiological Purity | Микробиолошка Чистота*:

| Parameter | Reference printed | Criterion printed |
|---|---|---|
| TAMC | `Ph. Eur. 2.6.12 cat. C` | `≤ 10⁵ CFU/g` |
| TYMC | `Ph. Eur. 2.6.12 cat. C` | `≤ 10⁴ CFU/g` |
| Bile-tolerant gram-neg. | `Ph. Eur. 2.6.31 cat. C` | `≤ 10⁴ CFU/g` |

Two readings, and this register cannot choose:

* It cites **Ph. Eur. 2.6.12**, and 2.6.12's own *Interpretation of results* is exactly
  where the ×2 note lives. A specification that adopts a chapter arguably adopts how that
  chapter says to read it — `≤ 10⁴` means 20 000 and the four conform.
* It states **no maximum acceptable count**, and Purely Plant documents distinguish the two
  ideas when they mean to: the in-house CoA form prints `<10^4, max 50 000 CFU/g`. Read as a
  plain in-house ceiling, `≤ 10⁴` means 10 000 and the four are 1.20× to 1.90× over.

| Row | Batch | Certificate | TYMC | vs Ph. Eur. 20 000 | vs QCSP 001 as written |
|---|---|---|---|---|---|
| 35 | `GG1024_02` | `472/0863/25` | 19 000 | conforms | **1.90× over** |
| 75 | `CJ052501-1` | `949/1687/25` | 17 000 | conforms | **1.70× over** |
| 38 | `HPA1024_01` | `587/1066/25` | 15 000 | conforms | **1.50× over** |
| 57 | `GP0824_03` | `628/1129/25` | 12 000 | conforms | **1.20× over** |

They are back to **amber, as undetermined** — not cleared and not failed. New rule **R6**
reports exactly this band. The register's specification row is unchanged: row 2 says its
reference values are the Ph. Eur. release specification, and they are.

**Two further defects in QCSP 001**, both bearing on which reading governs, neither this
register's to settle:

1. It labels every microbiology row **`cat. C`** while printing 10⁵ / 10⁴. Ph. Eur. 5.1.8
   Category C is TAMC 10⁴ and TYMC **10²** — which is exactly what certificates
   `1220/2171/25` and `1221/2172/25` print. On that reading these results fail by two
   further decades.
2. **Ph. Eur. 2.6.12 has no categories.** It is the enumeration method; the categories live
   in 5.1.4 and 5.1.8. `Ph. Eur. 2.6.12 cat. C` cites a chapter for something it does not
   contain.

And the version in force on the test date is unestablished: header `QCSP_001_…_v.01`, footer
`QCSP 001 v.03`, signed **01.06.2026** — a year after the June-2025 testing.

**What this says about the campaign's method.** The typed-record design says a value only
means something next to the limit it is judged against, and this file then said a limit is
two numbers. Both are still true and both were still not enough. **The release criterion can
live in a third document that neither the certificate nor the register cites** — and it did,
in this repository, unread through fourteen correction passes.

## 2. The stability sheet disagrees with two of its own certificates

The `Stability Testing Programme` sheet has never been page-verified —
`CNP_PAGE_VERIFICATION_2026-08-31.md`'s "202 of 202" covers the Batch Release QC sheet only.
Against the CNP page reads, **eight of its ten rows match exactly and two do not**:

| Row | Certificate | Sheet held | Page reads |
|---|---|---|---|
| 16 | `ППК26037` | CBN **0.19**, remark blank | CBN **1.09**, over the certificate's `≤ 1.00 %` |
| 18 | `ППК26058` | Δ⁹-THC **0.29** · THCA **0.97** · Total **1.17** | **16.99** · **0.07** · **17.05** |

Row 16 is the worse of the two: a result over its printed limit sat on the stability sheet
as a comfortably passing 0.19 with the remark column blank, while Batch Release QC row 95
held 1.09, page-read and flagged. The workbook contradicted itself across two sheets.

**Row 18 is the one worth understanding.** `0.29 + 0.97 × 0.877 = 1.14` against a printed
1.17 — **inside the R4 tolerance.** The page's `16.99 + 0.07 × 0.877 = 17.05` is equally
consistent. Three corrupted values together reproduced the certificate's own arithmetic
proof. **R4 shows a document self-consistent, not correct**, and that belongs beside every
claim made for it.

Both corrected from the page reads; row 16's remark now matches its siblings.

## 3. The stability certificates' verdicts were never read

Four CBN comments said the certificate "carries no verdict of any kind."
`CNP_PAGE_VERIFICATION_2026-08-31.md` records that the CNP pages were rendered **cropped to
0.10–0.82 of page height**, and that `ППК26127`'s failure was found only on a **second,
uncropped** render because its ЗАКЛУЧОК heading ran off the bottom edge. The ЗАКЛУЧОК block
sits below the results table — below the crop. On **72 of 73** CNP certificates the region
where a verdict appears was never in the image.

The comments now say that. An absence nobody looked for is not evidence.

## What the verify pass did not overturn

Twelve of fourteen determinations survived unchanged, including all five confirmed
exceedances, all four stability-sample classifications as *not a release sample*, and row
218 as *not a result at all*. The five that need a deviation record are the same five.

## Open, restated

1. **QA to determine what QCSP 001's `≤ 10⁴ CFU/g` means**, and which version was in force
   on the test date. Four release results turn on it.
2. **QCSP 001's `cat. C` label** against its Category B figures, and its citation of a
   chapter that has no categories.
3. **Five deviation records** — rows 21, 72, 83, 88, 101.
4. **Page-verify the Stability Testing Programme sheet.** Two of ten rows were wrong and one
   of those was wrong in a way R4 cannot see.
5. **Re-render the CNP certificates uncropped** and read the ЗАКЛУЧОК region on all 73.
6. **The Purely Plant in-house CoA form**, which states a maximum acceptable count 2.5× the
   compendial one.
7. Row 122 — whether `производителска спецификација` `10²` is absolute.
