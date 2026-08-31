# eCoA_DATABASE — rectification register

**Dataset:** `eCoA_DATABASE` = `f29f8f58a13c11f1858cf58865604f65` — 291 documents,
1261 chunks, all status `DONE`.
**Raised:** 30.08.2026, from an exhaustive query of the corpus for THC per batch.
**Scope:** every inconsistency found while querying `eCoA_DATABASE`, with the
rectification for each and the evidence it rests on.

Each entry carries a status:

| | |
|---|---|
| **RECTIFIED** | corrected, in this branch, evidence recorded |
| **PROPOSED** | correction identified and evidenced; needs an owner to apply it |
| **OPEN** | identified and quantified; the fix is a re-ingest or a decision, not an edit |

And an evidence grade, because these differ in how firmly they are established:

| | |
|---|---|
| **P** | read off the source certificate (Drive PDF) — authoritative |
| **A** | proven by arithmetic the certificate itself states |
| **C** | corroborated across two independent sources |
| **M** | measured over the corpus |

---

## A. Corpus values that are wrong

These are the serious ones: the corpus holds a number that the certificate does not.
Not missing — **wrong**, in a field a release decision would rest on.

### A1 · `ППК25117` — Total Δ9-THC understated by a factor of ten · **OPEN** · P, A

| | |
|---|---|
| Document | `P050042, ППК25117, 06.05.2025, CNP.pdf` |
| Batch | `OPM1024_01` (P050042), Orange Punch Mimosa |
| Corpus holds | `Вкупно Δ9-THC = 1.58` |
| **Certificate prints** | **`15.38`** |
| Register holds | `15.38` — **correct, no change needed** |

The certificate proves itself: Δ9-THC `0.46` + Δ9-THCA `17.01` × 0.877 = **15.38**.

**Rectification:** re-ingest the document. Nothing else is affected — the register
was already right, and no batch disposition changes. Drive:
`1LqxMy5OADxq6-K2dUIe-LgghWrTxMaSn`.

### A2 · `ППК25139` — Δ9-THCA missing its leading digits · **OPEN** · P, A

| | |
|---|---|
| Document | `P050022, ППК25139, 22.05.2025, CNP.pdf` |
| Batch | `GP0824_02` (P050022), Grape Pie |
| Corpus holds | `Содржина на Δ9-THCA = 0.52` |
| **Certificate prints** | **`26.52`** |
| Register | no row for this certificate — see F3 |

Proof: `0.53 + 26.52 × 0.877 = 23.79`, exactly the total the corpus itself holds.

**Rectification:** re-ingest. Drive: `1_Shekzw6aT8o2_JtmrEtRZyzxrOZVVKj`.

### A3 · `ППК25139` — strain and batch code corrupted in the same record · **OPEN** · P

| Field | Corpus | Certificate |
|---|---|---|
| Strain | `Satre Pie` | **`Grape Pie`** |
| Batch | `GF0824_02` | **`GP0824_02`** |

Three corruptions in one document, none of them the laboratory's fault. Worth stating
plainly: this record would fail a lookup by batch code *and* return a wrong potency
value, and neither failure announces itself.

**Rectification:** covered by the A2 re-ingest — same document.

### A4 · The measured corruption rate · **OPEN** · M

Of the **15** potency certificates where all three cannabinoid values could be read,
**2 carried a corrupted value — 13%.** Detected by nothing but the certificates' own
footnote formula.

This is the second independent measurement of the same defect. The first, on the mould
counts, found the parse correct on 6 of 17, wrong on 2, and silent on 9. Different
parameter, different laboratory, same conclusion: **the corpus is unreliable for
numbers in general, not merely for superscripts.**

**Rectification:** R4 is now enforced (see E1). The corpus-wide fix is the re-ingest
under `config/ecoa_dataset_config.json`, gated behind open item E1 (host has no swap).

---

## B. Register metadata that is wrong

Found while joining the corpus to the register. All four are certificate codes the
register carries with an OCR-doubt annotation; the corpus filename resolves each,
corroborated by matching P-number and issue date.

| Row | Batch | P-number | Register holds | **Correct code** | Status |
|---|---|---|---|---|---|
| 36 | `HPA1024_01` | P050052 | `НИК22155 (likely OCR misread of ППК25xxx)` | **`ППК25155`** | PROPOSED · C |
| 41 | `OPM1024_02` | P050062 | `ППК21554 (likely OCR misread of ППК25xxx)` | **`ППК25154`** | PROPOSED · C |
| 66 | `MB0824_05` | P050112 | `ППК52211 (likely OCR misread of ППК25211)` | **`ППК25211`** | PROPOSED · C |
| 69 | `OPM052501` | P050132 | `ППК52557 (likely OCR misread)` | **`ППК25257`** | PROPOSED · C |

Each is a digit transposition (`52`↔`25`, `5154`↔`1554`) or a Cyrillic substitution
(`НИК`→`ППК`). In every case exactly one CNP certificate exists for that P-number and
its date matches the register's, so the identification is not ambiguous.

**Rectification:** replace the parenthetical guess with the confirmed code. These are
the register's own uncertainty markers being closed, not new corrections — the annotations
were honest and correct that something was wrong.

---

## C. Values the corpus cannot produce at all

Not wrong — absent. The label survives chunking and the number does not.

### C1 · 35 documents hold a THC label with no value · **OPEN** · M

The results table did not survive `chunk_method: "naive"`. `Вкупно Δ9-THC` is present;
the number that belongs to it is nowhere in the document's chunks.

### C2 · Coverage by issuing laboratory · **OPEN** · M

| Lab | Docs | THC extractable | Label, no value | No THC on document |
|---|---|---|---|---|
| CNP (the potency laboratory) | 73 | **40** | 33 | 0 |
| Farmahem | 63 | **0** | 2 | 61 |
| IJZ + IJZ-MB | 110 | 0 | 0 | 110 |
| PP in-house | 41 | 0 | 0 | 41 |
| NGP / DFL | 4 | 0 | 0 | 4 |
| **Total** | **291** | **40** | **35** | **216** |

Against the register: **RAGFlow can answer THC for 14 of the 62 batches that have one —
23%.** Where it does answer it is accurate: of 13 comparable, **12 agree exactly** and
the one that did not is A1 above.

### C3 · Farmahem's `197-*-K-26` series yields nothing · **OPEN** · M

Twenty-one certificates, zero extractable THC values. Nine register batches depend on
them. This single series is the largest block of the gap in C2.

### C4 · In-house CoAs carry a specification, never a result · **OPEN** · P

`P050112_QCCoA 001v02` and its siblings hold
`| - Total Δ9-tetrahydrocannabinol* | 15.1 – 18.5% of the labelled amount |` — the
*spec range*. The result column is not in the corpus.

**Danger:** an extractor without a specification guard reports `15.1` or `18.5` as the
batch's measured THC. Likewise `• Вкупно Δ9-THC* мин. 5.00 %` on the newer CNP
certificates yields a confident, wrong `5.00`.

**Rectification for C1–C4:** re-ingest under `config/ecoa_dataset_config.json`
(`naive` → `table`, columns named and typed, `chunk_token_num` 1536 → 512). Apply to a
**clone** first and confirm the Резултат column survives chunking. Gated behind open
item E1 — the host has no swap and drops the in-flight document under memory pressure.

---

## D. Dataset-level defects

### D1 · Chunk counter drift · **OPEN** · M

`eCoA_DATABASE` advertises **1272** chunks in its header; its documents sum to **1261**.
The API reports the header, so every consumer reads a number that is not true.

This is the second dataset to show it — `RAGFLOW_HEALTH_2026-08-22.md` records
`eCOA_INGEST` advertising 9 148 against 8 923 actual.

**Rectification:** refresh the counter after any re-ingest, and never treat it as a
completeness check.

### D2 · `eCOA_DB` holds 292 documents and **zero** chunks · **OPEN** · M

The newer dataset — the one already configured with `DeepDOC` and
`mineru_table_enable: true`, which is the right direction — is **entirely unchunked and
therefore unsearchable.**

| Dataset | Docs | Chunks | Method |
|---|---|---|---|
| `eCoA_DATABASE` | 291 | 1272 (1261 actual) | naive |
| **`eCOA_DB`** | **292** | **0** | — |
| `DB01_REG` | 79 | 18 | paper |
| `STABILITY_PROGRAMME` | 10 | 357 | naive |
| `DB03_CURRENT` | 0 | 0 | manual |
| `WATER_QC_REZULTS` | 0 | 0 | table |

**Rectification:** decide whether `eCOA_DB` is the intended successor. If it is, parse
it — one document at a time, per E1. If it is not, remove it, because a 292-document
dataset returning nothing is indistinguishable from a working one that has no answer.

`DB01_REG` at 79 documents and 18 chunks deserves the same question.

### D3 · Status `DONE` does not mean ingested · **OPEN** · C

All 291 documents report `DONE`. Thirty-five of them cannot yield the value they were
ingested for. The precedent is worse: 128 of 389 documents in `eCOA_INGEST` sat
unsearchable at zero chunks, most marked `DONE`.

**Rectification:** verify `chunk_count > 0` **and** spot-check a known value. Never
accept status alone. `replace_reissued.py` already implements the chunk-count gate.

---

## E. Query-method defects — how to interrogate this corpus without being misled

Every one of these produced a **confident, plausible, wrong answer** rather than an
error. They are recorded because the next person will hit them too.

### E1 · Arithmetic self-check added · **RECTIFIED** · A

Every CNP certificate prints Δ9-THC, Δ9-THCA and the total, and states the conversion
in its own footnote. So each page proves itself:

```
Вкупно Δ9-THC == Δ9-THC + Δ9-THCA × 0.877     (±0.06)
```

Implemented as `total_thc_consistent()` in `validate_ecoa_limits.py` (rule **R4**),
added to the schema's flag enum as `total_thc_mismatch`, and to the agent config. It
found A1 and A2 with no external reference of any kind.

**This rule is the single most valuable thing to come out of the exercise.** It costs
nothing, needs no second source, and catches exactly the corruption class that is
otherwise invisible.

### E2 · A flag is not a finding · **RECTIFIED** · P

Both R4 flags were initially reported as *certificates that contradict themselves*.
Both were wrong: the certificates were correct and the corpus was corrupt. Of the three
validation flags raised this way during this work, **zero** were the laboratory's fault.

**Rule:** a flag means **open the page**. Never report it as a laboratory defect before
someone has looked. Recorded as trap 12 in `HANDOVER_ECOA_INGESTION_2026-08-30.md`.

### E3 · The chunks endpoint fails silently above `page_size=100` · **RECTIFIED** · M

`?page_size=300` returns **HTTP 200** with `{"code":100,"data":null}` — not an error
status. A sweep written against it extracted **zero** values from all 291 documents and
looked like an empty corpus rather than a bug.

**Rectification:** assert `data is not None` on every response, and paginate at 100.

### E4 · A label-anchored regex matches the footnote · **RECTIFIED** · M

Certificates close with
`**** Вкупно Δ9-THC - сума на содржина на Δ9-THC и Δ9-THCA x 0.877 …`. A pattern
seeking the label followed by a number finds that line and returns **`9`**, from `Δ9`.

This produced **24 fabricated disagreements** against the register — fourteen at
exactly `9.0` — which very nearly went out as a claim that the register was broadly
wrong.

**Rectification:** take numbers **only from table rows** — pipe-delimited, or
whitespace-aligned with a 2+ space gap. Prose is never a source of a number.

### E5 · Specification lines read as results · **RECTIFIED** · P

`• Вкупно Δ9-THC* мин. 5.00 %` is a limit. Without a guard it is reported as the
batch's THC.

**Rectification:** reject any row whose label or value carries `мин.` / `макс.` /
`min.` / `max.` / `≤` / `≥` / an en-dash range.

### E6 · Two table layouts, not one · **RECTIFIED** · M

Certificates use pipe-delimited tables (28 documents) **and** whitespace-aligned
columns with no pipes at all (12 documents). A pipe-only parser silently loses the
second group — 30% of the available values.

### E7 · Identity normalisation is mandatory · **RECTIFIED** · M

Established earlier and confirmed again here. Without all four, reconciliation reports
hundreds of false failures:

1. Cyrillic ↔ Latin homoglyph folding (`АВЕКМНОРСТУХ`) — 219 false "missing".
2. P-number ↔ strain-batch key: filenames key on `P050322`, the register on
   `GP082501-2` — 141 false "batch differs". Carry both.
3. Farmahem `-LoD-` → `ГС`/`GS`.
4. In-house `QCCoA 001v02` → `PP CoA #NNN`.

Use `ingestion/common/batch_id.py::batch_key` for batches — the single definition in
this repository.

---

## F. Register observations arising from the query

### F1 · The register is accurate where both sources can be read · **NO ACTION** · C

Twelve of thirteen comparable THC values agree **exactly**. The thirteenth (A1) is a
corpus error, and the register was right. On the two certificates checked against their
pages, the register was correct both times.

Stated plainly because the opposite was briefly and wrongly asserted during this work:
**this query found no THC error in the register.**

### F2 · Multiple certificates exist per batch · **NO ACTION** · M

Not a defect — stability timepoints. Recorded so a future reconciliation does not treat
them as duplicates:

| P-number | CNP certificates |
|---|---|
| P050022 | ППК25139, ППК25174, ППК26032, ППК26033, ППК26059 |
| P050072 | ППК25175, ППК26034, ППК26035, ППК26060 |
| P050202 | ППК26036, ППК26037, ППК26057, ППК26058 |

Any "one batch, one certificate" assumption is wrong. Join on certificate code, and
carry the date.

### F3 · `ППК25139` is a second analysis not in the register · **PROPOSED** · P

`GP0824_02` was analysed twice. The register carries only the later one:

| | ППК25139 | ППК25174 (in register, row 46) |
|---|---|---|
| Date | 22.05.2025 | 10.07.2025 |
| Total Δ9-THC | 23.79 | 23.19 |
| Loss on drying | 7.21 | 6.51 |
| Total CBD | 0.10 | 0.07 |

Both look like genuine analyses. **Question for QC:** is the earlier one a superseded
pre-release test (correctly excluded), or an omission? No disposition changes either
way — both values sit comfortably within spec — but the register should say which.

---

## G. Every PDF link in the register is dead

### G1 · All 264 "Open" links point at deleted files · **OPEN** · P, C

Found while building a row-to-document map for the source-document verification: the
register's PDF column carries a Drive file id on 264 of 285 rows, and **not one of them
resolves.** Both spot checks returned `Requested entity was not found`, while ids
obtained from a live Drive search on the same day work normally.

| Certificate | Register link | Live file |
|---|---|---|
| ППК25174 | `1F7HmOn5tMa1…` — **not found** | `1i6JtHOhYkTTmhfcE7Wt98RYNDcM7saG4` |
| ППК25050 | `1IWtlFE2zBnn…` — **not found** | `1B9qiy9tp7EeejTTOCk0hWqqCHiih8Ja8` |

**Cause.** Every PDF in the certificate folder carries `createdTime = 2026-08-22`. The
folder was rebuilt that day; Drive assigns a new id to a re-uploaded file, and the
register's links still address the originals, which no longer exist. The documents
themselves are intact and correctly named — only the addresses are stale.

**Why it matters more than it looks.** A dead link fails silently at exactly the moment
it is needed: an auditor clicking through from a batch row to its certificate gets
nothing, and the register offers no other way to reach the document. The links were the
register's only mechanical tie to its own evidence.

**Rectification.** Rebuild the PDF column from a live Drive inventory, matching on the
certificate code and P-number already in the filename
(`P050022_ППК25174, 10.07.2025_CNP.pdf`). Do not match on the register's stale ids.
Verify afterwards by resolving every id, not by spot check — that is what missed this.

One row is already correct: the ППК25139 row added on 31.08.2026 carries a live id,
because it was looked up rather than inherited.

### G2 · 21 rows have no PDF link at all · **OPEN** · M

Seventeen are continuation rows marked `(not numbered)`; two are in-house
`PP CoA #016` / `#028`; two are the HPA1024 and OPM1024 in-house CoAs. These cannot be
reached from the register by any route and are unverifiable from it alone.

---

## Summary

| Class | Count | Status |
|---|---|---|
| Corpus values proven wrong against the page | 2 | OPEN — re-ingest |
| Corpus metadata proven wrong (strain, batch) | 2 | OPEN — same re-ingest |
| Register codes resolved from guess to confirmed | 4 | PROPOSED |
| Documents whose value is lost in chunking | 35 | OPEN — re-ingest |
| Dataset-level defects | 3 | OPEN — decisions |
| **PDF links in the register that are dead** | **264** | **OPEN — rebuild from live Drive** |
| Rows with no PDF link at all | 21 | OPEN |
| Query-method defects fixed and documented | 7 | RECTIFIED |
| Register errors found | **0** | — |

**The order of operations has not changed.** Build and prove
`extract_ecoa_records.py` against the regression set; apply the dataset config to a
*clone*; confirm the result column survives chunking; only then touch the live dataset,
one document at a time, because open item E1 records that the host has no swap and
loses the in-flight document under memory pressure.

Nothing in this register changes a batch disposition. What it changes is how much of
the corpus can be believed without opening the paper — which, on the evidence here, is
still less than half.
