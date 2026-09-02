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

# CoQ_Analysis_Master_v4.xlsx — one certificate per row, result | reference

Built 02.09.2026 on v3. The `CoQ Parameter Tracker` sheet is re-laid out; the other
three sheets are v3's, untouched.

- Every parameter column is split in two: **Result (as reported)** on the left, the
  **eCOA ref, (date) [Lab]** on the right, and **each certificate sits on its own
  row** — a batch with six cannabinoid certificates occupies six rows, its identity,
  status, labs-present and missing-parameters cells merged down the block.
- The results are the desk's, keyed on the certificate code: the release register
  (chain step 19), the page reads of 31.08.2026 and the 12-month re-analyses.
  Multi-determination parameters list each determination (`TAMC 1.6×10⁴ · TYMC
  1×10⁴ · GNB <10² and >10 · Salm. absent · E. coli absent`). A stability-timepoint
  certificate is amber and marked — its result is not a release result. `—` means the
  certificate is credited on the tracker but the desk holds no value for that
  parameter from it: the parameter is not on that certificate, or the certificate
  never entered the release register (the 21 listed in the truth check).
- Which certificate is credited to which parameter is the owner's, carried from v3
  unchanged.
- Sized to print: Calibri 8, wrapped, row heights fitted to the tallest cell, A3
  landscape, one page wide, header rows repeated, panes frozen at D4.
