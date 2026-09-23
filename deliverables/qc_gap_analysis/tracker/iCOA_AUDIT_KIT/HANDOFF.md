# HANDOFF — the iCoA results against the master workbook

Written 23.09.2026. Assumes no knowledge of the conversation it came from.

## 1 · What was asked

1. **First, the fullness of the master workbook** — is every analysis result there, and is there
   enough in it to compile both the **CoQ** (certificate of quality) and the **iCoA** (internal
   certificate of analysis)?
2. **Then the new folder structure** — a folder per batch number holding the iCoA documents, some
   data filled in. Check the **Result column** of each against the workbook. Every result must
   carry the **correct institution**, the external laboratory's **certificate code**, its **date
   of issue**, and the **correct analysis reference** (method).
3. **The rule** — *one iCoA for every certificate of quality*: the initial testing for batch
   release, and **every retest** certificate of quality.

Step 1 is done and its output is in this folder. Steps 2–3 need the folder.

## 2 · Step 1 — done, 27 findings

`verify_fullness.py` against `CoQ_Analysis_Master_v56.xlsx`, output in
`FULLNESS_2026-09-23.md`. What it establishes:

**The workbook is complete as a grid.** 3,956 rows = **172 certificates × 23 determinations**,
with **no blank result cell** and no short panel. 3,175 results stated; 781 absences, all three
in the controlled vocabulary (`not tested` 350 · `upon request — not required for release` 344 ·
`carried from the initial testing — not tested` 87).

**The one-iCoA-per-CoQ rule holds: 172 ↔ 172, matched one to one** — 89 initial and 83 retests
(R 48 · R2 32 · R4 1 · R5 2), joined on the literal `Key` column of both registers.

**Provenance is all but complete.** Method and acceptance criterion on **3,175 of 3,175**;
laboratory, document and date of issue on **3,164 of 3,175**.

The 27 findings, by kind:

| n | finding |
| --- | --- |
| 11 | `#3 Identification C · HPLC/HPTLC` states a result with **no laboratory, no document and no date** — status *to be performed — see route* — on CoQ-PP_26-021, 050, 069, 070, 071, 072, 073, 074, 084, 166, 167 |
| 3 | **a laboratory under two names**: `IJZ` on 22 rows vs `IPH — Institute of Public Health` on 1,559 · `CNP` on 52 vs `UKIM Faculty of Pharmacy — Center for Natural Products` on 365 · `FHM` on 11 vs `Farmahem` on 642. Against a requirement that says *the correct institution*, 85 rows name it in the short form |
| 1 | the DAB-2018 method string reads *"(CNP, before its Ph. Eur. 3028 accreditation)"*, but **41 rows of the same laboratories carry the Ph. Eur. method with an issue date earlier than the last DAB row** (11.05.2026). The split is consistent per document, so the wording claims a date boundary the dates do not have |
| 3 | an external laboratory with **no sample-receipt date on any result** — `IJZ` 22 · `FHM` 11 · `State Phytosanitary Laboratory` 2 |
| 4 | an iCoA with **no basis date** — iCoA-PP_26-078, 079, 134, 135 |
| 4 | an iCoA whose **scope is wider than the other 168** — iCoA-PP_26-005 and 006 carry 16 determinations, iCoA-PP_26-023 and 024 carry 6. **This matters for step 2: the documents are not all three-determination certificates** |
| 1 | three lots carry a retest round with **no lower round on file** — P050022 I/R5 · P050072 I/R4 · P050202 I/R5. If the round is a campaign label this is expected; if it counts a lot's retests, earlier ones are missing |

## 3 · Step 2 — what to do when the folder arrives

`verify_icoa_folder.py <folder>` walks it and holds every document against the workbook. It
checks, per document, and reports every disagreement with both sides quoted:

* the **document ID** against `iCoA Register` for that lot and round — *not* against the filename
* the **strain**, **cultivation batch**, **P lot**, **series** and **issue date**
* the **scope** — which determinations the document is allowed to carry
* the **three in-house verdicts** against `#1 Ident. A`, `#2 Ident. B`, `#7 Foreign matter`
* every row of the results table — **result · method · acceptance criterion** — against
  `CoQ Compilation (long)` for the matching CoQ code and determination
* any **external certificate** the document cites — institution, code, date of issue
* across the folder, **one iCoA per CoQ**, initial and every retest

### Read the design before trusting any of it

**Verify the document ID against the register, never the filename or the header.** This is not
hypothetical. The iCoA design copy on Drive,
`iCoA-PP_26-036_P060012_WC_Wedding_Crasher_Initial.html`, prints `iCoA-PP_26-036` for lot
`P060012`. The register says `P060012|I` is **`iCoA-PP_26-035`**, strain **`Wedding Crusher`**,
and `iCoA-PP_26-036` belongs to **`P060022` / Cap Junky**. The repository's own issued fleet
agrees with the register. So that design copy carries **a wrong document ID and a wrong strain
spelling**, and anything built from it inherits both.

If the new design's Result column carries more than the three in-house determinations, take the
design as the truth and widen the check — but four of the 172 already have a wider scope in the
register, so widening is expected for those four and must not be silently applied to the rest.

## 4 · Rules that must not be broken

* **Never move an `Issuable` state** (allocated → issued). That is the owner's GMP authorisation.
* **Workbook v49 must not be used.** `CoQ_Analysis_Master_v44.xlsx` and the three 17.09 lists in
  `CoXTemp` are pre-renumbering and must not be distributed.
* **`specs/QCSP_001_v04/` is superseded** — not to be issued or cited. Current sheets are **v.03**.
* The **packaging-date question was resolved on 20.09.2026** and must not be reopened.
* **Vendor independence**: a release-critical number and the document carrying it come from the
  laboratory's own certificate, never inferred from elsewhere.
* Nothing is uploaded to the owner's Drive uninvited; `eCoA_DB` is not deleted without an explicit
  confirmation given at the time.

## 5 · Where the originals live

Repository `3p4e/letta-stack`, branch `claude/google-drive-links-d932ku`, working directory
`deliverables/qc_gap_analysis`. The workbook is `tracker/CoQ_Analysis_Master_v56.xlsx`; the issued
iCoA fleet is `SIGNED_2026-09-21/iCoA/{Initial,Retest}/HTML`; the sheet contract in prose is
`tracker/README.md` (*"The sheets are formula-driven"*). Richer machinery exists in the tree and a
checker that lives there should use it — `tracker/reference_sections.py` (`latest_master`,
`sheet_or_section`), `tracker/verify_workbook.py` (`load_values`, `table`),
`ingestion/common/batch_id.py` (`batch_key`), `tracker/tracker_data.py` (`nkey`, `as_date`),
`icoa_register.py`. The two scripts here are deliberately standalone so they can travel.

## 6 · Out of scope

Task #48 (`#9.6`/`#9.7` from the 31 expanded-panel documents); Task #51 (the letter to the
Institute about 434/0848/26 and the 02.02.2025 receipt line); the `text-shadow` source fix and the
reconversion of the 344 certificates and 57 specification sheets; the Word bulk-download archives;
the v.03 / 17.09.2026 version collision on the specification sheets.
