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
