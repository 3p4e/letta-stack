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

Corpus-derived entries: **37 certificates**, tiered T2 (passed the R4
arithmetic) or T3 (no independent check — pre-fill only, promote through
the remediation desk after opening the scan).

## Farmahem register vs page cross-check

All register values for the 63 Farmahem receipts agree with the
page reads — the CBD/CBN defects the campaign found (rows 9, 276,
286) are corrected in the FHM2 register.
