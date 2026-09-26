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
certificate is in our files. No apply script writes a T1 or T2 record (they refuse, `A.FROZEN`), and
the audit runs on Tranche 3. On 26.09 their records were restored to the state of `f161da1` after
the desk had changed them twice.

**The latest ruling governs.** Head of QC, 26.09.2026: *"how many rulings can I give you since the
10th of September and you're still invoking some old rule."* Decide a case by the newest ruling that
covers it. Do not reach back to an older one (the 10.09 "first value of a parameter", say) to
override it, and do not extend a ruling to a tranche it was not given for.

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
- **No reissuance**: the retest drafts of such lots are withdrawn — `-087`, `-138`, `-152`
  (`withdrawn` in the register; nothing built; numbers left free).
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
     is not `BSS1024_01/2`; `GRC102501/2` is not `GRC102501/1`.
  3. **Mycotoxins are the same case in every tranche.** Where IPH tested total aflatoxins at release,
     the **initial** prints the IPH total and B1/OTA `n/t`, and the **retest** prints all three from
     **Farmahem** (`197-М`, `220-М`, `227-М`) — every T1, T2 and T3 retest has the full Farmahem panel.
     In Tranche 3, where only the Farmahem panel is on record, it is the release testing and prints on
     the initial. B1 is never derived from a total.
  4. **What no certificate covers prints `n/t`** and goes on `tracker/LAB_REQUESTS_<tranche>_*.tsv`.
     A bare `[ — ]` on a result is a defect. Release results that disagree print `[pending]` until
     the Head of QC chooses — a later value must never paper over them.
  5. **Heavy metals come from IPH**, on the initial and the retest CoQ alike (the retest carries the
     initial's). Where IPH has no certificate for the lot, the cell is `n/t` and IPH is asked.
  6. **Identification A, identification B and foreign matter cite the internal certificate**, unless a
     CNP (`ППК`) certificate for the same lot tests them explicitly — then the CNP certificate is the
     source (FB012603 `ППК26112`, FB012603V `ППК26110`). `coq_check.js` OI-27 accepts exactly that case.
  7. **Specification, product code and grade** come from the newest potency grades
     (`potency_grades_2026-09-15.csv`, corrected to `Potency_specifications_25.pdf` of 17.09.2026) via
     `apply_potency_grades.py`: the grade is the window the printed Total THC falls in. A result in no
     window is reported for a new grade, never forced into the nearest one.
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

## 6. Git

Work on the branch the task names; never push to another without being asked. `git gc` in this
container must be given headroom first — it writes the new pack **before** deleting the loose
objects, and on a full disk it exits 0 having reclaimed nothing and leaves
`.git/objects/pack/tmp_pack_*` behind, which must then be deleted by hand. `git reflog expire
--expire=now --all && git prune --expire=now` frees space without writing a pack, so it goes first.
