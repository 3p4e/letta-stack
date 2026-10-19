# Word copies — one CoQ, one iCoA, one specification (07.10.2026)

Head of QC, 07.10.2026: *"create one document that is [a] … editable … Word document … that will be 100% visual copy
and equivalent to the PDFs"* — for one specification, one internal certificate of analysis and one certificate of
quality, after the day's changes.

| file | made from |
| --- | --- |
| `CoQ-PP_26-008_P050012_GG_Gorilla_Glue_Grade_II.docx` | `DELIVER_2026-09-26_T3/CoQ/Initial/PDF/` — the delivered page |
| `iCoA-PP_26-008_P050012_Gorilla_Glue.docx` | `DELIVER_2026-09-26_T3/iCoA/Initial/PDF/` — the iCoA that CoQ cites |
| `QCSP_001_GG-II_v.01_Gorilla_Glue_Grade_II.docx` | `specs/QCSP_001_ImB/PDF/` — the specification both cite |

**How.** `design_handoff/toolchain/pdf_to_docx_exact.py`: the page's own graphics (bars, bands, pills, rules, logo)
are the Word page's background, and every line of text is a real, editable Word run placed at the coordinates the PDF
gives it, in the house faces (Montserrat, Orbitron, Roboto Mono, Roboto Condensed), which are embedded in the file.
Nothing is re-flowed, so the page in Word is the PDF's page. A handful of symbols the house faces lack
(☒ ☐ ≤ ∑ Δ ⁹) stay in the background picture.

**Checked.** Each file was rendered back to PDF (LibreOffice) and every text run measured against the delivered PDF:
every run starts within 0.03 pt of its place and ends within 0.8 pt; one page each.

**Editing.** Click any text and type. Each line is its own frame, so a longer value does not push the page; widen the
frame if a line grows. In Word: *File → Options → Save → Embed fonts* keeps the faces when the file is passed on.
