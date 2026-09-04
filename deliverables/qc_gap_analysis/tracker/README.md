# CoQ_Analysis_Master_v3.xlsx — the owner's tracker, reflowed

Derived on 02.09.2026 from the owner's `CoQ_Analysis_Master_v2.xlsx` (Drive
`1NPq8O3Q60qvTw3469np43RF5k8wkU0Fx`, version of 02.09.2026 09:15). Two changes,
nothing else:

1. **Every certificate cell reads one document per line**, in the form the owner
   set on `CoQ Parameter Tracker!L24`:

       100-2-K-26, (09.04.2026) [FHM-K];
       100-3-K-26, (09.04.2026) [FHM-K]

   — 685 cells on the tracker sheet. Codes that contain spaces
   (`NGP-QCG-SOP-024 F3`, `NO-DOC-CODE (Report of Analysis)`) are kept whole.
   Cell fills, fonts, widths and wrapping are untouched.

2. **The glued sub-lot prefixes are stripped from the certificate codes** —
   `1_ППК26067`, `1_2362-2026`, `1_308-0552-26`, `2_051-6-K-26`, `2_051-6-LoD-26`,
   `02_ППК26113`, `02V_ППК26111` (39 occurrences) — and the digit goes back where it
   belongs, the batch: the `eCOA Document Index` rows for those seven documents now
   read `FB012601_1`, `GRC102501_2`, `JD012603_02` and `JD012603_02V`, and the
   single-lot batch `FB012601` reads `FB012601_1` on every sheet. `10802_2845-2` keeps
   its underscore: that is the State Phytosanitary Laboratory's own code. The merged
   rows `GRC102501` and `JD012603` on the tracker and missing-parameters sheets keep
   their names — they already list all their lots in the P-batch column.

The content of the tracker (which certificate is credited to which parameter) is
the owner's and is not changed here; `review/TRACKER_TRUTH_CHECK_2026-09-01.md`
records where it disagrees with the desk.

# CoQ_Analysis_Master_v6.xlsx — the tracker as flat tables

Built 02.09.2026 by `build_tracker_v6.py` from v3 (the owner's content) and the desk's
record (`../coq_artifact_data.json`: release register at chain step 19, page reads of
31.08.2026, 12-month re-analyses). It replaces the v4 and v5 layouts, which stacked
certificates inside merged batch blocks; those files are withdrawn (they remain in the
branch history).

Structure rules, every sheet:

- one header row, an autofilter on it, panes frozen under it; **no merged cells in any
  data region** — a batch that has six certificates has six complete rows, its identity
  repeated, never merged down a block;
- one value per cell; dates are real dates (DD.MM.YYYY), numeric results are numbers with
  the certificate's printed precision, qualitative results are text (`Conforms`, `absent`,
  `<LOQ`, `N.D.`);
- the state of a cell is carried by the standard Good / Neutral / Bad fills (legend on the
  `Read Me` sheet); the mark is always a plain ✓ or ✗;
- A3 landscape, one page wide, header row repeated on every printed page.

| sheet | one row per | columns |
|---|---|---|
| `Read Me` | — | purpose, sheet guide, legend, conventions |
| `Batch Coverage` | batch (81) | CU, P, strain, status, ✓/✗ for each of the 12 parameters, missing (n), missing parameters, certificates (n), labs present |
| `CoQ Parameter Tracker` | batch × certificate (253) | CU, P, certificate, date, lab, kind, then one column per determination (21) holding the value that certificate reports; blank = not credited for that parameter |
| `Results Register` | batch × determination × certificate (1 726) | CU, P, #, parameter, determination, mark, result, acceptance criterion, certificate, date, lab, kind, note |
| `eCOA Document Index` | document (253) | P, CU, lab, laboratory, kind, certificate, date, document type, parameters covered, values on desk ✓/✗, filename |
| `Parameters` | determination (21) | method, global acceptance criterion, source, tracker column |
| `Summary Dashboard` | — | the owner's aggregate, unchanged |

Legend (fill · mark): green ✓ certificate (eCoA or iCoA) and value on the desk · amber —
certificate credited but no value on the desk for that determination · orange ✓
stability-timepoint certificate (not a release result) · grey ✓ in-house document only
(not an eCoA or iCoA, not coverage for a release certificate) · red ✗ no certificate.

Which certificate is credited to which parameter is the owner's (v3, unchanged); the
counts agree with the owner's dashboard (287 batch × parameter gaps). Where the desk holds
no value from a credited certificate — most often Identification B on CNP certificates,
Total CBN on the 2025 CNP certificates, Aflatoxin B₁ and Ochratoxin A on Institute of
Public Health certificates that report only the aflatoxin sum — the cell says so (amber
—) rather than inventing a value.

# CoQ_Analysis_Master_v7.xlsx — the block layout, with the criteria enforced

Built 02.09.2026 by `build_tracker_v7.py` on the Head of QC's specification
(`CoQ_Tracker_v7_rebuild.gs`). It is the v6 workbook plus the sheet
`CoQ Parameter Tracker v7`; v6's flat table is kept beside it as
`CoQ Parameter Tracker (flat)` so the two can be compared, and every other sheet is
carried over unchanged.

The block rule:

- **one testing instance = one block of two rows** — the result(s) on the top row, the
  certificate that reports them on the bottom row. A batch holds as many blocks as it has
  testing instances, so a parameter tested twice on two dates gets **two blocks**, never
  two text lines inside one cell. Verified: 122 blocks, 1 464 parameter cells, none
  holding more than one certificate or more than one line;
- a parameter's certificates are taken in **ascending date order**, so the n-th block is
  the n-th round of testing; a parameter tested once is empty in the later blocks;
- **#1–#8 and #12** use `Result | eCOA ref | ✓/✗`, each merged across the block's two
  rows; **#9, #10, #11** give each sub-determination its own column on the top row, with
  the certificate merged beneath;
- the batch identity and STATUS are merged down all of the batch's blocks, and the whole
  batch is boxed with a thick border, each block separated by a hairline;
- **acceptance criteria sit in header row 3** and are enforced.

## One batch is one lot

Three joins had to be got right, and each was a real defect while it was wrong:

- **The index is joined on the P batch, never on the CU code.** Four CU codes carry two
  tracker rows (an original and the August re-analysis) and three lots share a CU code
  while having P batches of their own, so a CU join pulled another lot's certificates into
  the batch. An asterisk the owner puts on some CU codes is folded away for the join.
- **Tracker rows that share a CU and a P batch are merged into one batch** (81 rows → 77
  batches). They are the same lot, which the owner had to split across two rows because a
  flat table cannot show two rounds of testing; the block layout can. A lot's coverage is
  therefore the union of both rows' certificates, which is why the parameter gaps read 261
  here against the 287 of the split rows.
- **Certificate codes are matched on the folding key**, since the tracker and the index
  spell the same code with different Cyrillic and Latin letter forms.

One lot is left as the owner has it: `JD112501＊` carries an asterisk and no P batch of
its own, and its certificates are indexed under P060212.

## Why a credited certificate is silent

An amber cell no longer says only "no result on file". It names which of two different
problems it is, and the **Credit Audit** sheet lists every one of the 279 pairs with the
action it needs:

| finding | rows | meaning | action |
|---|---|---|---|
| not on this certificate | 191 | the document was read and carries no such row | move the credit to the certificate that does report the parameter, or record why it stands |
| not ingested | 88 | the desk holds no value from this document at all | re-extract it; the batch cannot reach a CoQ on that parameter until then |

Two patterns account for most of the first kind, and each was checked against the desk
before being written down:

- **The Farmahem pair is credited jointly, not backwards.** For every `051-x` and `100-x`
  lot the tracker credits *both* the `K` and the `LoD` certificate for #3–#6 *and* for #8.
  The desk shows the split cleanly: `051-1-K-26` holds Identification C, THC, CBD and CBN;
  `051-1-LoD-26` holds loss on drying, and nothing else. So each certificate of the pair
  looks silent for the half it does not carry — 73 rows. Splitting the credit so each
  certificate is credited only for what it reports clears all of them.
- **The older CNP report has no Identification B row; the newer one does.** 55 CNP
  certificates were read and carry no microscopy row, which is 55 of the audit rows. But
  12 CNP certificates — the ППК26110–ППК26119 and ППК26127–ППК26128 series of 30.06 to
  21.07.2026 — *do* report it, and the desk holds "Conforms" from each. So this is a change
  in the laboratory's report format, not a laboratory that never performs the test: the
  credit is wrong on the older series only, and must be kept on the newer one.

Of the "not ingested" rows, 30 documents are involved: 6 CNP certificates, 22 Institute of
Public Health certificates (the 2357–2365 and 304–312 series of 2026, a single systematic
gap) and 2 in-house NGP forms.

## On file, but not credited

A document that covers or reports a parameter while the owner's tracker does not credit it
there is still shown as a testing instance — greyed, marked `•`, its reference suffixed
"on file, not credited" — but it is **never counted as coverage**: what discharges a
parameter stays the owner's judgement, so the gap counts are unaffected. There are 16 such
instances across 11 batches, mostly CNP certificates of 30.06, 06.07 and 21.07.2026. They
are worth a decision: either credit them on the tracker or record why they do not count.

## The conformance check

Row 3 carries the global acceptance criteria of the `Parameters` sheet — the controlled
list of what is tested for QC batch release and CoQ compilation. The check is the
Quality Desk's own (`live_instrument/script.js`: `magnitude`, `acceptanceLimit`,
`overLimit`, `undetBand`), so the workbook and the desk cannot disagree:

| verdict | shown as | rule |
|---|---|---|
| out of specification | result in **red** | the value provably exceeds its criterion |
| undetermined | result in **amber** | a counted microbiological limit printed `≤ 10ⁿ CFU/g` is judged against **2 × 10ⁿ** (Ph. Eur. 5.1.4); between the printed limit and twice it the result is undetermined, not failing |
| not judged | plain | `ND`, `<LOQ`, `<10`, `absent`, a range written with "and", or any prose annotation |

Only **release** results are judged. A stability timepoint above the criterion is named
separately in STATUS, because a stability result is not a release result.

On the 81 batches this yields **5 out of specification** (TYMC above 2 × 10⁴ on GG1024_01,
GP052501, HPA052501, OPM052501, CJ062501/2), **4 undetermined** (TYMC in the Ph. Eur. band
on GG1024_02, HPA1024_01, GP0824_03, CJ052501/01) and **3 batches with a stability CBN
result above the release criterion** (GP0824_02, GP0824_03, GP062501) — the same counts the
release register and the CI gate hold. A scan of the whole register finds no further
exceedance.

## Rebuilding it inside Google Sheets

`CoQ_Tracker_v7_rebuild.gs` is the corrected Apps Script: paste it into the Sheet
(Extensions ▸ Apps Script) and run `buildTrackerV7`. Four corrections to the first draft,
each of which would otherwise have produced wrong output:

1. **Columns are found by header name**, not by fixed position. The draft read v5
   positions (`D` params covered, `I` parameter values) plus a `K` batch-key column that
   no version had; run against v6 it produced empty blocks.
2. **Acceptance criteria are read from the `Parameters` sheet** instead of being
   transcribed into the code, so the tracker cannot drift from the specification.
3. **The Ph. Eur. doubling rule is applied.** The draft flagged the whole band above the
   printed count limit as out of specification, which would have turned the four
   undetermined results into four false failures.
4. **Only release results are judged**, so the three stability CBN results are reported
   as a stability observation rather than as three more false failures.

To make the script runnable in Sheets, v7's `eCOA Document Index` gains two columns:
`PARAMETER VALUES` (what each document reports, as the desk holds it) and `BATCH KEY`.
The script's parser was run over all 253 index rows: 223 with values, 30 without, all 162
sub-determination groups recovered, and its verdicts identical to the build's.

# CoQ_Analysis_Master_v8.xlsx — v8's readings in the block layout, criteria enforced

Built 02.09.2026 by `build_tracker_v8.py`. This is the convergence of the two lines of
work on the tracker, and it is the file to use.

| from | what it contributes |
|---|---|
| **v8** (PR #17, built from the eCoA database on the ingestion host) | the readings themselves — verbatim from the certificate, two independent reads, derived cannabinoid totals, the per-compound pesticide panel read as one result, and a vocabulary that never calls an accredited certificate silent |
| **v7** (this line) | one two-row block per testing instance, the acceptance criteria in header row 3 enforced per Ph. Eur. 5.1.4, the lot join on the P batch, the merge of an original and a re-analysis row into one lot, and the Credit Audit |

## The merge rule

v8's reading wins where it has one, because it is verbatim from the page. **Where v8
reports no value but the release register or a page read holds one, the register value
stands** and is marked `ᴿ`. "Not ingested" is a statement about v8's corpus, not about the
certificate, and a verified result is never dropped by a rebuild.

That was checked before adopting anything: of the values both sources hold, **754 agree**
once decimal commas, unit suffixes and Cyrillic connectives are normalised, and **none
contradict**. v8 supplies 255 values the desk lacks; the desk supplies 133 v8 lacks.

| mark | meaning |
|---|---|
| plain | v8's reading of the certificate |
| `ᴰ` | a total the compiler derived from the free and acid forms because the laboratory printed none (57 cells) |
| `ᴿ` | held by the release register or a page read of 31.08.2026, not by the eCoA database (141 cells) |
| `held for review` | the two independent reads disagreed; a person must confirm from the page (3) |
| `not on this certificate` | the document was read and carries no such row (130) |
| `not ingested` | the database holds no read of that document at all (12) |
| `— MISSING —` | no certificate covers the parameter for that lot |

## What changed against v7

Silent credited cells fall from 161 to 63, and the Credit Audit from 279 rows to 144 —
v8's readings close 98 of them, the CNP Total CBN derivation being the largest single
group. Coverage and conformance are unchanged: 261 parameter gaps, **5 out of
specification, 4 undetermined, 3 stability results above the criterion**, on 122 blocks
over 77 lots. The conformance check runs on v8's verbatim strings, decimal commas and
`x 10^4` notation included.

## Credit corrections applied at build time

Two corrections to the credit table, each applied only where the evidence is explicit,
each listed row by row on the **Credit Corrections** sheet, and **neither written back to
the owner's workbook**. A removed credit does not remove the document: it still appears as
a testing instance, marked `•` and "on file, not credited".

| rule | removals | evidence |
|---|---|---|
| **R1 — the Farmahem pair** | 71, over 27 lots | the pair was credited jointly for #3–#6 *and* #8, while the `K` certificate reports identification C, THC, CBD and CBN and the `LoD` certificate reports loss on drying alone. Each now keeps only what it reports. |
| **R2 — CNP identification B** | 61 | credited to CNP certificates that carry no microscopy row. Removed there, **kept** on ППК26110–26119 and ППК26127–26128, whose newer report format does carry it. |

**The consequence of R2, stated plainly: gaps rise from 261 to 318.** Fifty-one lots now
have no evidence at all for identification B, where before they had a credit that the
certificate did not support. That is the honest state, and it is what the issuance plan
already foresees — those lots need an in-house iCoA for identification A and B. The
Credit Audit falls from 279 rows to **12**, because a silent credit is now either
corrected or a real task.

## Work Order — what no rebuild can fix

The **Work Order** sheet carries the 9 remaining tasks, each naming the document, the lot
and the parameters it blocks:

- **6 documents to re-extract** (`not ingested`): ППК25118, ППК25257, ППК25368, ППК26031,
  100-3-K-26 and 1625-2026. Each blocks Total CBN or identification C for its lot; two
  independent reads at 300 DPI, as the runner does.
- **3 figures held for review**: the two reads disagreed and a person must confirm from the
  page — Total CBN on the NGP forms of BSS052501 and GP062501, identification C on
  100-1-K-26 for J31112501.

## v9 — the verified build, slimmed for Drive

`build_tracker_v8.py --v9` writes `CoQ_Analysis_Master_v9.xlsx`: the v8 content after
the page-by-page truth check (`review/V8_TRUTH_CHECK_2026-09-02.md`), with the Results
Register, the flat tracker and the eCOA Document Index left out — they stay in v8 here.
Two build changes keep the file small enough to upload through the Drive connector
(102 KB against v8's 3.5 MB): a block that carries nothing writes no cells, and a merged
range is filled on its anchor cell only, which is the cell Excel and Google Sheets read.
Coverage, conformance and every value are identical to v8.

## Rendering

v8 prints the page verbatim, which mixed decimal commas with decimal points and repeated
the unit the column header already states. The separator and the trailing unit are
rendering, not measurement, so both are normalised — 0 cells now carry a decimal comma or
a trailing unit — and everything else stands as the laboratory printed it.


## v10 — the 30 IJZ-MB certificates of 31.08 and 01.09.2026 (04.09.2026)

Thirty microbiology certificates the Head of QC added to the Drive folder on 04.09.2026
were ingested into `eCOA_DB` (run 2, `ingestion/ecoa_runner/CORPUS_RUN_PLAN.md`) and read
twice at 300 DPI. `new_instances_from_records.py` turns the reconciled records and the split
manifest into `new_instances.json`; `build_tracker_v8.py --v9` reads it and:

- credits each certificate to #9 on its lot as a new testing instance, in date order, with
  the values the two reads agreed on — 29 of 30 read clean on every row; one row
  (P060432, bile-tolerant gram-negative) is `held for review` and sits on the Work Order.
  P060262's held row was ruled by the Head of QC on 04.09.2026 (`decisions_2026-09-04.tsv`);
- opens a lot row with no CU code for the three P batches the owner's tracker does not
  carry (P060102, P060342, P050142), each with a Work Order task to record the lot;
- marks #9 ✓ on **Batch Coverage**, recounts the missing list, the certificate count and
  the laboratories per lot, and recomputes the **Summary Dashboard**;
- rebuilds the owner's **Mikro CoQ Parameter** sheet (`--mikro=<the owner's workbook>`)
  from the tracker: the same lots, the identity columns and the #7–#12 blocks.

The laboratory prints the zero of a P-number as a letter O (`PO60052`); both batch
normalisers fold it, and `build_artifact_page.py` / `extract_artifact_data.py` produce
the published page from the workbook. The conformance picture is unchanged: five out of
specification, four undetermined, three stability exceedances — the new certificates are
all within their criteria, and where a lot's earlier TYMC was out of specification the
new instance stands beside it as a later round, not in place of it.


### The iCoA rule (Head of QC, 04.09.2026) — `--icoa`

Identification A (appearance) and B (microscopy) are tested at Purely Plant together with
foreign matter, at the date of packaging, and **one iCoA per batch** carries the three
results for release. Identification C conforms to the ImB specification and is referenced to
the certificate that carries the cannabinoid assay (#4), which the desk already credits; the
tracker prints it as "Conforms (ImB spec.)".

With `--icoa` every lot receives one in-house testing instance for #1, #2 and #7, referenced
to its planned iCoA number (`iCoA-PP-YYYY-NNNN` from the issuance plan; "iCoA — to be issued"
where the plan has none) and dated "packaging date — to record", because the packaging date
is not on the desk. Foreign matter is "Conforms" by the declaration of 13.08.2026, except
FB032601, where ППК26127 reports 0.08 % (Не одговара): held for the Head of QC and on the
Work Order. The **iCoA Issuance** sheet is the chronological issuance list: one row per batch in the
order of the release basis date its initial-release CoQ follows (the issuance plan of
31.08.2026), with the planned number (`iCoA — to be issued` where the plan assigns one at
issue), what the iCoA carries, and the cannabinoid-assay certificate that covers
identification C — the assay certificate itself, never a loss-on-drying certificate. Batch
Coverage marks in-house-only coverage in grey, as v6 did. Coverage moves from 0 to 52
complete lots of 84; conformance is unchanged.


### CNP document codes, and the retest series (Head of QC, 04.09.2026, second ruling)

Where a CNP certificate reports identification A, B or foreign matter (the report format
of ППК26110–26119 and ППК26127–26128 does), its document code is the CoQ's reference for
them and the iCoA covers only what CNP did not test; where CNP reports all three, no iCoA
is needed (11 lots). FB032601's CNP foreign matter reads 0.08 % (Не одговара): it is
credited as reported and raised on the Work Order as "non-conformance reported" — a
deviation / OOS record is needed before that CoQ can issue. Farmahem: identification C is
the K (potency) certificate.

The **iCoA Issuance** sheet then carries a second series: one iCoA per batch, same scope,
for the QP's retesting campaign (medical use, GACP product / API), in the order of the
additional-testing CoQ each belongs to. The reissued CoQ carries a new cannabinoid assay (#4–#6) and
new mycotoxins (#10); #8, #9, #11 and #12 are carried forward from the initial testing;
identification C is the new Farmahem K certificate. Each retest row names the retest assay
and mycotoxin certificates on file (the Farmahem 197-series K and M of August 2026: 20 lots
with both, 1 with the assay only) and is "pending" where they are not. A retest iCoA is a
new document with a new number in the year of issue — never the initial iCoA's number,
which the plan of 31.08.2026 had reused.
