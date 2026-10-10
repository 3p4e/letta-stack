# eCoA receipt rectification — 31.08.2026

## The root cause of “not read” everywhere

The receipt register's page-verified bit matched certificate codes with
`nk()`, which deletes every non-ASCII character: the Cyrillic К and М that
distinguish a Farmahem cannabinoid certificate from its mycotoxin sibling
vanished, ГС never folded to LOD, and a trailing bracketed note defeated the
match. **59 of the 74 “not read” receipts were false negatives** (56 Farmahem
+ 3 IPH). Re-keyed on `verification_coverage.fold()`: **232 of 247 receipts
are page-verified**; the 15 that remain are all Purely Plant in-house rows.
Independently corroborated by `verification_coverage.py`: 1,033 of 1,073
populated result cells (96.3%) sit on a page-verified certificate.

## Corpus tier for the remainder

The live RAGflow server answers, but the session credential is a different
tenant (`code 102` inside HTTP 200 — trap 10 in a new costume), so the
corpus is read from its local materialisations: the structured extraction
(`deliverables/qc_register/extracted_params.json`) and the vendored chunk
cache (`ingestion/ragflow/cache/all_cert_texts_2026-08-30.json`).

Corpus-derived entries: **37 certificates**, 321 values, every one tier T3
— present in the corpus with no independent check available, so they are
pre-fill only and are promoted through the remediation desk after the scan
is opened. **No value reached T2**: the R4 arithmetic gate needs a document
carrying Δ9-THC, Δ9-THCA and the total together, and no entry in this set
does. A corpus value is never rendered beside a page value for the same
analyte — where the two disagree the page wins and the corpus value is
recorded as a corruption instead.

## Farmahem register vs page cross-check

All register values for the 63 Farmahem receipts agree with the
page reads. The CBD/CBN defects the campaign found (rows 9, 276,
286) are corrected in the canonical register — row 276 by chain
step 17, after chain step 16 had reinstated the transposition on
the authority of an older derived export.
