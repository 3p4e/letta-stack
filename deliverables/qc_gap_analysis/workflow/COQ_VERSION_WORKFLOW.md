# Compiling a certificate of quality — the workflow for every CoQ from 22.10.2026

Head of QC, 22.10.2026 (#226, #229, #230). Applies to **every future CoQ and every next version of a batch's CoQ**.
Approved certificates are not touched: Tranches 1/2 as sent (`check_frozen_records.py`), the 24 Tranche 3 retest CoQs as
signed on 16.10.2026 (`check_signed_t3.py`). A copy of an approved certificate prints exactly what was approved.

## The rule

1. **The specification sets the parameters.** The batch's intermediate-bulk specification (strain and grade,
   `QCSP_001_<STRAIN>-<grade>_v.01`) lists every parameter a CoQ must cover. One result per parameter, cited from an
   external certificate on file (or the iCoA for what only in-house testing covers).
2. **Version 1** compiles the complete quality-control testing before packaging.
3. **A later result makes a new version.** When an accredited outsourced laboratory tests one or more specification
   parameters at a later date (for a reason that is justified and in line with GMP), the batch gets a **new CoQ** with
   a new code: it cites the new results, carries every other parameter with its original citation, and states that it
   supersedes the previous CoQ (its code and date). Versions 3, 4, … follow the same way — not "initial / retest".
4. **Never into an approved version.** A new result never changes a CoQ that has been approved or sent.

## The pipeline (to build)

| Step | What | File |
|---|---|---|
| Result pool | every external result on file per batch and parameter: laboratory, accreditation, certificate code, test and issue dates, and whether usable (or why not: stability time point, other lot, non-accredited, missing page, OOS under investigation) | from `eCOA_INGEST` and the two-read files |
| Decision file | per batch, version and parameter: the certificate cited, the reason, who decided and when | `COQ_SELECTIONS.tsv` — the only place a choice is made |
| Default pick | the latest usable accredited result dated on or before the version's issue date; where results disagree (out of specification, out of the grade window), `[pending]` until the Head of QC chooses | |
| Review sheet | per batch: parameters × candidate results, the pick highlighted, conflicts listed | sheet in the master |
| Build | register and CoQ generated from pool + decisions only | |
