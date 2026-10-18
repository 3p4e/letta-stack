# ACME_SOP work in progress: what goes into the DocEngine (18.10.2026)

Source: the ACME_SOP Drive folder (`1MZYJOs9LKplBh_McrPj8YzSLCDP5VJhE`), inventoried 18.10.2026. It holds 599 folders and
3,224 files. The Drive connector's paging is defective, so some folder counts are lower bounds.
Nothing in Drive was changed. `secrets.env` and `cookies.txt` at the root were not opened and must not be ingested.

## The rule used to decide

| bin | what | where it goes |
|---|---|---|
| 1 | a **controlled document** being written (SOP, annex, blank form/logbook template), newest copy only | DocEngine draft under its house code |
| 2 | a **record**: anything carrying a batch, lot, date, result or signature (CoQ, CoA, iCoA, filled forms, label runs, execution sets, issued campaign documents) | not authored; stays where it is |
| 3 | **reference input** (supplier specs and CoAs, equipment manuals, examples, master lists) | a reference dataset, never the approved-SOP dataset |
| 4 | tooling, workspace, build output, copies, secrets | excluded |

## Bin 1: drafts to import, in this order

| # | code | source folder (newest copy) | state | to fix on import |
|---|---|---|---|---|
| 1 | QCSOP011 v03 + A01–A09 | `QC SAM/QCSOP011_Sampling_Package_2026-06-30` | draft; v01 in use | The body still cites the legacy PP-QC-SOP-0xx codes more than 60 times. PP-QC-SOP-012 is **not** QCSOP012. |
| 2 | QCSOP012 v03 + A01, QCT017, QCT018 | `QC_CoX` | QA-reviewed, awaiting signature | QCT018 is also claimed by the QCSOP009 package. |
| 3 | QCSOP018 v02 + A01–A10 | `QCSOP_018_v2.0_Complete_Package` (A01–A09); `PP_SOP_SS` (A10) | draft; v01 in use | There are five parallel copies. Import one; drop the other four. |
| 4 | QCSOP019 + A03, A04; QCT022, QCT023 | `OOS_s` | awaiting signature | — |
| 5 | QCSOP009 v02 + A02–A05; QCT019, QCT020 | `AM_VALALL/00_AM_CURRENT_DOCUMENTS_2026-10-08/02_LATEST_DRAFTS` | v01 signed 04.05.2026 per the index | A revision is v02 under change control. Also settle the 009+013 merge. |
| 6 | QCSOP025 + A01–A03 | `SP_TRAN_OUTS` | draft | PP-QC-SOP-012 and -022 there are its predecessors. Import 025 only. |
| 7 | QCLB021 | `LAB_LIFE` | draft | — |

**Held: needs a code family that QALI 001 does not have.**
- The method validation and verification protocols and reports (PP-QC-AMVP/AMVR/MVP/MVR, a02.1 HMA, a02.2 oven, a04 foreign matter, HPLC 003).
- The 106 raw-material specifications (QCSP-RMI-*, one per material under QCSP002).

**Held: belongs to another department's register, which is not loaded.**
- WH: WHSOP002 + A01–A09, WHT003, WHLB003.
- EQ: EQSOP001 and EQSOP013 with their annexes.
- QA: QASOP031 A05–A10 (labels) and QASOP032 (HLVd).

The HPLC 003 package is marked *ILLUSTRATIVE data*. Only its protocol may be imported, never its numbers.

## Bin 2: records, excluded from authoring

- **Certificates:** CoQ-PP-2025/2026-00xx, iCoA_P01–P12 pages, CoX_DES, ImB_QC_COAs.
- **Specification pages:** the per-strain QCSP001 HTML pages. They belong to the certificate pipeline.
- **Sampling records:** QCT024 filled sets (62 files), PP-QC-SER-001_26 (21 batches), DAY1 packets, EXECUTION_SET_*, QC_SAMP/Tranche 2.
- **Labels:** SS Labels batch folders.
- **Other records:** the QC_OUT RQS requests, the HLVd ISSUE set (95 documents issued 31.07.2026), filled training records, QAT004 change-request forms.

**Finding.** The QCT024 sets, the execution records and the DAY1 packets were made on forms of a **draft** QCSOP011. A record made on an unapproved form is a documentation deviation. EudraLex Vol. 4 Ch. 4 requires documents to be approved, signed and dated by authorised persons (§4.3). Decide whether a deviation is raised or the forms were issued under an approved interim instruction.

## Bin 3: reference inputs

- Supplier specifications (`QC_SPCs/Specifikacii od dobavuvaci`) and nutrient CoAs (`HG_NUTR`).
- Equipment manuals behind `EQ_MAN`.
- `PP_SOP_SS/Examples`, including the legacy "QC_SOP_003 Stability" annexes. QALI 001 gives QCSOP003 to cleaning in QC; that content belongs under QCSOP018.
- The exported QALI 001 PDF, `QMS_TRACKING.md`, `QC_QMS_Document_Code_Registry.md`.

## Bin 4: excluded

- Workspace folders: `.claude`, `.kilo`, `.remember`, `.venv`, `.vscode`, `scripts`, `.git`, `node_modules`.
- Build output: `_build_*`, `_PDF_RENDER`, `_DELIVERY`, `_superseded`, `QC_SPCs/pipe`, `CowoRK/_WORK` and `08_previous_builds`, `hplc-build`.
- Tools and copies: DeepSeek Label app; `DAYLYs/New f` (a GrowFlow onboarding copy of every document); the WEEKLY_WEED_FLOW clone under `MB_MONIT`.
- `secrets.env` and `cookies.txt`: rotate whatever they hold.

## Numbering: fixed in this change

With QALI 001 alone, `GET /register/next` gave **QCSOP025, QCT017 and QCLB021**. Drafts already carry all three numbers.

`register/QC_WIP_RESERVED.yaml` now reserves every QC code the drafts carry, with the drafts' own titles. The next free codes are therefore:

| family | next free |
|---|---|
| SOP | QCSOP026 |
| form/template | QCT025 |
| logbook | QCLB022 |
| QCSOP011 annex | QCSOP011A10 |
| QCSOP018 annex | QCSOP018A11 |

The file lists the open conflicts: QCT018 is claimed twice; QCSOP003 A01–A07; the QCeCoA and QCCoQ families.

## DB3_PP_CURRENT: approved documents only, one entry per code + version

1. Pair the `.docx` and the signed scan by code + version.
2. The `.docx` is the text that is embedded.
3. The scan is the legal record. It is attached as metadata (Drive id, sha256) and is never embedded.
4. OCR the scan's first page only, to confirm code, version, effective date and signatures against the docx and the register. Report every mismatch to the Head of QC.
5. A document that exists only as a scan goes through OCR. Its entry is tagged `source: scan` and its text is checked before use.
6. **No ACME draft goes into DB3.** A draft retrieved as "approved and in use" is the failure this dataset exists to prevent.

Open item: QALI 001 shows QCSOP009 as awaiting signature, while the AM index says v01 was signed on 04.05.2026. Settle it from the signed scan, one document, and correct the register.
