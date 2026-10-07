# Merged sets, PDF and Word (07.10.2026)

Head of QC, 07.10.2026: *"the certificate of quality and internal certificates of analysis merged as one PDF
document without the specifications … the specifications, all of them merged as one PDF document … and three Word
files: all of the certificates of quality into one Word file, all the internal certificates of analysis as one Word
file and all the product specifications in one Word file."*

| file | holds |
| --- | --- |
| `../DELIVER_2026-10-07_T3_Final/T3_CoQ_with_iCoA_2026-10-07.pdf` | the 60 Tranche 3 CoQs, each followed by its iCoA — 117 pages, no specifications |
| `QCSP_001_ImB_all_58_specifications_2026-10-07.pdf` | all 58 specification sheets, strain by strain, a bookmark per strain and grade |
| `T3_CoQ_all_60_2026-10-07.docx` | the 60 Tranche 3 CoQs (initial and retest) in one Word file |
| `T3_iCoA_all_57_2026-10-07.docx` | the 57 Tranche 3 iCoAs in one Word file (`-075`, `-079`, `-080` have none: CNP tested 1, 2, 7) |
| `QCSP_001_ImB_all_58_specifications_2026-10-07.docx` | the 58 specification sheets in one Word file |

The Word files are made from the PDFs beside them (`T3_CoQ_all_2026-10-07.pdf`, `T3_iCoA_all_2026-10-07.pdf` in
`DELIVER_2026-10-07_T3_Final`) by `design_handoff/toolchain/pdf_to_docx_exact.py`, page for page: each page's
graphics behind real, editable text in the house faces, which are embedded. One Word page per PDF page.

    python3 specs/merge_qcsp_by_strain.py            # the all-sheets PDF (and the per-strain and set zips)
    python3 design_handoff/toolchain/pdf_to_docx_exact.py IN.pdf OUT.docx
