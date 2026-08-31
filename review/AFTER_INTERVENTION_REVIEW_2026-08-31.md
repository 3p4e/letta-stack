# After-intervention review — 31.08.2026

Four commits were made on 31.08.2026 against the QC deliverables and the live CoX
Quality Desk: document generation from the owner's masters (`c020439`), the four
per-scope iCoA masters with batch issuance and the remediation desk (`df14ad6`), the
receipt rectification round including register chain step 17 (`b761e65`), and the full
monograph citation with the CNP full-form fix and the desk constants (`a45c537`).

This is the review of that work: every substantive claim re-derived from primary
sources by three independent read-only passes, each instructed to **refute** rather
than confirm. It records what held, what did not, and what was done about it.

## Method

Nothing was taken on trust from the work being reviewed. Each pass re-computed from
the sources — the register workbooks cell by cell through all 18 chain steps, the
`review/*_page_reads_*.json` campaign records, the vendored corpus text, the
certificates' own tables — and measured the live artifact in a browser. Where the
review and the work disagreed, the disagreement was itself checked: one of the
review's own corrections was wrong (see *Numbers*) and is recorded as such.

## What held

- **The register restore (chain step 17) is correct.** Traced through every committed
  workbook: `<LOQ`/`0.22` from the row insert, corrected to `0.22`/`< LOQ` by the page
  campaign at step 7, reversed by step 16, restored at step 17. The certificate's own
  results table and the page read both give Total CBD `0.22`, Total CBN `< LOQ`.
- **FHM2 → FHM3 changed exactly what it claimed**: 2 values, 2 comments, 0 fills,
  0 hyperlinks, 0 style or structural differences across all three sheets.
- **`fold()` is collision-safe.** 247 codes → 246 distinct keys (the one collision is
  the same lab reference with and without an editorial note). `nk()`, which it
  replaced, produced 24 collisions — every Farmahem К/М pair merged.
- **No page-read value is attributed to the wrong certificate.** 227 page-read records
  fold to 227 distinct keys; every receipt match is code-identical except the six rows
  whose code cell names two documents, and on each the embedded control-book number's
  batch equals the register row's batch.
- **The corpus pre-fill never crossed a batch.** All 15 not-page-verified in-house rows
  matched on their own P-number, each with exactly one candidate record, and
  `batch_canonical == batch_as_printed ==` the register's P-number in all 15.
- **The CNP full-form detection is exact.** 12 certificates, 12 register rows; no false
  positive, and a relaxed re-scan of all 73 CNP documents under every spelling and OCR
  variant found no missed certificate. `reported` feeds display and search only —
  no count, coverage partition or routing decision reads it.
- **Label orientation is arithmetically proven.** `thc = d9 + 0.877·thca` on 60/60 CNP
  records; `cbd = cbd_raw + 0.877·cbda` on 34/34; zero records consistent with the
  swapped reading. Uncertainty columns and specification strings are never rendered as
  results. 840 page-read values reconcile to the register modulo notation.
- **19 of 22 flag-dossier entries** check out against the register cells, the applying
  scripts' comments and the page reads — including all nine TYMC values and their
  multipliers and the four stability-arm findings.

## What did not hold, and what was done

| # | Finding | Disposition |
|---|---|---|
| **F1** | The full bilingual citation wrapped identification rows 1–3 to three lines, pushing the CoQ's **signature and approval block 107–142 px off the fixed A4 page** — invisible on screen and in print, on all 166 certificates. | **Fixed.** The document now prints the citation in a measured one-line form, `Conforms to mon. Cannabis flos (07/2024:3028), Ph.Eur. 11.0` ("mon." is the master's own abbreviation). Schedule, workbooks and the desk's detail table keep the full bilingual criterion. Re-measured over all 166: **0 certificates lose the approval block**; overflow returns to the master's own baseline (0–32 px, identical certificate for certificate to the short criterion it replaced). |
| **F2** | A corpus value rendered beside a page value for the same analyte because the two sources label it differently. On **ППК26037** — an amber, out-of-specification receipt — the page's CBN 1.09 % sat one line above the corpus's 0.19 %. | **Fixed.** Values now carry a canonical analyte identity; a corpus value is suppressed wherever a page read covers the same analyte, compared by magnitude so notation differences are not mistaken for disagreements. Six real disagreements survive and are recorded as corpus corruptions, shown on the receipt row and written up as finding A5 in `ECOA_RECTIFICATIONS_2026-08-30.md`. |
| **F3** | The receipt desk's value field could **destroy an existing page reading**: a value whose parameter already had one was silently dropped on write, and the failure rollback deleted readings it had never written. Reproduced twice in a browser, including by a plain double-click. | **Fixed.** The desk now refuses the collision with an explicit message naming the standing value (mirroring the remediation desk), rolls back only what it wrote, drops the container only when empty, stamps once per action, and tests the in-session overlay for duplicate codes. |
| **F4** | Three inaccurate statements in the flag dossier: "the closest call on the register" attached to the wrong certificate; the two `ГС` loss-on-drying ambers described a **conforming** 10.3 % as over a 10.00 % limit that does not govern them; "largest count" where it is the largest TYMC; and an inference presented as a source's words on `197-6-К/26`. | **Fixed.** The epithet moved to `472/0863/25` (19 000 against 20 000, and the generating rule is > 18 000); the `ГС` lines now state that the value conforms against the certificate's own `< 12`, the register's `≤ 12.00` and QCSP 001 §8's `≤ 12.0 %`, and that the amber records the twin-batch label defect and the reverse binding; the TYMC qualification and the attribution are corrected. |
| **F5** | Two register defects predating the chain: cell `L57` (`628/1129/25`) read `<10¹ and >10³` — a count below 10 and above 1 000 at once; row 239's code cell read `(not numbered)` although certificate `305/0549/26` exists and was page-read. | **Fixed as chain step 18** (`apply_gnb_range_and_number.py`, idempotent, refuse-on-mismatch): `<10⁴ and >10³` per the page, and the number written with its issuing laboratory. **The five results are deliberately not written** — transcribing results into the release register is a QC act against the physical certificate, and the artifact already carries them as page-read provenance. The receipt register consequently moves 247 → 248 documents, 232 → 233 page-verified. |
| **F6** | Step 17's record called step 16 "a misreading". It was not: step 16 followed `master_coa_table.tsv`, a derived export that genuinely transposes this one record — and **the export still holds it**. | **Fixed.** Step 17's docstring names the conflicting source and why two direct readings outrank a derived export (93 values swept, one disagreement); step 16 carries a supersession note and is otherwise left exactly as applied; `ingestion/coa_track/letta-imb-coas/exports/KNOWN_DEFECTS.md` warns anyone re-deriving from the export. The cell comment now carries the full history of the value. |
| **F7–F10** | Smaller defects: three IPH pesticide values were partial reads rendered as complete panel results; the one failing CNP certificate's verdict was the only verdict not rendered; the P03/P09 masters' lockup labels matched none of the filler's, so those scopes would have printed the worked specimen's header for another batch; a batch with two in-house certificates would have been resolved by file order. | **All fixed.** Partial reads carry their coverage qualifier in the label and tooltip; `verdict` added to the CNP labels; the filler accepts both label spellings and gives the foreign-matter master its section suffix; the corpus pool sorts by issue date and discloses the choice. |
| **F11** | Records contradicted by the night's work: the 197-7 account in the schedule, the "FHM2" sentence and its generator, README's two conflicting "current workbook" lines and its 13-step chain, a tier claim of T2 values where none exist, and a handover that presents the REST API as reliable. | **All corrected**, generator first where one existed. A new trap 13 records that a valid credential can be the wrong tenant and that RAGflow answers `code 102` inside HTTP 200. |

## Numbers

- Receipt register: **248 documents, 233 page-verified, 15 not** — all fifteen Purely
  Plant in-house rows, which have no outside page to read.
- Page-read values carried onto receipts: **1 318**, plus 267 corpus pre-fills, plus
  6 suppressed corpus corruptions.
- Verification coverage, measured independently: **1 033 of 1 073 populated result
  cells (96.3 %)** sit on a page-verified certificate.
- **A correction to the review itself.** One pass reported the `verified_map()`
  docstring's "59 false negatives out of 74" as wrong, measuring 65 of 80. Both are
  right about different things: 59/74 is the count against the implementation actually
  replaced, which paired `nk()` with a ППК-number fallback; 65/80 is bare `nk()`. The
  docstring now says which.

## Open items — for QC, not for this repository

1. **`L57` and row 239 want a look at the physical documents.** The corrected range and
   the written certificate number both come from the page-read campaign; the date of
   issue for `305/0549/26` and its five results are still to be transcribed from the
   certificate, and the amber on `L57` should be reviewed now that the value is possible.
2. **`master_coa_table.tsv` holds a known transposition** (`197-7-К/26`). Anything
   re-derived from it reintroduces the defect.
3. **`ППК26037`'s corpus record is corrupt on an out-of-specification value** (CBN 0.19
   against the page's 1.09) — the first corruption found on a failing result.
4. **A page-read key is stale**: `319-0586-25` was superseded by the register's
   `318/0585/25`. The evidence file is deliberately not edited; the key simply matches
   nothing.
5. **The CoQ master overruns its own page by up to 32 px** at the identification rows,
   independent of anything changed tonight — the approval block's last ~18 px sit under
   the footer strip. Worth a look when the master is next revised.
6. **The live RAGflow credential belongs to another tenant** and cannot read the working
   corpus; the local materialisations are canonical until a key for the owning tenant
   is available.
