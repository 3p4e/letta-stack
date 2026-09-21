# The signed certificates, one file per document — 21.09.2026

Every certificate on its own, nothing merged. 172 certificates of quality and 172
internal certificates of analysis, initial and retest, each as a separate file.

    CoQ/Initial/   89 documents     iCoA/Initial/   89 documents
    CoQ/Retest/    83 documents     iCoA/Retest/    83 documents

and under each, the same document in three formats:

| folder | what it is |
| --- | --- |
| `PDF/` | the controlled record — one A4 page, vector, fonts embedded, signatures on the page |
| `HTML/` | the editable source, self-contained, opens in any browser |
| `DOCX/` | the Word document, **made from the PDF beside it** |

**Signed.** The deposited signatures of the QA Manager and the Head of QC are on every
page; the Analyst box keeps its rule and is signed by hand. The unsigned set of the same
documents is the one committed under `design_handoff/out/` (HTML) and
`design_handoff/pdf/` (PDF) — one switch, `PP_SIGNATURES=1`, builds the difference and
nothing else changes between them.

**Filled.** No result cell is empty on any of the 172 — 4,674 of 4,674 carry a figure or
one of the design system's eight tokens. The one expected block of `n/t` is aflatoxin B₁
and ochratoxin A on the *initial* certificates, 176 cells, which the re-analysis campaign
carries on the retests.

**The Word files are the PDF, not a second drawing of it.** They were re-made on
21.09.2026 from the printed page rather than from the HTML source, after the owner ruled
that an HTML export — *"a totally different file, different design, different structure,
different everything"* — will not do in a GMP environment. Each one carries the PDF's own
graphics as the page and every line of text as a real, editable Word run pinned to the
coordinates the certificate gives it, with the house faces embedded. Measured against the
approved page, a run starts within 0.03 pt of where it belongs and ends within 0.72 pt at
worst. The method and the measurements are in `tracker/PDF_TO_WORD_2026-09-21.md`.

The product specification is the fifty-seven per-grade sheets under
`specs/QCSP_001_ImB/`, built on the owner's approved template. The earlier
`specs/QCSP_001_v04/` set is superseded and must not be issued from.

What each token on a result cell asserts, and which determinations still print `[ — ]` and
why, is set out in `tracker/SWEEP_AND_SIGNED_PRINT_2026-09-21.md`.
