# Purely Plant certificate desk — standing rules

## 1. The approved scans are the source, and the index is how you read them

The Head of QC's ruling of 25.09.2026:

> *"the latest and current scans of the certificates of quality … with their correct document codes,
> their correct data issuing, their superseded document codes, and the internal certificates of
> analysis that are referenced inside each of the certificates of quality — so everything you do in
> the future regarding anything else you will build it upon the information and data contained into
> this folder."*

**The folder:** `https://drive.google.com/drive/folders/1vXy-8drEqBJjBpaadW-E8hGnnb7Q4BmU`
— 46 scanned certificates of quality, one per batch, named by lot code.

It is the authority for: the **current** certificate code, its **issue date**, the **superseded**
code it replaces, the **internal certificate cited**, and the **parameters credited** to that
internal certificate. Where the register disagrees with a scan, **the scan wins** and the register
is corrected — not the other way round. Where no scan speaks to a lot, the register may supply the
value, and the run must **name it as register-sourced** rather than pass it off as scanned.

## 2. Never OCR those scans again — read the index

They are **scanned image PDFs**. Reading one costs vision tokens, and reading all 46 costs them 46
times over. They have been read, and the reading is committed:

| file | what it holds |
| --- | --- |
| `deliverables/qc_gap_analysis/tracker/SCAN_INDEX_2026-09-25.tsv` | **the index — read this** |
| `…/tracker/SCAN_INDEX_2026-09-25.xlsx` | the same, as a spreadsheet |
| `…/tracker/DRIVE_SCAN_MANIFEST_2026-09-25.tsv` | each batch → its Drive file id, so a row traces to its scan |
| [the same index as a live Google Sheet](https://docs.google.com/spreadsheets/d/1PqQ_59JGwXqqWDWFrCBGFpyHW-I8uaTa7jui7U60PfM/edit) | in the scan folder itself, readable without the repository |

`tracker/build_scan_index.py` rebuilds the index from the committed sources and `tracker/scan_index_xlsx.py`
renders the spreadsheet. Neither opens a scan.

**The rule:** read the index. Do not open the scans to answer a question the index already answers,
and do not re-derive the index from the scans because it looks stale — check it first.

A scan may be re-read only to settle a **specific, named** disagreement, one document at a time, and
whatever the read establishes is **written back into the index in the same change**, so the next
session inherits it. Never a sweep of all 46.

If a field is genuinely absent from the index, add it by listing the batches that need it and reading
only those.

## 3. The certificate package in Drive

`https://drive.google.com/drive/folders/1Ju37BR51Q0XTbYOfOZyGB4aE8YoF1LRu`

| | |
| --- | --- |
| `iCOA_FIN/` | the current internal certificates — `iCOA_T1`, `iCOA_T2`, `iCOA_T3` |
| `OLD_ICOA/` | the superseded set |
| `_sig/` | the signature assets — take signatures from here, do not rebuild them from certificate files |
| `_generator/`, `index.html` | the generator and its index |

**What can and cannot be written to Drive:** `create_file` uploads binary content as base64, so the
cost is ~1.35 tokens per byte. An index or any small text file is fine. A ~616 KB certificate HTML
(~205k tokens) or a multi-MB merged PDF (~600k+) is not — deliver those through the app instead of
claiming Drive is impossible. `update_file` changes **metadata only**; it can move a file between
folders without re-uploading it, which is how a superseded document goes to `OLD_ICOA`.

## 4. Two rules that hold across both certificate fleets

- **Dating.** One test date in section 01 and that same date on every analysis — *except* on a
  certificate that has loss on drying tested. Loss on drying is a 24-hour run, so its window opens
  the day before and **closes on the issue date the customer's certificate of quality cites**, never
  on the register's examination date.
- **Attribution.** No approved scan credits microbiology, mycotoxins, heavy metals or pesticides to
  an in-house internal certificate. Where a register row claims more than its scan, the scan governs.

## 5. No silent blank on a certificate

**Tranches 1 and 2 are not touched.** Head of QC, 26.09.2026: *"Don't touch T1 and T2 — they are
already issued and sent to the customer."* For every T1 and T2 lot the release testing was **CNP**
(potency) and **IPH** (mycotoxins) and the retest testing **Farmahem**, whether or not the release
certificate is in our files. The 26.09 apply scripts refuse a T1 or T2 record (`A.FROZEN`); 28 older
ones (`apply_icoa_citations.py`, `apply_lab_attribution.py` …) do not, so
`tracker/check_frozen_records.py` holds every T1/T2 record and page against the restored state
(`FROZEN_T1_T2_2026-09-26.json`) and CI fails on any change. The audit runs on Tranche 3. On 26.09
their records were restored to the state of `f161da1` after the desk had changed them twice.

**The latest ruling governs.** Head of QC, 26.09.2026: *"how many rulings can I give you since the
10th of September and you're still invoking some old rule."* Decide a case by the newest ruling that
covers it. Do not reach back to an older one (the 10.09 "first value of a parameter", say) to
override it, and do not extend a ruling to a tranche it was not given for.

**Every lot is issued, for sale or not.** Head of QC, 27.09.2026: a lot absent from the sale list
(`VERSA_UVOZ-IZVOZ_KONOPLJA3.xlsx` on Drive, the list to Versa) *"is not meant for sale. But that does
not mean that you should not issue any certificate or not include it into the issuance list. You
should. And it should be issued chronologically, regardless if it's in a tranche or not."* The
tranche moves are already recorded — `tracker/TRANCHE_ASSIGNMENT_2026-09-18.md`,
`tranche_assignment_2026-09-18.csv` (P060332 moved T1 → T3; CLE072501, OPM092501, SJ092501,
JD042601, FB042601, CC042601 out of the tranches) — read them before asking. Not on the sale list:
BSS1024_01/2 (P050142), CC012601/1 (P060332).

**Tranche 3: where Farmahem is the only testing on record, it is the release testing** (Head of QC,
26.09.2026 — *"I'm not sure about all of the T3 initial release CoQs"*). Applied by
`tracker/apply_first_testing_ruling_2026-09-26.py`, decided per lot by
`audit_empty_results.release_family`:

- **Cannabinoids** (Identification C with them): no CNP result on record and only Farmahem's → *"the
  Farmahem testing is the initial release testing and there will be no reissuance for those CoQ"* —
  the Farmahem values print on the initial. A CNP result on record → Farmahem is the retest, and the
  initial takes the CNP certificate's own value where it reports one.
- **Mycotoxins**: IPH total aflatoxins on record → the Farmahem panel is the retest (initial: IPH
  total, B1/OTA `n/t`). Only the Farmahem panel on record → *"the testing in Farmahem for mycotoxins
  is part of initial release testing"*: all three print on the initial.
- **No reissuance**: the retest drafts of such lots are withdrawn — `-087`, `-138`
  (`withdrawn` in the register; nothing built; numbers left free). `-152` was withdrawn too until
  27.09.2026, when GRC102501/1's release testing of February 2026 was found filed under the parent
  code "GRC102501" (`intake_GRC102501_2026-09-27/`): it is reinstated as the lot's retest. Look for a
  lot's release certificates under its parent code and its sister sub-lot's Drive folder before
  concluding the campaign was its first testing. **The same, outside the tranches** (Head of QC,
  27.09.2026, "same as Tranche 3"): JD042601 (P060492), CC042601 and FB042601 have only Farmahem
  220-30/31/32-К and -М/26 on record, so that is their release testing — initials `-084`, `-166`,
  `-167` print it (dated 18.09.2026) and `-125`, `-171`, `-172` are withdrawn
  (`OUTSIDE_SAME_AS_T3` in the script). **Except** where a parameter was
  tested again well after the first: *"the second certificate for microbiology is going to enter the
  CoQ, and if the initial testing was way before, then it is definitely a retest and the reissuing
  of the CoQ"* — `-160` (P060342: IPH 539/1070/26 of 31.08 after 362/0692/26 of 01.06) is kept, and
  carries the Farmahem release results as carried from `-073`.
- **Dates**: on or after the last result the initial cites (ruling 1 below), at the desk's usual
  seven days (`audit_empty_results.initial_issue`), never after the lot's own retest.

Head of QC, 26.09.2026: *"they're missing values for many of the parameters and there must not be
a case like that."* A result cell printed `[ — ]` for weeks without anyone saying why.

- **Before any certificate build, run `python3 deliverables/qc_gap_analysis/tracker/audit_empty_results.py
  --tranche T3 --strict`**. CI runs it for Tranche 3. It exits 1
  on a **WIRED-MISS** (a same-lot certificate on or before the CoQ reports the parameter, unprinted), a
  **FIRST-TESTING** cell (the lot's first testing sits only on the retest), a **RETEST-ON-INITIAL**
  value, a **BARE** cell (a status the renderer cannot turn into `n/t` or `[pending]` — it must contain
  "not tested" or "awaiting"), or a draft retest whose *supersedes* date its initial no longer carries.
  It reads the CNP release certificates in the RAGflow page-text cache as well as the corpus: on
  26.09 four T3 initials printed a retest CBN while their own CNP certificate reported it (ППК25118,
  ППК25257, ППК25368, ППК26031). The company's in-house records (lab `PURELYPLANT`, no code) are not
  certificates: ruling of 17.09 (R3), `n/t`.
- **The rulings of 26.09.2026**, applied by `tracker/apply_empty_results_ruling_2026-09-26.py` and `tracker/apply_t3_source_rulings_2026-09-26.py`:
  1. **A later result is printed and the certificate re-dated** (Tranche 3) — *only* where that
     later result is the lot's release testing (above); a retest value never goes on an initial. The
     source is the same lot's retest record. A draft retest's *supersedes* line moves with the date.
  2. **Never another lot's certificate — sub-lots included.** *"They are separate lots."* `BSS1024`
     is not `BSS1024_01/2`; `GRC102501/2` is not `GRC102501/1`. A record that holds its P number where
     the cultivation batch belongs takes the cultivation batch from the owner's workbook
     (`batch_dates_2026-09-10.csv`): P060332 is `CC012601/1` (`-068`, `-087`), not `CC012603` (P060372).
  3. **Mycotoxins are the same case in every tranche.** Where IPH tested total aflatoxins at release,
     the **initial** prints the IPH total and B1/OTA `n/t`, and the **retest** prints all three from
     **Farmahem** (`197-М`, `220-М`, `227-М`) — every T1, T2 and T3 retest has the full Farmahem panel.
     In Tranche 3, where only the Farmahem panel is on record, it is the release testing and prints on
     the initial. B1 is never derived from a total.
  4. **What no certificate covers prints `n/t`** and goes on `tracker/LAB_REQUESTS_<tranche>_*.tsv`.
     A bare `[ — ]` on a result is a defect. Release results that disagree print `[pending]` until
     the Head of QC chooses — a later value must never paper over them. A **retest** must not print a value its
     initial holds pending, nor read a full-panel result around a missing page: on 28.09.2026
     `-162`'s pesticides printed "ND — all 26 residues" from IPH `1065/2026` while page 3 (three of the
     residues and the pesticide conformity statement) is missing and its initial `-052` held them
     pending — now `[pending]` on both. And a retest's mycotoxins are the **Farmahem retest panel**,
     not "carried from the initial" (23 rows had the value from Farmahem but a stale carried status).
     `tracker/check_carry_provenance.py` (CI) fails on either.
  5. **Heavy metals come from IPH**, on the initial and the retest CoQ alike (the retest carries the
     initial's). Where IPH has no certificate for the lot, the cell is `n/t` and IPH is asked.
  6. **Identification A, identification B and foreign matter cite the internal certificate**, unless a
     CNP (`ППК`) certificate for the same lot tests them explicitly — then the CNP certificate is the
     source (FB012603 `ППК26112`, FB012603V `ППК26110`, SCR022601 `ППК26116`). `coq_check.js` OI-27
     accepts exactly that case. The CNP certificate texts in the RAGflow cache are read as well as the
     corpus (ППК26116 is only there). **An internal certificate covers exactly what its own CoQ
     credits to it**, as in the approved scans: 1, 2, 7, plus 8 only where loss on drying was done
     in-house (`-026`, like HPA1024/OPM1024); where CNP tested 1, 2, 7 and 8 there is **no** internal
     certificate (`-075`, `-079`, `-080`, like the scans' `-092`, `-123`). Loss on drying in Tranche 3
     is CNP's or Farmahem's (`-ГС`), in-house only for `-026`, and untested for `-021`, `-050`, `-068`,
     `-073`. `T3_CoQ_Latest_*.pdf` is each lot's current certificate: the retest, or the initial where
     there is no reissue. *"Where needed for the parameters that are not covered by other outsource
     laboratory an iCOA will be issued containing those parameters tested"* (Head of QC, 26.09.2026).
     **Identification C is never one of them.** It is discharged by the certificate that tested the
     cannabinoids and cites the same certificate as the Total THC row — the owner's ruling of
     02.09.2026 (`README.md`, "Identification C"), which has not changed; on 26.09 the desk put it on
     `-026`'s iCoA as in-house and was corrected. `-026` (P050202): its release cannabinoids were tested
     by **New Garden Pharma**, an external laboratory — analysis test report `NGP/QCG/SOP-024 F3` of
     28.11.2025 (Total THC 24.89 %, CBD 0.17 %, LoD 8.19 %, read from the page) — so rows 3, 4, 5 cite
     it; NGP is not in-house, whatever older tables call it. Its loss on drying stays on the iCoA, as
     the approved scan of `-107` credits the sister NGP lot's. CNP's `ППК26036/37/57/58` for P050202
     are **stability time points**, never release results. Head of QC, 26.09.2026: New Garden Pharma
     is cited for **nothing else**. The certificates it obtained from external laboratories (IPH
     `1155/2056/25`, `1157/2058/25`, `5661/2025`, Farmahem `276-31-М/25`, State Phytosanitary
     `10802_2845/2`) were obtained in our name and are cited under the laboratory that issued them.
     What NGP tested itself stands only on an **initial** release CoQ; a reissue is always tested by
     an accredited external laboratory.
  7. **Specification, product code and grade** come from the newest potency grades
     (`potency_grades_2026-09-15.csv`, corrected to `Potency_specifications_25.pdf` of 17.09.2026) via
     `apply_potency_grades.py`: the grade is the window the printed Total THC falls in. A result in no
     window is reported for a new grade, never forced into the nearest one. **The latest potency
     builder is deployed on KVM4** — `https://specs.srv1231216.hstgr.cloud` (`potency-spec-service`;
     read `GET /api/specs`, `/api/specs/<ABBR>`); check it, and only it, for a strain's current grades,
     then carry a new one into `potency_grades_2026-09-15.csv`. WED-II (22.00 ± 1.40, 20.60–23.39 %)
     came from there on 26.09.2026 and grades `-046`. GRC-IV (7.00 ± 0.70, 6.30–7.69 %) was set by the
     Head of QC on 27.09.2026 for `-050` (7.05 %), which no grade covered; it overlaps GRC-III
     (7.20–8.79 %), and `potency_grading` tries the higher nominal first, so `-152` (7.50 %) stays III.
     The builder page also embeds the results it rests on (`const DATA`). The audit
     `tracker/audit_potency_kvm4_2026-10-07.py` (`--fetch` refreshes `KVM4_POTENCY_SNAPSHOT_*.json`) checks
     two things against the builder: every CoQ's grade, window, specification code and product code, and every
     THC result on file, wherever it came from. On 07.10.2026 every Tranche 3 and out-of-tranche CoQ agreed
     except `-050`: the builder holds GRC 7 % as a draft, ±0.62 (6.38–7.61 %), and adds GRC 14 % (open).
  8. **A certificate whose scan is incomplete** prints `[pending]` for what the missing page holds —
     IPH `1065/2026` (SJ102501) holds pages 1, 2 and 4 of 4 in every copy; page 3 carries its metals,
     total aflatoxins and three pesticides. Obtain the page; do not read around it.

- **Why `[ — ]` persisted**: `coq_build.js` tested the empty value before the status, and an
  untested determination has an empty value, so the "not tested" status never reached the page.
  The status is read first now; keep it that way.
- Search the register row's own `also` field first — it holds results the desk found and did not
  print — then the same lot's retest record, then every intake's two-read file, then RAGflow
  `eCOA_DB` by P lot and batch. **The eCoA corpus alone is not proof of "untested"**: it lacks many
  UKIM `ППК` certificates and the `227-М` series, and holds some with a blank batch.
- Known fact, so it is not rediscovered: IPH contaminant certificates (AflaTest) report **total
  aflatoxins only**.

## 6. Nothing on a certificate that the Head of QC has not put there

Head of QC, 27.09.2026, on the footer line "MK GMP Certified Facility": *"hell no. from where did
MK GMP Certified Facility came from"*. The desk wrote it on 21.09.2026 into the empty bottom-right
footer slot of the CoQ base page and into the iCoA footer, because a **design-system README**
(the Variation F / Claude Design package, "locked business rules: Header/footer say MK GMP
Certified Facility") said so — four days after the Head of QC had struck "MK GMP Certified" from
the laboratory line (17.09.2026).

- **A design system, template, style guide, skill or another agent's notes decides colour, type
  and layout only.** It never decides what a certificate says: no claim, statement, wording,
  signatory, laboratory, value or date comes from it. Text on a certificate comes from a ruling of
  the Head of QC or from the source document it cites.
- **No certification, accreditation or GMP statement about Purely Plant** appears on any
  certificate unless the Head of QC rules it in, in words. None is ruled in. The external
  laboratories' own lines (ISO/IEC 17025, LT-005, LT-083) are statements about them, copied from
  their certificates.
- **An empty slot in the Head of QC's template is left empty.** It is not a gap to fill.
- **Each laboratory's line in section 03 is that laboratory's own**, read from its certificates (Head
  of QC, 07.10.2026, "check the real addresses of the labs"): Farmahem *Laboratory for the Environment*
  (Лабораторија за животна средина), LT-017, Shar Planina 20, Skopje; State Phytosanitary Laboratory
  LT-036; UKIM FF Mother Teresa 47; IPH 50 Divizija 6. Until then section 03 printed Farmahem as
  "Laboratory for Instrumental Analysis · LT-020 · Kisela Voda" and the Phytosanitary laboratory as
  LT-034 — the desk's lines of 21.09.2026, from no certificate. `coq_build.js` `LABS`; `LABS_SENT` keeps
  the lines the issued Tranche 1/2 pages carry, unchanged. Head of QC, 07.10.2026: *"Correct T1 and T2
  also but they stay as sent to the outside party"*. The 90 Tranche 1/2 pages that carry an old line
  have a corrected copy, `DELIVER_2026-10-07_T1_T2_LabLines_Corrected/`
  (`tracker/build_t1_t2_lab_lines_corrected_2026-10-07.py`), in which only the laboratory lines change.
  The pages as sent, the register and `check_frozen_records.py` are untouched. Whether the customer is
  asked to replace the certificates is his decision.
- Before adopting any rule from a document that is not a ruling, check it against the rulings —
  the newest governs — and ask when they differ.
- `tracker/check_certificate_claims.py` fails the build and CI on such a claim in any page a build
  can still change. Tranches 1 and 2 of the 18.09 grouping are issued and keep the line as sent
  (`design_handoff/toolchain/build_v40.js` `FROZEN_LOT`); every other certificate is built without it —
  including the six lots that left the tranches on 18.09, none of whose certificates was ever issued.

**Lots outside every tranche** are delivered by `tracker/build_nontranche_bundle_2026-09-27.py`
(`DELIVER_2026-09-27_NoTranche/`). Four of them held internal-certificate numbers that sent T1/T2 pages
carry; with the Head of QC's approval (27.09.2026) the 25.09 rule moved them to the first free numbers
(`tracker/apply_nontranche_icoa_moves_2026-09-27.py`): CLE072501 → `iCoA-PP_26-103`, OPM092501 → `-108`,
SJ092501 → `-119`, JD042601 → `-120` (its retest since withdrawn). On 28.09.2026 the same rule, held
against the **approved scans** as well (`tracker/apply_scan_icoa_moves_2026-09-28.py`), moved the unissued
T3 initial `-023` (P050172) from `iCoA-PP_26-023` — which the sent scan of `-107` cites for P050192 — to
`-127`, the last free number. `tracker/check_icoa_references.py` (CI) holds every delivered CoQ's iCoA
citation against the iCoA page: code, issue date, lot, specification, test date, the sections for the rows
credited, date order, and no number a scan gives another lot.

## 7. What the Head of QC has had to say more than once

The full record — 190 corrections, 07.09.2026–07.10.2026, each quoted — is
`deliverables/qc_gap_analysis/tracker/DESK_CORRECTIONS.md`, and the same is in Open Brain
(`open_brain`, `thoughts`, `metadata.source = claude-code-desk`). Where two of these meet, the newer
ruling governs (§5). The most repeated, in order:

1. **It is on file.** Never report a result, certificate or eCoA as missing, not found or "not
   available" before searching the eCoA database folder and its Excel indexes, the latest master
   workbook, every intake's two-read file, the parent code and the sister sub-lot's Drive folder, and
   RAGflow `eCOA_DB` (said 14 times).
2. **Apply the rulings already given.** Read them here first; do not reopen, forget or reach back past
   them (13 times).
3. **Carry every change into every deliverable** and every sheet of the latest master; a version
   number proves nothing, only a check against every ruling does (11 times).
4. **Potency grades come only from the Head of QC** — the KVM4 potency builder (§5 ruling 7), never an
   older table, never "a missing specification" (11 times).
5. **iCoAs.** One per CoQ, and a retest CoQ cites only its own retest iCoA — except where an outside
   laboratory (CNP) tested everything an iCoA would hold: then there is none (`-075`, `-079`, `-080`;
   26.09.2026, §5 ruling 6) (10 times).
6. **Be short and do not waste tokens**: no re-OCR, no page images in Word, no long reports (10 times).
7. **The deliverable asked for comes first** — the merged PDF when a merged PDF is asked for (9 times).
8. **Templates are fixed.** Change only the values: never parameter names, acceptance criteria,
   columns or layout. The design system governs layout only (§6) (8 times).
9. **No missing values on a certificate** (§5) (7 times).
10. **Mycotoxins** (§5 ruling 3) (7 times).

Standing rules the corrections produced (message numbers are in the record):

- **The templates and the fonts** (Head of QC, 27.09.2026: *"The font is all wrong."*). The CoQ page is
  his `FIN_SP-COA-COQ/templates/coq/Certificate_of_Quality_CoQ.html` with the adjustments he asked for on
  16–17.09 (`design_handoff/base/`); the iCoA is his own format of 24.09 (`iCoA-PP_26-050 … Retest_1`,
  and `-110 … LOD` where loss on drying is in-house). Both are set in **Montserrat, Roboto Mono and
  Orbitron**, plus **Roboto Condensed** for the document codes of the CoQ's section 03 (28.09.2026). The CoQ page loads them from Google, which the printer blocks, so every CoQ print inlines
  them first (`print_v40.py`; `house_css` in the bundle scripts). Orbitron has no Cyrillic and no "№",
  so on the iCoA the Macedonian words of its Orbitron labels fell to Liberation Sans until the review of
  27.09.2026; the bundles now put Montserrat behind Orbitron (`house_stack`), as the CoQ sets its
  Macedonian. A letter, digit or "№" in Liberation or DejaVu on **either** certificate is a defect and
  the bundle refuses it (`assert_house_fonts`); only symbols the house faces lack (≤ ☒ ☐ ∑ Δ) fall back.
  Check a printed page's fonts with `pdffonts` before sending it.
- **An iCoA states what its CoQ states.** Same product code, same specification reference — the
  register's, `…_v.01`. Until 27.09.2026 every T3 iCoA printed `…_v.03` (a rewrite copied from the 24.09
  owner-format builder) under a CoQ printing `…_v.01`; `check_pair` in the bundle now refuses that. The
  issued T1/T2 iCoAs of 24.09 print `_v.03` and are not touched.
- **Dates on every certificate not yet issued** come from the owner's workbook
  (`tracker/apply_batch_dates_2026-09-27.py`: exact batch or P lot, recorded star aliases, empty fields
  only; an initial iCoA with no test date takes the packaging date; an empty P lot takes the
  workbook's `p_batch` — 29 T3 and out-of-tranche certificates printed their cultivation batch as the
  production batch until 27.09.2026). A date field the register cannot
  fill prints "—" **and** is listed in `REGISTER_GAPS.tsv` — the CoQ's own header fields (manufacture,
  packaging, product code, specification) as well as the iCoA's.
- **One A4 page.** Nothing crosses the margins or runs into header or footer; look at the rendered page
  after every layout change. Section 03 of the CoQ (Head of QC, 28.09.2026), on every certificate not yet issued
  (`build_v40.js`, `labref-grid`): each laboratory on **two rows, inline** — English name and
  accreditation; Macedonian name, LT code and address; **"UKIM FF"**, not the full name; **fixed column
  widths** (codes 190 px, parameters 84 px), the same on every certificate; laboratories left-aligned,
  document codes **centred** in their column, parameter numbers **right-aligned** on the page margin, and
  three or more consecutive parameter numbers written as a **range** ("2–4", not "2, 3, 4");
  document codes in **Roboto Condensed** (the narrow face he asked for, inlined at print like the house
  faces); document codes and parameter numbers **always on a two-row grid filled column by column** —
  one item in row 1; two, one per row; a third back in row 1, and so on. The bundles refuse a CoQ whose
  laboratory entry runs to a third row or whose page passes 1123 px (`layout_probe`).
- **Numbering.** Simple and chronological, no empty code rows; a code on a sent scan never moves;
  Tranche 3 takes the first free numbers. The order check (`tracker/issuance_order_check.py` →
  `tracker/ISSUANCE_ORDER_CHECK_2026-09-27.tsv`; 167 live numbers, 11 out of date order) is with the
  Head of QC — renumber nothing without him. CI fails when the list no longer matches the register.
- **One source for every code.** The register (`coq_artifact_data.json`), which the 46 approved scans
  confirm, numbers the CoQ and its iCoA. `icoa_register.py` takes its codes from it (`register_codes`)
  since 27.09.2026 — before that it kept the 10.09 issue-order numbering, disagreed with 156 of 167
  live lots, and the master workbook and CI's workbook check, built on it, agreed with each other and
  not with the certificates.
- **The master is v57** (`tracker/sync_master_v57.py`): v56's register sheets rewritten from the
  register as values, in number order, withdrawn numbers marked; References, both Compilations, Result
  Supersession and Potency Grades rebuilt by their own builders. `verify_workbook.py` accepts an
  out-of-order CoQ number only if the order list names it, and no longer holds the iCoA series to date
  order (the 25.09 first-free-number rule and the sent scans make it not chronological). Any change to
  the register is carried into the master by rerunning the sync — the builder `build_tracker_v8.py`
  cannot reproduce v56 (its build command was never recorded).
- **"Superseded" is a newer version of the same thing, never an input a script reads.** The 25.09
  deletion took `CoQ_Analysis_Master_v3.xlsx` (the owner's original tracker, read by
  `tracker_data.load_owner`, which `coq_references.py` needs), `v6` (the master builder's base) and
  `v20_owner` (the workbook the Head of QC sent on 10.09.2026); all three were restored on 27.09.2026.
  Before deleting a file, grep the scripts for its name.
- **Specifications are all v.01**; a strain's grade numerals are sequential by creation and say nothing
  about higher or lower potency.
- **Dates.** Packaging and manufacturing dates come from the master workbook (`batch_dates_2026-09-10.csv`);
  where a batch has several packaging dates, the first. The label is "manufacturing date"; no harvest
  date on an iCoA; a sampling or CNP certificate date is not a packaging date. An initial iCoA is tested
  on the packaging date, a retest iCoA on the retest sampling date, one date on every analysis (§4).
- **Retest CoQ** = the retested parameters plus every other parameter carried from the initial with its
  original citation; no "not tested" on a retest CoQ.
- **The microbiology panel prints as the lot's own certificate reports it** (Head of QC, 07.10.2026):
  *"you must include all parameters tested and present in the eCOA unless explicitly told"*. Where the
  certificate was ordered against the manufacturer's specification it also reports *P. aeruginosa* and
  *S. aureus*; #9.6 and #9.7 then print from it (`tracker/apply_micro_panel_ruling_2026-10-07.py`, 32
  Tranche 3 CoQs). A certificate that does not report them adds no row. *"You will not use analysis
  results from one batch to fill in for another batch and strain"*: `548/1079/26` (OI-37) stays out. The
  two rows fit one A4 page through `build_v40.js` `PANEL_FIT_LAYER`, written only on those pages.
- **Wording.** ND is a *not detected* result; a parameter not tested is `n/t`, never ND. One Macedonian
  "Conforms" (Одговара); Macedonian "метод", not "метода". Phenotype "Hybrid, Indica/Sativa dominant"
  when the split is unknown, "Hybrid, Indica 80, Sativa 20" when known — the same everywhere.
- **Removed, and not to come back:** the processing (machine/hand trimmed) parameter on CoQs; the
  bottom commentary sentence on iCoAs; the bottom-right document code on specifications; "MK GMP
  Certified" anywhere (§6).
- **In-house laboratory citation:** "Purely Plant QC Department · In-house | Пјурли Плант — Сектор за
  КК · In-house · Kojlija 1043, Petrovec-Skopje, MK".
- **Supersedes line** directly beneath the current CoQ code and issue date, very small and greyed.
- **Look.** No grey; zebra rows kept; heading bars run edge to edge; table rows fade to white by the
  page margins, with no hard lines in a gradient; graphics flattened for print. **Widen the fades**
  (Head of QC, 28.09.2026): every coloured band and rule is solid only across the centre and eases
  to absolute white well before the left/right margins — a centre plateau ramping to white at each
  margin, not solid across the width with a short edge ramp (which read as a hard stop of colour into
  white). `build_v40.js` `WIDE_FADE_LAYER` (CoQ) and the iCoA base templates' `__owner-wide-fade`
  block carry it; the plateau lives in one place so it is tuned once. It governs the reprints only —
  the CoQ layer is gated `!FROZEN_LOT`, so the issued Tranche 1/2 pages `check_frozen_records.py`
  holds are untouched — and the full-bleed heading bars and footer are left edge to edge.
- **Signatures** from `_sig/` only, rotated: Christina Cekic far left, the other two on the right, the
  QC Manager's 15–20 % larger and crossing the line; a signed and an unsigned set.
- **Bundles.** Each page of an attached external certificate carries a ~1.5 cm stamp with the CoQ code
  and date and the Head of QC's signature only, laid over the page without shrinking it, upright.
- **Word** files are exact, editable copies of the page — never page images, never a re-layout.
- **Nothing invented.** No category, statement or reason that no ruling or document supports (there
  is no "12-month reissue"; only a retest reissues a CoQ).
- **Working.** Fix a defect instead of listing it; nothing from memory, check every value; explain a
  proposed correction plainly and briefly; clickable download links, one per package; delete
  superseded versions when told.

**Open with the Head of QC (27.09.2026):** *"I need the -087, -138 and -152. In too."* — `-152` is
reinstated; `-087` and `-138` are still withdrawn under the 26.09 no-reissuance ruling. Ask; do not
decide. From the review of 27.09.2026, also his to decide: the issued Tranche 2 record of `-123` cites
`iCoA-PP_26-123` although its approved scan cites no iCoA (the number is `-109`'s); the issued T1/T2
iCoAs of 24.09 print `…_v.03`; the CoQ footer's "QCSOP 012 v.03" (his template) against our empty slot;
`-021`'s manufacture date (the workbook says "not given"); packaging dates for CC042601, FB042601 and
the three P160 lots; the 11 numbers out of date order. From 07.10.2026: whether the corrected Tranche 1/2
copies replace the certificates the customer holds, and whether that copy also drops the "MK GMP Certified
Facility" footer line the sent pages carry (§6).

## 8. Git

Work on the branch the task names; never push to another without being asked. `git gc` in this
container must be given headroom first — it writes the new pack **before** deleting the loose
objects, and on a full disk it exits 0 having reclaimed nothing and leaves
`.git/objects/pack/tmp_pack_*` behind, which must then be deleted by hand. `git reflog expire
--expire=now --all && git prune --expire=now` frees space without writing a pack, so it goes first.
