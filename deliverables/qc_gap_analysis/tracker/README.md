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
