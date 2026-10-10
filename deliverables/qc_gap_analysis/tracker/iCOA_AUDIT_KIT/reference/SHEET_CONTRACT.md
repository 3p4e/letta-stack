# The workbook, sheet by sheet

`CoQ_Analysis_Master_v56.xlsx`, 12 sheets. Read `tracker/README.md` in the repository for the
full prose; this is what a checker needs.

| sheet | what it holds |
| --- | --- |
| `Batch Coverage` | which test families each batch has |
| `CoQ Parameter Tracker v56` | the working sheet, one row per batch and series |
| `Batch Dates` | harvest, packaging, sampling |
| `iCoA Register` | one row per internal certificate — code, scope, the three in-house verdicts, the eCoA it cites |
| `CoQ Register` | one row per certificate of quality — issuable state, series, lot, THC, grade, specification |
| `CoQ References` | the documents each certificate cites, with sampling and receipt dates |
| `Potency Grades` | the grade window per lot |
| `CoQ Compilation` | the wide form — one row per certificate |
| **`CoQ Compilation (long)`** | **one row per printed cell — the sheet to work from** |
| `Result Supersession` | where a later result replaced an earlier one |
| `Parameters` | the determinations and their acceptance criteria |
| `Reference` | nine leaf sheets folded in on 14.09.2026, addressed through `_fold_<slug>` defined names |

## `CoQ Compilation (long)` — 18 columns, all literal

    CoQ code · Series · Batch (cultivation) · P lot · Strain · Date of issue · # · Parameter ·
    Method · Acceptance criterion · Result · Document · Issued · Laboratory ·
    Received by the laboratory · Status · Route · Also on file

3,956 rows = 172 certificates × 23 determinations. No formulas, so no recalculation is needed.
This is the authoritative join from a CoQ code to its lot, batch, strain, issue date and every
result with its provenance.

## The formula columns

**openpyxl stores no cached value for a formula**, so these come back empty and must never be
counted as missing data.

| sheet | formula columns |
| --- | --- |
| `CoQ Register` | `No.` · **`CoQ code`** · `Issue date (planned)` · `Rule date` · **`iCoA (register)`** · `iCoA issue date` |
| `iCoA Register` | `Issue date (planned)` · `Test date (packaging)` · `Packaging complete` · **`CoQ (register)`** · `CoQ issue (planned)` |
| `CoQ Compilation (long)`, `Result Supersession` | none |

Three ways through, in order of preference:

1. **Join on `Key` instead.** Both registers carry a **literal** `Key` — `CJ1024|I`,
   `P050202|R2` — lot and testing round. The iCoA-to-CoQ link needs nothing else. This is what
   `verify_fullness.py` check H does.
2. **Reconstruct the CoQ code from the rule its own formula states**
   (`tracker/build_tracker_v8.py:2727`): walk `CoQ Register` top to bottom, count the rows whose
   `Issuable` is `yes`, `allocated` or `ruled`, and the *n*-th is `CoQ-PP_26-%03d`. Reproduces
   the formula exactly, with no LibreOffice.
3. **Recalculate** through LibreOffice — needed only for the planned dates. In the repository,
   `tracker/verify_workbook.py::load_values()` does this and degrades safely when `soffice` is
   absent.

## Identity

* A lot and its starred spelling are **one lot**: `GG012601＊` is `GG012601`. The repository's
  `ingestion/common/batch_id.py::batch_key()` is the normaliser.
* A `Key` is `<lot>|<round>`: `I` initial release, `R`, `R2`, `R4`, `R5` retests. Derive the
  Series-to-round mapping from the register itself — both columns are literal and sit side by side.
* Document codes are compared after normalising separators and case
  (`tracker/tracker_data.py::nkey()`).

## The em-dash

`—` is the workbook's own "not applicable". It is **not** a value, and it is not the same as an
empty cell. Eleven Identification C results hang on that distinction.
