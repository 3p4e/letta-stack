# Handover — the eCoA ingestion pipeline

**For:** the agent taking over RAGFlow eCoA ingestion for Purely Plant GmbH.
**Written:** 30.08.2026. **Branch:** `claude/google-drive-links-d932ku` (PR #12, draft, CI green).
**Repository:** `3p4e/letta-stack` — **private**. `raw.githubusercontent.com` links to it
always 404; that host ignores GitHub session cookies. Clone it, or use the API with a token.

Read this before touching anything. It is written so you do not have to reconstruct a
week of verification work, and so you do not repeat the four false starts recorded at the
bottom, each of which cost hours and produced confident wrong answers on the way.

---

## 1. What this pipeline is for, and what went wrong with it

Purely Plant releases cannabis flower batches against Certificates of Analysis from four
external laboratories plus in-house QC. Those certificates are ingested into RAGFlow on
KVM4 (`eCoA_DATABASE`) so agents and people can answer questions about batch quality.
A separate Google Sheets **Batch Release QC register** is the human-facing record.

On 29–30.08.2026 the register was verified against the certificate pages themselves.
The finding:

> **Six mould counts (TYMC) in the register were understated by exactly one power of ten.
> Five of the six therefore read as passing when the certificate shows a failure.**

| Row | Batch | Certificate | Register held | Page shows | vs limit |
|---|---|---|---|---|---|
| 21 | GG1024_01 | 320/0587/25 | 4.2×10³ | **4,2 × 10⁴** | 4.2× over |
| 56 | GP0824_03 | 628/1129/25 | 1.2×10³ | **1,2 × 10⁴** | over |
| 71 | OPM052501 | 904/1589/25 | 3.3×10³ | **3,3 × 10⁴** | 3.3× over |
| 82 | GP052501 | 946/1684/25 | 3.6×10³ | **3,6 × 10⁴** | 3.6× over |
| 100 | CJ062501-2 | 1032/1851/25 | 4.9×10^3 | **4,9 × 10⁴** | 4.9× over, largest found |
| 8 | BG1024 | 163/0271/25 | 1×10³ | **1 × 10⁴** | at limit; disposition unchanged |

**AMENDED 31.08.2026 — the count is five, not ten.** Ten register rows sit at or above the
printed power of ten once corrected. That is not the same as exceeding the criterion.
Ph. Eur. 5.1.4 / 2.6.12 and USP <1111> read an enumeration criterion of `10ⁿ CFU` as a
**maximum acceptable count of 2 × 10ⁿ**, so `≤ 10⁴ CFU/g` conforms up to 20 000. Against
that, five rows are out of specification (21, 71, 82, 87, 100) and four conform (35, 38,
56, 74); row 121 turns on a manufacturer specification rather than on the pharmacopoeia.
Full record in `review/OOS_RECTIFICATION_2026-08-31.md`.

**Every one of those five certificates still concluded ОДГОВАРА** — "complies". That second
fact is a laboratory problem, not a pipeline problem, and no amount of better ingestion
fixes it. What the pipeline must do is stop *hiding* it.

Governing limits are Ph. Eur. 5.1.8 Category C: TAMC ≤ 10⁵, TYMC ≤ 10⁴ CFU/g, read under
the interpretation note above. Some certificates print tighter limits of their own — see
trap 6. And **never compare a count against a limit with the function that parsed the
count**: `magnitude()` answers what number a measurement is, `acceptance_limit()` answers
what the largest conforming result is, and for `10ⁿ CFU/g` those differ by a factor of two.
That confusion is what produced the wrong number above.

---

## 2. The measured diagnosis — do not re-derive this

Seventeen certificates were rendered at 300 DPI and read off the page by eye. Against
that ground truth, RAGFlow's existing parse of the TYMC result was:

| RAGFlow's parse | Count |
|---|---|
| Correct | 6 |
| **Wrong** | **2** |
| **Not extractable at all** — parameter label present, result absent | **9** |

Both errors run the same direction — **10⁴ read as 10³, never the reverse** — on
`320/0587/25` and `1032/1851/25`.

### Four root causes

**1. The exponent is a superscript and no text path survives it.** Google Drive's text
extraction drops it entirely: the same certificate extracts as `… 5,1 х 10 CFU/g 4,2 x 10
CFU/g`, every exponent gone. RAGFlow's vision parse renders exponents but misreads ⁴ as ³.
**Only the rendered page is authoritative.** `pdftotext` and any text layer are excluded
from the numeric path — this is not a preference, it is a measured finding.

**2. Table structure is lost, so values detach from their labels.** This is the cause of
the 9. The chunk contains `Вкупен број габи и мувли-ТYMC` and, somewhere else, a list of
numbers, with nothing binding parameter to result to limit.

> **Critical, and counter-intuitive: this is NOT a vision failure.** `eCoA_DATABASE`
> already runs `layout_recognize: "gpt-4.1@openai-vlm@OpenAI"`. The VLM was never the weak
> link. `chunk_method: "naive"` then flattened its output into 1536-token blobs split on
> newlines. Anyone arriving at this problem proposes "use a vision model" as the fix; it
> is already in place and it is not the fix. The newer `eCOA_DB` dataset already moved to
> `DeepDOC` + `mineru_table_enable: true`.

**3. Cyrillic and Latin homoglyphs are unstable across the corpus.** `ТАМС`/`TAMC`,
`ТУМС`/`ТYMC`/`TUMC` for one parameter; `131112501` parsed for batch `J31112501`;
`197-1-К/26` (Cyrillic К) and `197-1-K-26` (Latin K) for the same document. Exact-match
lookup fails silently on all of these.

**4. Nothing ever compared a result to its own limit.** Every certificate prints the limit
next to the result. One subtraction, at ingest, catches all five — years before a person did.

**5. And a limit is two numbers, not one.** What the certificate prints, and the largest
result that still conforms. For an enumeration criterion of `10ⁿ CFU/g` those differ by a
factor of two (Ph. Eur. 5.1.4 / 2.6.12, USP <1111>). The first version of
`validate_ecoa_limits.py` parsed the criterion with `magnitude()` — the function that parses
the *result* — and reported nine TYMC results out of specification where five are. Use
`acceptance_limit()`, never `magnitude()`, for a limit.

---

## 3. What already exists

All committed and pushed. CI green on all 8 checks at `fda72c8`.

### Built for this problem

| Path | What it is | State |
|---|---|---|
| `ingestion/ragflow/ECOA_RAG_PIPELINE_2026-08-30.md` | The six-step pipeline design and the reasoning. **Read this second, after this handover.** | done |
| `ingestion/ragflow/config/ecoa_dataset_config.json` | PATCH body for the dataset. `naive`→`table`, columns named and typed, `chunk_token_num` 1536→512, `auto_keywords` 4→0. `layout_recognize` deliberately unchanged. | done, **not applied** |
| `ingestion/ragflow/config/ecoa_extraction_schema.json` | JSON Schema for the typed record. Draft 2020-12. `value`/`limit` are **numbers, never strings**. | done, 8/8 tests pass |
| `ingestion/ragflow/config/ecoa_extraction_agent.json` | Model chain, extraction prompt, routing by document class, acceptance tests. | done |
| `ingestion/ragflow/validate_ecoa_limits.py` | R1/R2 rules at ingest. `magnitude()` handles Cyrillic х, superscripts, carets, decimal commas. | done, proven |
| `deliverables/qc_gap_analysis/apply_register_corrections.py` | The six corrections, each cited to a page. Refuses to run if a cell doesn't hold its expected prior value. | done, applied |
| `deliverables/qc_gap_analysis/PP_Batch_Release_QC_Register_CORRECTED_2026-08-30.xlsx` | Corrected workbook. | done, **not yet in Drive** |
| `review/ECOA_REGISTER_VERIFICATION_2026-08-29.md` | Twelve findings with evidence. | done |
| `review/OPEN_DECISIONS_2026-08-29.md` | 24 open items, A1–E6, with owners. | done |

### Reuse these — do not reimplement

| Path | Why |
|---|---|
| `ingestion/common/batch_id.py::batch_key` | **The single** batch-identity definition. `GG1024_01`/`GG1024-01`/`GG1024/01` key alike; `GG1024_01/01` stays distinct from its parent; trailing `V` = verification sample and is part of identity. `policy_check.py` already imports it. Anything re-deriving this rule is a bug. |
| `ingestion/ragflow/doc_identity.py` | Identifies a report by what is printed on it (`Лаб. број`, `Датум на земање`, `Страна N од M`), never by filename. Has `better_of()` for digital-vs-scan duplicates. Verified live: the same report as digital export and as a differently-named image-only scan both resolve to one record. |
| `ingestion/ragflow/replace_reissued.py` | Reissue handling. Completeness gate → page diff → replace → **verify `chunk_count > 0`**. |
| `ingestion/coa_track/letta-imb-coas/letta_host_tools/pp_ocr_scanned_pdf.py` | The proven vision read. Verified against `GG1024.pdf` reproducing all 29 register rows exactly. Its prompt rules are the ones to copy. |
| `ingestion/ragflow/validate_ecoa_limits.py::magnitude` | Number parsing across every notation this corpus uses. Has a prose guard — see trap 5. |
| `ingestion/coa_track/letta-imb-coas/AGENT_MODEL_POLICY.md` | The model chain, and the standing prohibition on classical OCR. |

---

## 4. What is NOT built — your first task

**`ingestion/ragflow/extract_ecoa_records.py`** — the runner. Everything above is
specification and gates; this is the thing that produces records.

Shape:

```
for each certificate PDF:
    classify           -> doc_class A / B / C   (routing in ecoa_extraction_agent.json)
    render             -> pdftoppm -r 300, PNG per page
    read twice         -> vision chain, independent passes
    compare            -> disagreement on value/limit/operator/parameter =>
                          reads_agree=false, value=null, confidence=review, raise the page
    normalise identity -> batch_key(), certificate_key
    validate           -> R1/R2 from validate_ecoa_limits.py
    emit               -> JSONL conforming to ecoa_extraction_schema.json
```

Non-negotiables, each of which exists because of a specific measured failure:

- **Two reads that must agree.** The failure being fixed was a single unchecked read. A
  second read costs far less than a missed out-of-specification batch.
- **Never parse a number from a text layer.** Root cause 1.
- **Capture the limit per result**, from the same page. Never inherit a column header.
- **A record flagged `over_limit` is stored AND surfaced.** Never written silently. This
  is the whole point of the exercise.
- **Classical OCR is forbidden** and `scripts/policy_check.py` rule 1 fails CI on it.
  Macedonian Cyrillic mixed with Latin chemical symbols is the case Tesseract handles worst.

### Acceptance — this is your definition of done

`ecoa_extraction_agent.json` carries an `acceptance_tests` block. These 17 values were read
off rendered pages during the verification and are the regression set:

- **Must reproduce and flag:** `320/0587/25` (42000 vs 10000), `628/1129/25` (12000),
  `904/1589/25` (33000), `946/1684/25` (36000), `1032/1851/25` (49000). Plus
  `163/0271/25` at 10000 — exactly at limit, must **not** flag `over_limit`.
- **Must not flag (11):** `161/0269/25`, `588/1067/25`, `767/1376/25`, `947/1685/25`,
  `1009/1813/25`, `1218/2169/25`, `1226/2192/25`, `1227/2193/25`, `1228/2194/25`,
  `4/0007/26`, `6/0009/26`.
- **Must not be silent:** both NGP documents (`P050202`, `P050192`,
  `NGP-QCG-SOP-024 F3`). They currently parse to nothing numeric. A reviewed record or an
  explicit gap is acceptable; silence is not.

An extractor that cannot reproduce those has not fixed the thing it exists to fix.

---

## 5. Environment and access

```
RAGFLOW_API_SERVER   # base URL, from env
RAGFLOW_API_KEY      # from env — NEVER print, echo, log or paste this
```

**`eCoA_DATABASE` = `f29f8f58a13c11f1858cf58865604f65`** — 291 documents, all status
`DONE`, 1261 chunks summed across documents. The dataset header advertises 1272; see trap 7.

Two routes, and you will need both:

1. **REST API** — reliable. `/api/v1/datasets`, `/datasets/{id}/documents`,
   `/datasets/{id}/documents/{doc}/chunks`, `/retrieval`. This is what worked throughout
   the verification.
2. **RAGFlow MCP server** — `ragflow_list_datasets`, `ragflow_list_chats`,
   `ragflow_retrieval`. Convenient, but **it went down mid-verification**. When it does,
   fall through to the REST API rather than reporting the corpus unreachable.

`Letta_KVM4_MCP` requires an OAuth flow that cannot run in a non-interactive session. If
you need it, the user must authorise it via claude.ai connector settings.

Source documents also live in Google Drive:
`https://drive.google.com/drive/folders/1rwBvSAEoAZWsSKSaAQFUXkQLmZA13mSI`
Read access works. **Write access does not** — `copy_file` and `update_file` require an
approval this session type cannot obtain. Any Drive change is the user's to make.

---

## 6. Hard constraints

**Secrets**
- Never print `RAGFLOW_API_KEY` or any Moonshot/OpenAI key, in chat or in a commit.
- **The RAGFlow API key is still in this repo's git history at commit `83ae904`.** Rotation
  is open item A4 and has not happened. **Do not make this repository public.**

**Never modify**
- `apps/wwf-docengine/**` — out of scope, hands off.
- `server/manifests/2026-08-09/**` — dated manifests are a historical record; never rewrite one.

**CI — `python3 scripts/policy_check.py`, 8 invariants**

| # | Invariant |
|---|---|
| 1 | classical OCR never invoked |
| 2 | no Letta source creation |
| 3 | no committed credentials |
| 4 | all Python parses |
| 5 | gap analysis self-consistent |
| 6 | no all-interfaces published ports |
| 7 | pip installs are pinned |
| 8 | innerHTML interpolations are escaped |

Rules 1 and 2 match on source text, so a file that merely *mentions* the forbidden pattern
trips them. Both carry a `SELF` guard for exactly this reason; follow that precedent rather
than weakening the pattern.

**Commits** — trailer exactly:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
Never put a model identifier in a commit message, PR title/body, code comment, or any
pushed artifact.

---

## 7. Traps — every one of these produced a confident wrong answer first

**1. Homoglyph folding on certificate codes.** A naive matcher reported **219 false
"missing" documents**. Cause: Cyrillic `К` vs Latin `K`, and `/` vs `-`. Fold homoglyphs
and strip separators before comparing anything.

**2. Two different keys for one batch.** **141 false "batch differs"**. Filenames key on
the **P-number** (`P050322`); the register keys on the **strain-batch code** (`GP082501-2`).
Carry both and match on either. With all four normalisations, 236 of 284 register rows
resolve on the first pass.

**3. `ГС` folds to `GS`, not `GC`.** Farmahem's `-LoD-` maps to `ГС`/`GS`. Generic
homoglyph folding gets this wrong — special-case it *before* the general fold.

**4. Filename parsing on underscored batches.** `GRC102501_2` breaks a naive split. Split
on `", "` if present, else on the *first* `_`, anchored on the date regex.

**5. Prose cells parse as numbers.** `"COMPLIES (numeric value not present in captured
source excerpt for report 1625/2026 …)"` parsed to `1625` and was reported as **406× over
an aflatoxin limit of 4**. A false positive like that trains people to ignore the check,
which is worse than no check. `magnitude()` now guards: `letters > 12 and letters >
len(s) * 0.35` → not a measurement. Keep that guard.

**6. Per-certificate limits differ from the column header.** `1220/2171/25` prints
TYMC ≤ 10² where the register column says 10⁴. Its result of 200 **fails on the paper and
passes against the column.** This is why the schema captures `limit` per result.
`validate_ecoa_limits.py` still compares against the column limit and is knowingly
incomplete here — the runner is what fixes it.

**7. Dataset status and counters both lie.** The `eCoA_DATABASE` header advertises 1272
chunks where its documents sum to 1261. Worse precedent: **128 of 389 documents in
`eCOA_INGEST` sat unsearchable with zero chunks, most marked `DONE`.** Never treat
`status: DONE` as proof of ingestion — verify `chunk_count > 0`.

**8. Legend and footer rows contaminate extraction.** Extracting blindly gave 87 result
blocks for 81 batches. Filter to rows where column A is numeric.

**9. Not every exceedance is a failure — check the context before reporting one.**
Two near-misses, both caught only at the last moment:
- Row 96, `ППК26058`, CBN 2.05% — an **accelerated-stability timepoint**, correctly recorded
  on the Stability sheet with the exceedance annotated. The register was right.
- `PM112501`, register 13.33 vs design 10.79 — a **T2 retest** under rule R5. Both correct.

A stability timepoint over limit is data. A release result over limit is a deviation.
Establish which you are looking at *before* writing a finding.

**10. The chunks endpoint caps `page_size` at 100 — and fails silently past it.**
`?page_size=300` returns HTTP 200 with `{"code":100,"data":null}`, not an error status. A
sweep written against it produced **zero** extractions across all 291 documents and looked
like an empty corpus rather than a bug. Always assert `data is not None`, and paginate.

**11. A regex anchored on a parameter label matches the footnote.** Certificates end with
`**** Вкупно Δ9-THC - сума на содржина на Δ9-THC и Δ9-THCA x 0.877 …`. A pattern looking
for the label followed by a number finds that line and returns **9**, from `Δ9`. This
produced 24 fake "disagreements" against the register — fourteen of them at exactly 9.0 —
before it was caught. **Take numbers only from table rows** (pipe-delimited, or
whitespace-aligned with a 2+ space gap); never from a line of prose. Then reject any row
whose label or value carries `мин.` / `макс.` / `≤` / `≥` / an en-dash range, because
`• Вкупно Δ9-THC* мин. 5.00 %` is a specification and an extractor without that guard
reports 5.00 as the batch's THC.

**12. Do not trust the chunk text over the page.** Three worked examples, all from the
same two days, all the same mistake.

*The mould counts.* Three certificates were reported to the owner as false alarms on the
strength of chunk text reading `4,2 х 10³`. The rendered page read `4,2 x 10⁴`. The
cross-check was right and the parse was wrong; the correction had to be issued.

*`ППК25139`.* R4 flagged it, and it was reported as a certificate that "contradicts
itself" — Δ9-THC 0.53, Δ9-THCA 0.52, Total 23.79. The owner challenged it and asked to see
the certificate. The page prints **Δ9-THCA 26.52**, and 0.53 + 26.52 × 0.877 = 23.79
exactly. The certificate was perfect; the corpus had dropped two digits. The same record
also holds `Satre Pie` for Grape Pie and `GF0824_02` for GP0824_02.

*`ППК25117`.* Corpus total 1.58 against 0.46 and 17.01. Page prints **15.38**. Correct
certificate, correct register, corrupt corpus — again.

**The rule.** If chunk text and page disagree, the page wins, every time, without
exception. And a validation flag is a reason to *open the page*, never a laboratory
finding in itself — of the three flags raised this way so far, **zero** turned out to be
the laboratory's fault. Pulling the page costs one Drive read and would have prevented
all three misreports.

---

## 8. Sequencing, and what is owed to whom

**Before you re-ingest anything — open item E1 🔴:** the RAGFlow host has **no swap** and
loses the in-flight document under memory pressure (16 G total, ~6.5 G available). Queue
documents **one at a time**, or add swap first. A bulk re-ingest of 291 documents without
addressing this will lose documents silently.

**Order of operations:**

1. Build the runner. Prove it against the 17-certificate regression set. *No live changes yet.*
2. Clone `eCoA_DATABASE`, PATCH the clone with `ecoa_dataset_config.json` (**strip the
   `_meta` block first — the API rejects unknown fields**), re-parse a handful, and confirm
   the Резултат column survives chunking.
3. Only then touch the live dataset, one document at a time.
4. Run R1/R2 over the re-ingest and clear every finding against a page.
5. Refresh the chunk counter.

**Not yours — the user's, and blocking QC closure:**
- Snapshot the Drive workbook, then replace it with the corrected version.
- **Open ten deviation records** (item B1 🔴). The laboratories concluded ОДГОВАРА over
  their own failing numbers; this needs a QC decision, not a pipeline.
- Rotate the RAGFlow API key (A4 🔴).

**Still unverified, if you want more ground truth:**
- In-house THC on `P050202` — the NGP documents parse to nothing numeric.
- A random-sample error rate across the ~250 non-microbiology register rows. Only
  microbiology has been checked page-by-page; the rest of the register is unmeasured.

**Related open items:** B5–B8 (batch-identity rulings; B5 and B6 are settled as questions
of fact and await only a ruling), C1/C3, D2, D3, E1–E6. All in
`review/OPEN_DECISIONS_2026-08-29.md` with owners and proposed resolutions.

---

## 9. The one idea to keep

**Numbers stop being retrieved from prose.**

Chunk text is for narrative questions — who signed, what method, what the remarks say. Every
value a release decision touches comes from a typed record, extracted once, with its limit
in the same object, checked by subtraction, stored only if it passes. A chunk can be wrong
invisibly. A record with `value` and `limit` as numbers cannot.

That is the entire design, and everything in `config/` is downstream of it.
