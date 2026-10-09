# Grapes and Cream grade IV — two versions to choose from (08.10.2026)

**Decided 08.10.2026 (Head of QC with QA): A, 8.00 ± 0.80 % (7.20–8.79 %).** B is kept for the record only.

Head of QC, 08.10.2026: *"create additional set of documentation for GRC for 7.0% … and the COQ and iCOA with the
same codes and all else as for the 8.00% … me and QA will decide on the final spec grade either 7 or 8.0%"*.

| | A — 8.00 % | B — 7.00 % |
| --- | --- | --- |
| QCSP_001_GRC-IV_v.01 | 8.00 ± 0.80 %, window 7.20–8.79 % | 7.00 ± 0.70 %, window 6.30–7.69 % |
| product code | `GRC_THC8 : CBD1` | `GRC_THC7 : CBD1` |
| CoQ-PP_26-050 (initial, 7.05 %) | below the window | in the window |
| CoQ-PP_26-152 (retest, 7.50 %) | in the window | in the window |
| status | the main line since 08.10.2026 (register, KVM4, every package) | the 07.10.2026 grade, rebuilt for comparison |

The tolerance of B is ± 0.70, as set on 27.09.2026 (*"7 % plus minus 10 % of nominal value … 7 % plus minus 0.7"*).
Everything else is the same in A and B: certificate codes, dates, results, citations, iCoA-PP_26-050 and -095, layout.
B's sheet and CoQ pages are byte for byte the 7.00 pages of 07.10.2026; each B page reads as its A page except for the
grade fields (`tracker/build_grc_grade_options_2026-10-08.py`).

Each folder, PDF and Word:
- `QCSP_001_GRC-IV_v.01_GRC-IV_<grade>` — the sheet;
- `QCSP_001_GRC_v.01_Grapes_And_Cream_all_grades_GRC-IV_<grade>` — GRC-I, GRC-II and GRC-IV;
- `P060142_…_Initial_CoQ-PP_26-050+iCoA-PP_26-050+QCSP_001_GRC-IV_v.01` and `…_Retest_CoQ-PP_26-152+iCoA-PP_26-095+…`.

Once one is chosen: for B, `tracker/apply_grc_grade_8_2026-10-08.py` is reversed (grade table and register -050/-152)
and the KVM4 builder is written back to 7 ± 0.7, only at the Head of QC's word.
