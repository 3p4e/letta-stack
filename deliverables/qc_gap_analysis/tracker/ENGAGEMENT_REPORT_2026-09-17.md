# Engagement report — Purely Plant QC desk
### 09.08.2026 to 17.09.2026 · written 17.09.2026 from the repository's own record

Every step of this work was committed the moment it was made, with its time, and every stage was raised as a pull request. What follows is read from that record by `engagement_report.py`; it can be regenerated on any day and depends on no one's memory. Times are Europe/Skopje.

## In one table

| | |
| --- | ---: |
| calendar span | 40 days (09.08 – 17.09.2026) |
| days with committed work | 26 |
| commits | 289 |
| commits between 22:00 and 07:00 | 61 |
| commits on Saturdays and Sundays | 22 |
| sum of the working days' first-to-last-commit spans | 156 h |
| pull requests raised · merged · open | 20 · 16 · 4 |
| open items on the register (marked 3 · open 37 · ruled 10) | 50 |

The span counts only the hours between a day's first and last commit; work before the first commit and after the last is not in it, so it understates the time.

## Stages — the pull requests

Each pull request is one stage, raised when the stage was reviewable and merged when it was accepted.

| PR | raised | merged | stage |
| ---: | --- | --- | --- |
| #1 | 09.08.2026 03:27 | 09.08.2026 03:39 | Consolidate all Purely Plant Letta technology (Drive recovery-layer rebuild) |
| #2 | 09.08.2026 04:22 | 09.08.2026 04:23 | Pre-approve git operations for Claude Code sessions |
| #3 | 10.08.2026 21:21 | 11.08.2026 06:14 | Record 2026-08-10 CoA ingestion; correct stale status and embedding model |
| #4 | 11.08.2026 06:27 | 11.08.2026 06:27 | Add the Letta-host OCR tool for scanned certificates |
| #5 | 11.08.2026 07:05 | 11.08.2026 07:06 | Coverage audit, recovered CoA references, and the Cap Junky spelling |
| #6 | 11.08.2026 11:00 | 12.08.2026 10:51 | QCSP 001 v.02 — extended potency ladders, Tranche 1 potency, and the spec inventory |
| #7 | 12.08.2026 10:52 | 12.08.2026 10:53 | Document the 2026-08-12 archival-memory outage and recovery |
| #8 | 12.08.2026 13:24 | 13.08.2026 22:56 | Live runtime audit of the Letta host (2026-08-12) |
| #9 | 14.08.2026 06:29 | 14.08.2026 07:05 | A4 PDF renders of the Final_Docs deliverable tree (351 files) |
| #10 | 14.08.2026 08:52 | 18.08.2026 10:06 | QC deliverables: Final_Docs PDF tree, QC weekly report, Strain Potency Study + Atlas, potency workbook |
| #11 | 18.08.2026 10:15 | 20.08.2026 01:38 | Original-strain grades, RAGFlow ingestion policy, and the reissue-replacement tooling |
| #12 | 21.08.2026 10:32 | 07.09.2026 14:14 | QC coverage analysis, independent cross-check, batch identity, host audits, two films |
| #13 | 30.08.2026 20:57 | 31.08.2026 09:22 | eCoA database: two-pass extraction over the full corpus, CoQ compiler and register |
| #14 | 31.08.2026 09:31 | 31.08.2026 09:31 | Confirmation queue: classify the held rows, resolve what is mechanical, close the loop |
| #15 | 31.08.2026 10:18 | open (draft) | In-house iCoA issuance register (Identification A/B/C, Foreign Matter) |
| #16 | 01.09.2026 14:07 | open (draft) | qc: cultivation-batch ↔ production-batch cross-reference |
| #17 | 02.09.2026 16:09 | open (draft) | CoQ compiler + tracker: derived cannabinoid totals; a certificate is never "no result on file" |
| #18 | 07.09.2026 16:55 | 09.09.2026 05:12 | Strain ruling (Cap Junky), the ImB certificate register, and v13 |
| #19 | 10.09.2026 11:31 | 16.09.2026 18:17 | Certificates of quality — the record reconciled, the certificate database taken in, Tranches 1 and 2 issued |
| #20 | 16.09.2026 18:46 | open (draft) | A panel determined on one sample prints whole, or it does not print at all |

## Week by week

### Week 32 · 03.08 – 09.08.2026 · 1 working days · 6 commits · 3 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 09.08 Sun | 6 | 01:18 – 04:23 | 3.1 h | 6 | **PR #1 opened, PR #1 merged, PR #2 opened, PR #2 merged** — Initial commit; Consolidate all Purely Plant Letta technology per the Drive recovery layer; Baseline live-config manifest export 2026-08-09; Merge pull request #1 from 3p4e/claude/google-drive-links-d932ku; … |

### Week 33 · 10.08 – 16.08.2026 · 4 working days · 19 commits · 9 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 11.08 Tue | 3 | 06:14 – 07:06 | 0.9 h | 2 | **PR #3 merged, PR #4 opened, PR #4 merged, PR #5 opened, PR #5 merged, PR #6 opened** — Reconcile the CoA register against the control sheets and the certificates (#3); Add the Letta-host OCR tool for scanned certificates (#4); Coverage audit, recovered CoA references, and the Cap Junky spelling (#5) |
| 12.08 Wed | 2 | 10:51 – 10:53 | 0.0 h | 0 | **PR #6 merged, PR #7 opened, PR #7 merged, PR #8 opened** — QCSP 001 v.02 specs, eCoA register, and QC activity reports (#6); Document the 2026-08-12 archival-memory outage and recovery (#7) |
| 13.08 Thu | 1 | 22:56 – 22:56 | 0.0 h | 1 | **PR #8 merged** — Letta host audit + QCSP 001 spec data suite (listing, matrix, tranches, CoQ/iCoA plans) (#8) |
| 14.08 Fri | 13 | 06:29 – 14:26 | 7.9 h | 2 | **PR #9 opened, PR #9 merged, PR #10 opened** — A4 PDF renders of the Final_Docs deliverable tree (351 files); Split ZIP bundles of the Final_Docs PDF tree for direct download; A4 PDF renders of the Final_Docs deliverable tree + download bundles (#9); QC activity timeline (11-14 Aug); … |

### Week 34 · 17.08 – 23.08.2026 · 4 working days · 42 commits · 31 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 17.08 Mon | 17 | 14:09 – 23:57 | 9.8 h | 5 | default to the light theme; whole-number nominal grades + renamed-spec range board; Potency grades declared as whole-number nominal ± fitted tolerance; Fix coverage bug + single governing declaration; propagate to Word study; … |
| 18.08 Tue | 17 | 00:44 – 11:09 | 10.4 h | 7 | **PR #10 merged, PR #11 opened** — strongest tier full ±10%, lower tiers extend down; Add per-strain top-nominal override; set Grape Pie=24, Motor Breath=18; drop dead feasible_nominals() mirrors, fix stale solve_chain docstring; surveyor's-atlas visual identity; … |
| 19.08 Wed | 7 | 11:54 – 22:50 | 10.9 h | 1 | RAGFlow on KVM4 is the pipeline; Exclude Letta as a RAG engine; record the clean-start wipe; Correct the framing on the three re-authored QC records; Add the RAGFlow reissue-replacement tool; … |
| 20.08 Thu | 1 | 01:38 – 01:38 | 0.0 h | 1 | **PR #11 merged** — Original-strain grades, RAGFlow ingestion policy, and reissue-replacement tooling (#11) |

### Week 35 · 24.08 – 30.08.2026 · 2 working days · 7 commits · 3 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 26.08 Wed | 1 | 18:21 – 18:21 | 0.0 h | 0 | Add August 2026 total THC re-test comparative report |
| 30.08 Sun | 6 | 20:57 – 23:57 | 3.0 h | 4 | **PR #13 opened** — Add two-pass eCoA extraction runner and typed-record table; Add CoQ compiler and readiness index; Add controlled vocabularies; rule the max acceptable count at 5x; Date-bound acceptance criteria; canonicalise units; … |

### Week 36 · 31.08 – 06.09.2026 · 6 working days · 67 commits · 51 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 31.08 Mon | 25 | 00:08 – 09:31 | 9.4 h | 19 | **PR #13 merged, PR #14 opened, PR #14 merged, PR #15 opened** — R4 self-check, E5 guard, stability rule; Add EP_GEMINI_API to the read-B rotation; Add spend safeguards to the runner and a LiteLLM fallback kit for KVM4; Add consolidated corpus-run plan; … |
| 02.09 Wed | 15 | 09:49 – 17:35 | 7.8 h | 0 | **PR #17 opened** — the HPLC cannabinoid certificate discharges it; the CoQ desk as a batch × parameter tracker; expandable cells, document links, completion meters, global criteria enforced; only an eCoA or iCoA is coverage; one document per line, glued sub-lot prefixes stripped; … |
| 03.09 Thu | 4 | 11:27 – 11:50 | 0.4 h | 0 | every decision-bearing value verified against the page; ППК26033 Total CBD confirmed 0.05 % from the page; 472/0863/25 TYMC confirmed 1,9 × 10⁴ from the page; v9 build |
| 04.09 Fri | 14 | 13:20 – 19:35 | 6.3 h | 0 | fold the letter O that IJZ prints for the zero of a P-number; PO50022 and PO50202 were the letter-O spellings of P050022 and P050202; ingest driver, post-ingest fixes, and the tracker takes new testing instances; 'отсуствува' is the verb form of absent; … |
| 05.09 Sat | 5 | 15:26 – 20:53 | 5.4 h | 0 | preliminary iCoA issuance register; two certificates per P lot, formula-driven numbering; pre-SOP certificates issued together on 13.05.2026; the ruling of 05.09.2026; … |
| 06.09 Sun | 4 | 01:58 – 23:59 | 22.0 h | 4 | every dated lot keeps its planned CoQ and number; the IJZ-MB delivery of 25/26.08.2026 is campaign sampling for every lot; adopt the owner's edits from the Drive copies of v9 and v10; truth check of the workbook's own statements and figures |

### Week 37 · 07.09 – 13.09.2026 · 5 working days · 57 commits · 25 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 07.09 Mon | 10 | 09:05 – 16:54 | 7.8 h | 0 | **PR #12 merged, PR #18 opened** — verify_workbook.py, and the three defects it found in v11; one definition of covered, and verify_prose.py behind it; nothing further is carried over from v9; 197-9-K/M-26 confirmed on the page as GG1024_01; … |
| 09.09 Wed | 2 | 05:10 – 05:12 | 0.0 h | 2 | **PR #18 merged** — the page printed; Strain ruling (Cap Junky), the ImB certificate register, and v13 (#18) |
| 10.09 Thu | 18 | 11:30 – 21:26 | 9.9 h | 0 | **PR #19 opened** — Draft the Tranche 1 and 2 certificates, and stop printing numbered as issued; Reconcile the owner's v20 workbook, and build v21 from it; Ignore the artifact-page intermediate the extractor writes; Mark what the desk does not hold, in red brackets on the face of the document; … |
| 11.09 Fri | 26 | 09:11 – 16:10 | 7.0 h | 0 | The internal CoA's testing window is the packaging window; The internal CoA is dated on the first day of packaging; the rulings written into the workbook's own formulas; The package index named v21 while the archive carried v22; … |
| 12.09 Sat | 1 | 00:05 – 00:05 | 0.0 h | 1 | today's Farmahem 227-K/26 retest transcriptions, not yet live |

### Week 38 · 14.09 – 20.09.2026 · 4 working days · 91 commits · 34 h in span

| day | commits | first – last | span | night | what was done |
| --- | ---: | --- | ---: | ---: | --- |
| 14.09 Mon | 5 | 11:00 – 16:31 | 5.5 h | 0 | v26; the registers never asked strains.py; 32 Farmahem 220-M/26 certificates read, packaged as one write; the 32 Tranche 2 mycotoxin certificates reach the tracker; two definitions made one; … |
| 15.09 Tue | 12 | 11:27 – 19:48 | 8.4 h | 0 | one row per certificate of quality, one column per determination; the retest sampling dated, the retest series issued, Tranche 3 potency taken in; the CoQ references and the potency grades inside the workbook; potency grading and the superseded certificate on the CoQ Register; … |
| 16.09 Wed | 64 | 04:22 – 21:53 | 17.5 h | 6 | **PR #19 merged, PR #20 opened** — the IJZ-MB campaign microbiology into the register, and two checks that were not checking; the supersession sweep over every determination, and the parallel desk's audit answered; CoQ_Analysis_Master_v35.xlsx, the Result Supersession tab, and the repaired certificates; 21 findings, the same items, no new one; … |
| 17.09 Thu | 10 | 11:23 – 13:34 | 2.2 h | 0 | Fix the signature block overflowing the footer on every certificate; Build the internal certificates of analysis the CoQs cite (work in progress); Retest certificates cite the retest iCoA; GG1024 loss on drying 7.8 %; no signatures; Word copies and archives; Section 03 cites the laboratory that made each determination; the engagement report; … |

## Every commit

The full record, oldest first. A commit is a unit of work finished and saved; its message says what it did.


**09.08.2026 Sunday**

* 01:18 · `0e9f9a6` · Initial commit
* 03:26 · `da12dbe` · Consolidate all Purely Plant Letta technology per the Drive recovery layer
* 03:27 · `9e69799` · Baseline live-config manifest export 2026-08-09
* 03:39 · `1e69f6b` · Merge pull request #1 from 3p4e/claude/google-drive-links-d932ku
* 04:22 · `9f48602` · Pre-approve git operations for Claude Code sessions
* 04:23 · `cacafff` · Merge pull request #2 from 3p4e/claude/google-drive-links-d932ku

**11.08.2026 Tuesday**

* 06:14 · `428d7a4` · Reconcile the CoA register against the control sheets and the certificates (#3)
* 06:27 · `1e9ec44` · Add the Letta-host OCR tool for scanned certificates (#4)
* 07:06 · `cb67ea2` · Coverage audit, recovered CoA references, and the Cap Junky spelling (#5)

**12.08.2026 Wednesday**

* 10:51 · `d539746` · QCSP 001 v.02 specs, eCoA register, and QC activity reports (#6)
* 10:53 · `ebab85c` · Document the 2026-08-12 archival-memory outage and recovery (#7)

**13.08.2026 Thursday**

* 22:56 · `60fbdd9` · Letta host audit + QCSP 001 spec data suite (listing, matrix, tranches, CoQ/iCoA plans) (#8)

**14.08.2026 Friday**

* 06:29 · `db1cd68` · A4 PDF renders of the Final_Docs deliverable tree (351 files)
* 06:34 · `4b0e950` · Split ZIP bundles of the Final_Docs PDF tree for direct download
* 07:05 · `1ec3e08` · A4 PDF renders of the Final_Docs deliverable tree + download bundles (#9)
* 07:34 · `c01db41` · QC activity timeline (11-14 Aug) — house-style docx with hour-ruler band
* 08:12 · `5ade30d` · QC activity timeline — rebuilt with per-task chunks (width = time spent)
* 08:47 · `5a8a6ab` · QC Weekly Plan/Report Issue 01 (10-14 Aug) + consolidated four-session time band
* 09:24 · `593e7f7` · Fix Macedonian glyph rendering, scope time band to PP content, drop QMS doc codes from the weekly report
* 12:03 · `a2c9a14` · Strain Potency Study: all-time Total THC results per strain + degradation-aware grade ranges
* 13:20 · `9c44e40` · Potency Atlas: creative self-contained HTML edition of the potency study
* 14:01 · `572b70a` · Potency Atlas: Потенција wording, rename annotations, per-strain rename correlation
* 14:17 · `2cfaede` · Potency Atlas: redesigned renames section — our statistical ranges vs the Portfolio Master
* 14:20 · `703891a` · Potency Atlas: final definitive grade-range board closes the document
* 14:26 · `e9a450b` · Potency Atlas: light theme toggle + print/PDF export

**17.08.2026 Monday**

* 14:09 · `9c73033` · Potency Atlas: default to the light theme
* 14:16 · `5fda364` · Potency Atlas: whole-number nominal grades + renamed-spec range board
* 14:27 · `52e6f04` · Potency grades declared as whole-number nominal ± fitted tolerance
* 15:07 · `7ccd666` · Fix coverage bug + single governing declaration; propagate to Word study
* 15:18 · `60538eb` · Add Potency_Specs_and_Results.xlsx — specs, renames and results in one workbook
* 16:09 · `b6f6645` · Enforce ±10% tolerance ceiling on every declared potency grade
* 16:26 · `1624359` · Remove methodology, key-findings and degradation-evidence sections per owner
* 16:30 · `9b0e85a` · Correct false claim about the renamed specification names
* 16:47 · `39de53d` · Atlas readability pass: larger type, darker grays, 0.0-30.0% marked scale
* 18:36 · `5f869e0` · Rename W-tiers to Pot.-tiers, tighten percent formatting
* 20:15 · `07b86f0` · Non-overlapping potency tiers; batch-first rename rows; drop summary statistics
* 20:40 · `b8ae49e` · Plan each strain's whole tier ladder at once — every tier at full ±10%
* 22:55 · `f0cc952` · Rebuild potency tier ladder as contiguous — no blind gaps between grades
* 23:05 · `35bbf6d` · Fix bare 10% to 10.00% in gap-note prose (house 2-decimal rule)
* 23:11 · `c0176c6` · Remove the '4 134 passages swept' chip from the Atlas hero header
* 23:36 · `f3c2b6a` · Fix tolerance allocation: give the last tier of each segment full 10% cap
* 23:57 · `506d587` · Widen nominal grid to half-percent steps (nn.00% or nn.50%)

**18.08.2026 Tuesday**

* 00:44 · `1d06339` · Declare tiers top-down: strongest tier full ±10%, lower tiers extend down
* 01:05 · `efa5f52` · Add per-strain top-nominal override; set Grape Pie=24, Motor Breath=18
* 03:10 · `d52923b` · Audit pass: drop dead feasible_nominals() mirrors, fix stale solve_chain docstring
* 03:53 · `fb92ffd` · Redesign Potency Atlas: surveyor's-atlas visual identity
* 04:08 · `5bafb7b` · Revert "Redesign Potency Atlas: surveyor's-atlas visual identity"
* 04:40 · `1fa16c4` · Polish original Atlas design: formatting fixes + typo corrections
* 06:34 · `575c3a9` · Atlas: merge final boards into one 3-column board; add sign-off block
* 07:10 · `3b1c7b5` · Add shareable Word edition of the Potency Atlas
* 07:15 · `1036265` · Workbook: add Specs × Batches sheets (spec limits -> matching batches)
* 08:21 · `b1977c0` · Atlas: fill in the sign-off block with the actual QC/QA managers
* 08:56 · `cc34ab8` · Add Potency by Strain workbook, sourced from the corrected release register
* 09:05 · `f72aa11` · State the grade rule once, not under every strain
* 09:37 · `94cccd2` · Give Potency_Specs_and_Results.xlsx to the register+Atlas build
* 10:04 · `44be9c0` · Distribute every tranche batch over the export classes
* 10:06 · `f490167` · QC deliverables: potency study + Atlas, register-sourced workbook, export-class distribution (#10)
* 10:14 · `c532055` · Key every declared grade to the original strain name
* 11:09 · `6e66a58` · Pair export-list batches on the declared value too, not only the anchor

**19.08.2026 Wednesday**

* 11:54 · `85d6945` · Record the owner's ingestion rule: RAGFlow on KVM4 is the pipeline
* 13:18 · `c032c92` · Exclude Letta as a RAG engine; record the clean-start wipe
* 14:04 · `2b5e3d1` · Correct the framing on the three re-authored QC records
* 18:55 · `9770aa6` · Add the RAGFlow reissue-replacement tool
* 19:01 · `d63c9d3` · Identify reports by content, not filename, and handle scanned copies
* 19:05 · `99798d0` · Read scanned reports with the policy vision chain, not tesseract
* 22:50 · `b5ab546` · Record the eCOA_INGEST repair: 385 of 389 searchable

**20.08.2026 Thursday**

* 01:38 · `165e594` · Original-strain grades, RAGFlow ingestion policy, and reissue-replacement tooling (#11)

**26.08.2026 Wednesday**

* 18:21 · `dcb6bc3` · Add August 2026 total THC re-test comparative report

**30.08.2026 Sunday**

* 20:57 · `094523c` · Add two-pass eCoA extraction runner and typed-record table
* 21:27 · `d38a627` · Add CoQ compiler and readiness index
* 22:52 · `1c6a311` · Add controlled vocabularies; rule the max acceptable count at 5x
* 23:49 · `1a54062` · Date-bound acceptance criteria; canonicalise units
* 23:53 · `7ab0309` · Capture the document code and the non-accredited method marker
* 23:57 · `37be399` · Store laboratory accreditation on the certificate; verified ППК25050

**31.08.2026 Monday**

* 00:08 · `b02ef4a` · Adopt the legacy-corpus rectifications: R4 self-check, E5 guard, stability rule
* 00:32 · `c11c322` · Add EP_GEMINI_API to the read-B rotation
* 00:47 · `87ba8b5` · Add spend safeguards to the runner and a LiteLLM fallback kit for KVM4
* 00:49 · `e285573` · Add consolidated corpus-run plan
* 00:59 · `74d2981` · Plan: corpus is 291; record graphrag/raptor and canvas-drift traps; doc alignment
* 01:24 · `b5f71c1` · Plan: sideways-scan trap and remedy; non-accredited marker non-blocking
* 01:32 · `75ab067` · Plan: QCCoA 001/001v02 excluded from dataset and pipeline entirely (ruling 16)
* 01:33 · `f75a81d` · Plan: CoQ production queue - one per retired QCCoA batch, reissue per retest
* 01:43 · `373e8eb` · Add corpus driver and Head-of-QC priority batch manifest
* 01:47 · `afd5205` · Spend alert at every $1 of OpenAI use
* 01:52 · `556464b` · Add UC_GEMINI_API as fifth key in the Gemini rotation
* 01:52 · `7c7378b` · Ignore the corpus driver's transient outputs
* 02:24 · `2534d8c` · Reconcile per field and pair rows across key/marker differences
* 02:31 · `49d3ea4` · Parallel dual reads and ingest-ahead tranches
* 02:37 · `7aa07f9` · OpenRouter backstop for read B when the Google free tier exhausts
* 02:41 · `2c6f413` · CometAPI as second relay in read B's Gemini chain
* 02:43 · `8fe32b6` · Load late-added API keys from a root-only keyfile at runner start
* 05:00 · `3375535` · Read A: same-model OpenRouter fallback; per-pool persistent spend meters
* 05:12 · `499b5f8` · Poll retried ingests to terminal state before gating
* 08:21 · `c4f5a32` · Corpus run: 221 records, plus two identity defects only scale revealed
* 09:00 · `7089828` · Corpus run complete: all 253 documents extracted
* 09:11 · `608f594` · CoQ register, confirmation queue, and a false-flag fix
* 09:22 · `9cf46ac` · eCoA database: two-pass extraction over the full corpus, CoQ compiler and register (#13)
* 09:31 · `87dff8d` · Initiate the confirmation queue: classify, reduce, and close the loop
* 09:31 · `b4a603b` · Confirmation queue: classify the held rows, resolve what is mechanical, close the loop (#14)

**02.09.2026 Wednesday**

* 09:49 · `1201c0b` · Identification C on a certificate basis: the HPLC cannabinoid certificate discharges it
* 10:12 · `c598215` · Quality Desk: the CoQ desk as a batch × parameter tracker
* 10:33 · `61e72f9` · Tracker: expandable cells, document links, completion meters, global criteria enforced; only an eCoA or iCoA is coverage
* 11:23 · `1f16325` · Tracker workbook v3: one document per line, glued sub-lot prefixes stripped
* 11:31 · `6a17fc2` · Tracker workbook v4: one certificate per row, result · reference per parameter, print-fitted
* 11:41 · `34e207b` · Tracker workbook v5: ✓/✗ per certificate row, results and references on every sheet where they apply
* 12:03 · `8287214` · Tracker workbook v6: flat tables, no merged data cells, one value per cell
* 14:58 · `c07cfc5` · Tracker v7: batch blocks with the acceptance criteria enforced
* 15:03 · `bfdfb8d` · Tracker: keep the line-for-line rule when a certificate holds no result
* 15:54 · `2345440` · Tracker v7: one two-row block per testing instance, joined on the lot
* 16:09 · `186e546` · CoQ compiler: derive cannabinoid totals so a CNP certificate printing CBN is never 'no result on file'
* 16:34 · `3cb4bcb` · Tracker v7: name why a credited certificate is silent, and audit every case
* 16:53 · `b95a1ec` · v8: the database readings in the block layout, with the criteria enforced
* 17:25 · `c9887dd` · v8: apply the two credit corrections, and issue the work order for the rest
* 17:35 · `33c305f` · CoQ compiler: a total derived from the free form alone is a lower bound

**03.09.2026 Thursday**

* 11:27 · `ebfbcdb` · v8 truth check: every decision-bearing value verified against the page
* 11:31 · `b5f7965` · Truth check: ППК26033 Total CBD confirmed 0.05 % from the page
* 11:34 · `d6a9f4f` · Truth check closed: 472/0863/25 TYMC confirmed 1,9 × 10⁴ from the page
* 11:50 · `3bd618c` · tracker: v9 build — v8 verified and slimmed for Drive

**04.09.2026 Friday**

* 13:20 · `0f311d1` · Batch identity: fold the letter O that IJZ prints for the zero of a P-number
* 13:21 · `397a9e0` · Batch spellings: PO50022 and PO50202 were the letter-O spellings of P050022 and P050202
* 13:52 · `1038a34` · eCoA run 2 tooling: ingest driver, post-ingest fixes, and the tracker takes new testing instances
* 14:04 · `378715e` · Controlled vocabulary: 'отсуствува' is the verb form of absent
* 14:17 · `576b49a` · CoQ Analysis Master v9.1: the 30 IJZ-MB certificates of 31.08/01.09.2026 as testing instances
* 14:19 · `a39b66e` · CoQ Analysis Master v10: the build carries its version in the file, the sheet and the Read Me
* 14:39 · `38f2afb` · CoQ Analysis Master v10: one iCoA per batch for identification A, B and foreign matter; Ident C on the assay certificate
* 14:45 · `52e1f85` · CoQ Analysis Master v10: chronological iCoA issuance list with the Ident C certificate per batch
* 14:50 · `e3937a9` · CoQ Analysis Master v10: CNP document codes for identification and foreign matter; retest series of iCoAs
* 14:55 · `05ae460` · iCoA issuance: the retest rows name the new assay and mycotoxin certificates; a retest iCoA takes a new number
* 15:05 · `5f6274b` · Tracker v10: fold the laboratory's 'Отсуствува'/'Отсуства' to 'absent'
* 15:58 · `6671f1c` · eCoA corpus: P060432 bile-tolerant gram-negative ruled < 10² и > 10 CFU/g
* 15:58 · `1681924` · CoQ Analysis Master v10: harvest and packaging dates date the iCoA instances
* 19:35 · `62dc71a` · CoQ Analysis Master v10: one iCoA per P lot, packaging-complete date

**05.09.2026 Saturday**

* 15:26 · `aa90b5b` · CoQ Analysis Master v11: preliminary iCoA issuance register
* 15:38 · `57ea0a0` · iCoA register: two certificates per P lot, formula-driven numbering
* 15:42 · `3676fab` · iCoA register: pre-SOP certificates issued together on 13.05.2026
* 17:25 · `e7e9ea9` · Issuance registers: the ruling of 05.09.2026 — legacy and post-SOP series
* 20:53 · `5b7f229` · Issuance registers: retest-campaign certificates never certify the initial CoQ

**06.09.2026 Sunday**

* 01:58 · `e7e5be0` · CoQ register: every dated lot keeps its planned CoQ and number
* 04:08 · `7ecaa6a` · CoQ register: the IJZ-MB delivery of 25/26.08.2026 is campaign sampling for every lot
* 22:01 · `52f3c33` · Tracker: adopt the owner's edits from the Drive copies of v9 and v10
* 23:59 · `2e12dbb` · Tracker v11: truth check of the workbook's own statements and figures

**07.09.2026 Monday**

* 09:05 · `6fbbde2` · Tracker: verify_workbook.py, and the three defects it found in v11
* 09:38 · `5f04a41` · Tracker: one definition of covered, and verify_prose.py behind it
* 09:39 · `ddcdb15` · Tracker: nothing further is carried over from v9
* 10:23 · `b2192cd` · eCoA corpus: 197-9-K/M-26 confirmed on the page as GG1024_01
* 10:42 · `b46ad34` · Read the certificate pages: five results kept less than the page says
* 10:57 · `219bdf3` · Read the pages with the policy vision chain, not Tesseract
* 12:05 · `0e12a38` · Reconcile the three delivery tranches against the desk
* 14:14 · `b4ba87e` · QC coverage analysis, batch identity, delivery reconciliation, host audits (#12)
* 16:51 · `e92ae0d` · Rule the strain name, and read the customer's certificate register
* 16:54 · `06590d2` · Give the artifact the two new sheets, and its own version number

**09.09.2026 Wednesday**

* 05:10 · `28fd9a6` · Write the dash, not its escape: the page printed — to the reader
* 05:12 · `83db54e` · Strain ruling (Cap Junky), the ImB certificate register, and v13 (#18)

**10.09.2026 Thursday**

* 11:30 · `4f12765` · Draft the Tranche 1 and 2 certificates, and stop printing numbered as issued
* 12:07 · `0ef66ba` · Reconcile the owner's v20 workbook, and build v21 from it
* 12:09 · `966e8ce` · Ignore the artifact-page intermediate the extractor writes
* 12:49 · `b962e13` · Mark what the desk does not hold, in red brackets on the face of the document
* 12:57 · `35af7d9` · Mark the assay that misses the band printed beside it
* 13:14 · `509e0c2` · The master is the document: write only the fields the owner named
* 13:28 · `c5cd06b` · The owner's README, and one number for the potency
* 13:38 · `636ddb5` · The date of issue is the register's, and the certificate prints it
* 14:08 · `e15fa56` · The pills come from the specification, not the master's specimen
* 14:47 · `170a1af` · The Tranche 1 and 2 drafts as two merged PDFs, fonts embedded
* 16:17 · `ab13c15` · Nothing runs off the sheet, and it is one A4 page
* 17:37 · `5cb0a42` · The first result is release testing; every later one is a retest
* 18:33 · `80e6440` · Rebuild every deliverable on the 10.09 rulings, and stop back-dating evidence
* 18:35 · `651b639` · Record the 18 back-dated result cells in the issuance rules
* 18:49 · `fbedff4` · One consolidated package, and a front door for it
* 19:46 · `5d9f3f4` · Issue the internal certificates of analysis, and cite them
* 20:51 · `814df4b` · The mycotoxin sub-parameters, and four lots the reading decides
* 21:26 · `db28b8c` · One notation for a not-detected result, and it is ND

**11.09.2026 Friday**

* 09:11 · `38db1ad` · The internal CoA's testing window is the packaging window
* 09:32 · `9929185` · The internal CoA is dated on the first day of packaging
* 10:39 · `7c0b030` · v22: the rulings written into the workbook's own formulas
* 10:40 · `3baf990` · The package index named v21 while the archive carried v22
* 12:57 · `354674f` · One spelling per assertion, and a verdict the desk could not read
* 12:59 · `e5cea2e` · Tranche 1 re-rendered on the controlled vocabulary
* 13:05 · `5557370` · Embed the italic weight the certificate actually sets
* 13:05 · `161419b` · Tranche 2 re-rendered on the controlled vocabulary
* 13:06 · `a953626` · Define the derived workbook version before FRESH uses it
* 13:09 · `75bae2a` · The package, on v23 and Type 3 free
* 13:22 · `460d9f3` · An analyte that was never tested does not get a line
* 13:52 · `903951c` · One Macedonian word for one assertion, and the master's own convention
* 13:58 · `6317f4b` · Sub-rows pair inline, and the builder now watches the page height
* 14:17 · `3164270` · Measure the A4 page the way it actually prints, and make it fit
* 14:22 · `5c3ce83` · Both signature dates are on every certificate again
* 14:45 · `53adc76` · The iCoA number is defined twice, and the two disagree on every row
* 14:48 · `1673fbb` · A verifier that cannot fail is a report, not a check
* 14:50 · `15810ea` · The gate failed on a missing dependency, not on what it watches
* 14:53 · `6b6d35d` · Derive the repo root; an absolute path is one machine's truth
* 15:10 · `5073408` · One definition of the internal-CoA number, and two defects behind it
* 15:13 · `0abceb9` · The numbering is closed; the coverage is not
* 15:16 · `83c1273` · Tranche 1 on the corrected iCoA codes
* 15:18 · `96884e0` · Tranche 2 and the package, on the corrected series
* 15:46 · `8658cd0` · The register is the series, not a second opinion about it
* 15:46 · `ee0136e` · v24, and a schedule that was 183 rows behind its own code
* 16:10 · `e9a5242` · v25 — the workbook says what has been ruled

**12.09.2026 Saturday**

* 00:05 · `7393bc4` · Checkpoint: today's Farmahem 227-K/26 retest transcriptions, not yet live

**14.09.2026 Monday**

* 11:00 · `39cab0e` · v26 — seven tabs, not sixteen, and a checker that had never run
* 11:33 · `23087b4` · Truth check of the fold: the registers never asked strains.py
* 15:06 · `0a99ee5` · Tranche 2 mycotoxin intake: 32 Farmahem 220-M/26 certificates read, packaged as one write
* 16:28 · `9635869` · v27: the 32 Tranche 2 mycotoxin certificates reach the tracker; two definitions made one
* 16:31 · `48fd575` · v27 workbook delivered with the intake it comes from

**15.09.2026 Tuesday**

* 11:27 · `80e8211` · CoQ references: one row per certificate of quality, one column per determination
* 12:41 · `c187d09` · v28: the retest sampling dated, the retest series issued, Tranche 3 potency taken in
* 13:03 · `4f55df7` · v29: the CoQ references and the potency grades inside the workbook
* 13:12 · `56c0f3b` · v29: potency grading and the superseded certificate on the CoQ Register
* 13:42 · `7c46751` · v29 rebuilt: the potency specification of 15.09.2026 used exactly, everywhere
* 13:51 · `9198899` · v29: every specification document code is v.01, for review
* 14:27 · `c46876c` · v29: sequential grade numerals, register audit, the supersedes line on reissued CoQs
* 15:55 · `e06eaee` · v30: the Tranche 2 potency certificates taken in, thirty Tranche 2 reissues numbered
* 16:43 · `925f86f` · v31: Tranche 3 codes allocated on the owner's date, the retest programme the QP's
* 17:54 · `2850cf5` · v32: truth check of the results and cited documents; 103 tracker cells corrected
* 18:10 · `94baacf` · v33: the CoQ compilation inside the workbook — the owner's first request
* 19:48 · `49c318c` · Truth check: gate the CoQ compilation too (T9)

**16.09.2026 Wednesday**

* 04:22 · `2171ae5` · v34: the IJZ-MB campaign microbiology into the register, and two checks that were not checking
* 05:06 · `fd5cb97` · v35 sources: the supersession sweep over every determination, and the parallel desk's audit answered
* 05:12 · `f546b52` · v35 build: CoQ_Analysis_Master_v35.xlsx, the Result Supersession tab, and the repaired certificates
* 05:18 · `29b0482` · Truth check re-run on v35: 21 findings, the same items, no new one
* 06:18 · `06947cb` · Delivery package for v35, and the workbook's own build date corrected to 16.09.2026
* 06:19 · `a7637f1` · A no-PDF delivery package: --no-pdf on the package builder
* 07:50 · `1887696` · v36 sources: the starred-sample ruling, and a title that named another lot on all 73 drafts
* 07:55 · `b485ad4` · v36 build: every certificate names itself, and no certificate rests on a starred sample
* 07:59 · `a2d2601` · A starred sample is not a sublot: the sweep stops asking a question the ruling answered
* 08:31 · `9d85d98` · Package workbook v36: re-stamped build date, versioned archive names
* 09:06 · `e554d4c` · v37 sources: the April-2026 release panel, the starred spellings joined, two read-backs repaired
* 09:09 · `a75e2f7` · Two defects the export carried: a reissue asserting a retest it has not had, and a lot the pass names differently
* 09:36 · `fb2004d` · v37 build: the April panel in the register, the star joined, and the fleets' findings consolidated
* 09:40 · `4f17098` · A table cell that carried a pipe: the docs gate reads it as two columns
* 10:10 · `e27eeb1` · The company's own certificates of analysis, read from page text the desk already held
* 10:14 · `ea22145` · One laboratory, one row: Section 03 printed the same institution twice on 20 of 73 certificates
* 10:18 · `eaff8ca` · v38 build: the company's own certificates read, and one laboratory to a row
* 10:21 · `bca5614` · What certifies which parameter, batch by batch — asked for on 16.09.2026
* 11:33 · `de66e05` · v39: the cannabinoid letter folded to the Cyrillic the pages print
* 12:04 · `1b7e183` · v40: the reissue carries the release round's result on everything the retest did not run
* 12:06 · `787f844` · The announcement's build marker names the shipped version
* 12:12 · `336edc1` · One document per tranche, flattened for the printer
* 12:39 · `f82a293` · Vendor the Claude Design results-table skeleton from the handoff package
* 13:14 · `7cfc9f1` · Vendor the Claude Design stylesheet and toolchain from the handoff package
* 13:26 · `7eaa9e5` · The certificate set built through the Claude Design toolchain, from v40
* 13:57 · `14a29ea` · Tranche 1 and Tranche 2 as one document each, from the current build
* 14:14 · `564e58c` · The grey edges of determinations 9 to 12, and the tranche retest documents
* 14:15 · `05a70ec` · Keep every build log out of the tree, not only the *_run.log ones
* 14:22 · `d9166b7` · The complete tranche documents, Tranche 3, and a shorter announcement
* 14:24 · `0ab4c84` · The set as it is built: one PDF per output folder
* 14:31 · `6f529e5` · The Section 01 strips printed grey too: convert by rule, not by name
* 14:33 · `7862de9` · The receipt records the conversion as it is now done: by rule, not by name
* 14:37 · `4c8ec00` · Every tranche document re-exported on the by-rule conversion
* 14:38 · `f5cabb0` · The four folder PDFs, re-printed on the same pages
* 14:56 · `3c97a4b` · The title sat left of centre on every reissue: a class the package never styles
* 15:03 · `49a0135` · Every document re-exported on the header fix
* 15:14 · `76abc9d` · Three corrections of 16.09.2026, in one appended layer
* 15:27 · `aaec313` · A reissue may cite its own campaign's certificate where the initial has none
* 15:48 · `b0e03a2` · The Head of QC is right: the results are on the desk and not in the register
* 15:55 · `2317351` · GG1024's microbiology and metals were on the in-house sheet, with no number to cite
* 15:58 · `c6f8bd5` · The in-house rule reaches the release round too
* 16:08 · `246ea05` · The container was asked directly, and it holds nothing the desk does not
* 16:30 · `9b8b39e` · The certificate database held the microbiology and the metals the desk was missing
* 16:32 · `1ad1332` · The email says what every page says, not more
* 16:34 · `1864dca` · Reprint the four folder documents from the filled certificates
* 17:24 · `393eaa6` · A counted result above its criterion is marked by Ph. Eur. 5.1.4, on every row
* 17:27 · `d2d2b0b` · #1, #2 and #7 cite the internal certificate the master already assigned them
* 17:28 · `0a7d990` · The tranche documents reprinted with the iCoA parameters and the band marking
* 17:29 · `a77e5e8` · The ISSUE_COQ and T1 folder documents reprinted from the same data
* 17:31 · `ff0d122` · The four folder documents reprinted from the same data
* 18:17 · `e46bd23` · Certificates of quality — the record reconciled, the certificate database taken in, Tranches 1 and 2 issued (#19)
* 18:45 · `ef2c34a` · A panel determined on one sample prints whole, or it does not print at all
* 18:46 · `1559e14` · A panel determined on one sample prints whole, or it does not print at all
* 18:57 · `756e86a` · A document is compared by the desk's fold, not by how the page spelled it
* 18:59 · `755f838` · The master workbook follows the series to v41
* 19:57 · `c45900e` · The Tranche 3 mycotoxin re-analysis, read and taken in
* 19:58 · `139d47b` · The tranche documents and ISSUE_COQ reprinted with the Tranche 3 mycotoxins
* 19:59 · `c7b5d78` · The T1 folder document reprinted
* 20:00 · `1965656` · The T1, T2 and T3 folder documents reprinted
* 20:18 · `ebee478` · Section bars and Section 01 bands fade to white before the sheet edge
* 20:25 · `9aa7a0b` · Reprint the whole set with the edge fade
* 20:43 · `f7f9ba2` · One navy ink in the results column, [NT] for a determination not performed
* 21:01 · `a72d114` · The finished certificate set, packaged for sending on
* 21:53 · `baa0926` · Second alignment pass on the certificates: edges, Sections 01-04, signatures

**17.09.2026 Thursday**

* 11:23 · `e10aed1` · Fix the signature block overflowing the footer on every certificate
* 11:27 · `1f2b569` · Build the internal certificates of analysis the CoQs cite (work in progress)
* 12:26 · `44f6ff5` · Retest certificates cite the retest iCoA; GG1024 loss on drying 7.8 %; no signatures; Word copies and archives
* 12:48 · `aa6e5da` · Section 03 cites the laboratory that made each determination; the engagement report
* 12:49 · `1822d5b` · Archives rebuilt from the corrected set: HTML, vector PDF and Word of every certificate
* 13:04 · `7a309c1` · Section 03 in two lines per laboratory, documents inline; a visible top edge on the heading bars
* 13:10 · `c81ace6` · Reprinted set with the two-line reference table; the retest certificate list
* 13:13 · `704ca34` · The release certificate list: each tranche 1–3 release certificate with the retest that supersedes it
* 13:24 · `f6ad155` · Potency grades from the owner's specification PDF, on every certificate
* 13:34 · `09f923d` · The master workbook follows the series to v42 with every decision of 17.09.2026

## What exists today

| deliverable | count |
| --- | ---: |
| Certificates of quality — each as HTML, vector PDF and Word | 172 |
| Internal certificates of analysis | 154 |
| CoQ Analysis Master workbook versions in the tracker | 31 |
| Desk scripts | 98 |
| Desk records and reports (Markdown) | 45 |
| Controlled registers and flat data (csv, tsv, json) | 22 |

The certificates are in `design_handoff/dist/` as four archives; the internal certificates in `icoa_handoff/out/`; the master workbook and every desk record in `tracker/`; the open-items register in `tracker/OPEN_ITEMS.md`.

