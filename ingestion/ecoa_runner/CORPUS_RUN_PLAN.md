# eCOA_DB corpus run — consolidated plan (30.08.2026)

Single source of truth for the from-scratch run over the 253 documents in
`eCOA_DB`. Consolidates every Head-of-QC ruling and budget decision to date;
supersedes the plans scattered through the session that produced it.

## Decisions ledger (Head of QC)

| # | Ruling |
|---|---|
| 1 | CoQ per batch, QCSOP 012 v.03 structure; every result cites doc code + institution + credentials |
| 2 | Micro criteria are Ph. Eur. 5.1.8 **category C**; printed limits are evidence, never the criterion |
| 3 | Maximum acceptable count = **5×** the stated criterion (Ph. Eur. 5.1.8; confirmed by five IJZ certificates) |
| 4 | QCCoA 001/001v02 are superseded (tier 3, fallback only, flagged); CoQ supersedes them |
| 5 | Batch codes never Cyrillic; §2.1 grammar (`GG1024_01`); a batch code is never reused |
| 6 | A genuine retest supersedes and triggers CoQ reissue; **stability timepoints never supersede release results** |
| 7 | Section 03 groups by INSTITUTION (IJZ = one row, all cert codes/dates, departments ignored) |
| 8 | Established strain nomenclature governs over certificate text ("Cap Junkie" = Cap Junky) |
| 9 | Either pesticide panel by jurisdiction; panel-wide "≤ LOQ" or per-compound; any find named individually |
| 10 | Loss on drying ≤10% (DAB) was correct historically; Ph. Eur. 2.2.32 now ≤12% — superseded, not defective |
| 11 | Heavy-metal units are mg/kg corpus-wide; `(l)` on IJZ certs is an undefined template artefact, ppm==mg/kg |
| 12 | Results a laboratory marks non-accredited (*) must not be cited under its accreditation |
| 13 | Legacy-corpus rectifications adopted: R4 arithmetic self-check, E5 spec-line guard, F2 stability rule |
| 14 | Old chunks are contaminated: dataset wiped (verified 0 per-doc, 0 retrieval hits); all documents re-ingest from scratch |
| 15 | `desktop.ini` (Drive sync junk) deleted from the dataset |
| 16 | **QCCoA 001/001v02 excluded entirely** (31.08): all 38 deleted from `eCOA_DB`, never ingested, never extracted. The corpus is **253** external/CNP certificates. Consequence: a parameter whose only source was a QCCoA now reports **MISSING** on the CoQ — no tier-3 fallback rows will exist. The tier-3 code path in `build_coq` stays as a dormant guard |

## Budget posture (user, 30.08.2026)

- OpenAI: **use freely**; user tops up before it runs out. Runner keeps the
  metered ceiling (`OPENAI_BUDGET_USD`, default $5.50) as a stop-loss, raised by
  env var after each top-up — protection against surprise, not a spending plan.
- Moonshot: subscription active; balance can be added. The two chat-pasted keys
  are rotated/dead — only RAGFlow's stored credential works.
- Gemini: free tier only, 4 keys rotating; `GEMINI_API_KEY` leaked and dead.
- gemini-2.5-pro considered and declined: no free quota, gpt-5-class paid price,
  and the free flash read is not the weak link.
- ChatGPT Go: no API access; useful as human eyes on the review queue only.

## Model matrix (final)

| Role | Model | Basis |
|---|---|---|
| RAGFlow parser (all formats) | gpt-4.1 @ openai-vlm | proven clean at test; paid, topped up |
| Extractor: questions | gpt-4.1-mini | moonshot returns empty on this prompt; ~$0.001/doc |
| Extractor: keywords | moonshot-v1-128k | works, flat-rate |
| Chat/agent nodes | kimi-k2.6, temp 0 | ruling |
| Embedding | voyage-3-large | working, retrieval verified |
| Runner read A | gpt-5 | zero wrong values recorded |
| Runner read B | gemini-3.6-flash, 4-key rotation | zero cost, proven |
| Arbiter on held rows (planned) | gpt-5, **advisory only** | a third read may inform the reviewer, never auto-confirm — disagreement is still resolved by a human |

## Known traps (all observed live; the run script must respect every one)

1. `POST /api/v1/documents/ingest` needs integer `run: 1` — boolean returns
   "success" and enqueues nothing.
2. `prompts` on extractor nodes silently re-nests to `[{content:[...]}]` and
   kills every ingest with "expected string, got 'list'" — GET and verify shape
   before every tranche.
3. An extractor's annotations survive only if the NEXT node's prompt references
   that extractor's `@chunks` output — referencing the chunker orphans them.
4. `DELETE /chunks` with an empty body reports success and deletes nothing —
   pass `chunk_ids`, verify the count after.
5. `run: DONE` ≠ ingested; the dataset-header chunk counter drifts — verify
   per-document chunk_count and read a chunk back.
6. Re-ingest with `delete: true` destroys existing chunks even when the new
   parse FAILS — quality gate passes before the next tranche starts.
7. Extractor failures can write `**ERROR**...` into indexed keyword fields —
   the gate rejects any chunk containing it.
8. Gemini 3 thinking tokens eat `maxOutputTokens` — stay at 32768.
9. Both models agreeing is not truth (cert_code null on ППК25050): shared blind
   spots are prompt defects, not disagreements.
10. Dataset `parser_config` shipped with `use_graphrag: true` and
    `use_raptor: true` — a large silent token burn had either ever triggered.
    Both now off; the update PUT only accepts a MINIMAL parser_config (sending
    the config back with its internal keys fails with code 101).
11. The canvas held `image/table_context_size: 1` against the engine's 0 — a
    canvas save would have changed chunking behaviour mid-corpus. Aligned.
12. A scan can be SIDEWAYS while its PDF metadata says portrait/rotation-0
    (both NGP worksheets). gpt-4.1 hallucinates on a sideways page; gpt-5 read
    it anyway. Remedy, proven on both: rotate pages upright
    (`page.set_rotation(90)`), replace the document, re-ingest. The quality
    gate is what surfaces these; a length check alone is not enough — one
    hallucinated retry passed 300 chars, so the gate also probes for a
    plausible batch code in the content.

## Alignment with the official pipeline documentation (ragflow.io, read 30.08)

- Component order Parser → Chunker → Transformer → Indexer: ours matches.
- The docs state the exact failure we found live: "The Transformer node does
  not automatically acquire content from its preceding nodes" — upstream
  variables must be referenced explicitly. Our chain (Questions reads the
  chunker, Keywords reads Questions' output) is the documented pattern.
- Indexing pre-generated QUESTIONS yields "significantly higher similarity
  than matching questions with answers" — we index questions + keywords + text.
- The docs' default chunk size is 512; we deliberately run 2048 with 0 overlap
  so one certificate stays one chunk. Retrieval here finds the CERTIFICATE
  (the runner then reads the actual PDF); splitting a 2-page certificate into
  four fragments would only separate the batch code from the results table.
- Cross-dataset retrieval requires the same embedding model on every dataset
  searched together; the legacy dataset does not share `voyage-3-large`, so
  never query it jointly with `eCOA_DB`.

## Order of operations

1. **Regression gate** — re-run the pilot set through the current runner;
   require: all previously confirmed values reproduced and `ППК25050` cert_code
   captured. The IJZ non-accredited markers are reported but non-blocking
   (Head of QC, 31.08: "not that of great importance").
2. **Tranche loop** (~20 docs): ingest (`run:1, delete:true`) → poll to terminal
   → quality gate (chunk>0, no `**ERROR**`, no mojibake per `quality_guard`,
   questions+keywords populated) → two-pass runner → `build_table` rebuild →
   failures re-queued once, then held for review, never силently skipped.
3. **Priority head of the queue**: `P050042/ППК25117`, `P050022/ППК25139`
   (closes legacy A1–A3), then the CANCELLED `SJ112501_051-2-LoD-26`.
4. **After each tranche**: checkup.py green, spend report, review queue size.
5. **After the corpus**: `coq_index` over all batches; report READY /
   BLOCKED / NEEDS-ICOA / REISSUE-DUE; legacy register B-codes confirmed
   against extracted CNP codes for the Head of QC to apply.

## CoQ production queue (Head of QC, 31.08)

Every deleted QCCoA 001/001v02 is replaced by a CoQ compiled from the
originating eCoAs — one per batch below. A batch whose parameters were
retested additionally gets a **new CoQ version** carrying the retested value
together with every non-retested value under its ORIGINAL certificate
reference and date (QCSOP 012 v.03 versioning; retest detection is value-based
via `build_coq` superseded rows, stability timepoints excluded).

QCCoA 001 (16): BG1024, BSS1024, CJ1024, P050012, P050022 (two issues,
10.07 + 17.07.2025 — both retired), P050032, P050042, P050052, P050062,
P050072, P050092, P050102, P050122, P050162, P050182

QCCoA 001v02 (22): P050082, P050112, P050132, P050172, P050192, P050202,
P050212, P050272, P050282, P050292, P050302, P050312, P050322,
P060012, P060022, P060032, P060042, P060052, P060062, P060072, P060082,
P060092

That is ~37 unique batches. `coq_index` decides per batch whether the CoQ can
issue (READY) or what blocks it (MISSING rows now that no tier-3 fallback
exists); the BG1024 retest (THC 21.80 → 26.14) is already the first entry in
the reissue queue.

## Outside this session's reach (needs the user)

- LiteLLM deploy on KVM4 (`ingestion/litellm/README.md`, three commands).
- `docker logs` on the 5 failed executor tasks.
- Register edits: B-row cert codes; F3 (ППК25139 second analysis) decision.
- `SUPERSEDED_CRITERIA['loss_on_drying'].until` changeover date from the
  specification version history.


## Run 2 — 04.09.2026: 30 IJZ-MB certificates (issued 31.08 and 01.09.2026)

Thirty microbiology certificates the Head of QC added to the Drive folder on 04.09.2026
(`_SPLIT_MANIFEST_IJZ-MB_2026-08-31_01.09.2026.csv` names them, page by page, with
sha256). Pulled through the Drive connector, hash-verified, uploaded to `eCOA_DB` and run
through the pipeline agent; all 30 pass the gate. The manifest itself is not ingested.

Two rows the reads disagreed on — bile-tolerant gram-negative bacteria, where the
laboratory prints a range (`< 10³ и > 10²`) and one read saw only the exponent as `ˣ` —
were ruled by the Head of QC from the certificate pages on 04.09.2026 and applied through
`decisions_2026-09-04.tsv` (DECISION B, RULED_BY, BASIS): P060262 `< 10³ и > 10² CFU/g`,
P060432 `< 10² и > 10 CFU/g`. `apply_decisions.py --write` regenerates the worksheet from
the open items (it drops an unapplied decision typed into it): fill the sheet after
`--write`, then apply without it.

### What had changed since run 1, and what was done about it

| Found | Done |
|---|---|
| The parser and the questions extractor pointed at an OpenRouter credential the tenant no longer holds | parser back to `gpt-4.1@openai-vlm@OpenAI` (run 1's id); questions to `gpt-4o-mini@openai-vlm@OpenAI` — `gpt-4.1-mini` cannot be registered on the OpenAI factory (`add_llm` fails its access test) |
| `moonshot-v1-128k` answers "Not found the model / Permission denied" | keywords extractor to `kimi-k2.6@MOONSHOT_API@Moonshot`, the ruling's chat model |
| Both extractor `prompts` fields had re-nested again (trap 2) | flattened before the run, as always |
| The dataset carried `use_graphrag: true` and `use_raptor: true` again (trap 10) | both off, minimal `parser_config` PUT, verified |
| OpenAI credit exhausted at the first parse (429 `credit_balance_exhausted`) | topped up by the Head of QC; the one certificate that failed in the window was re-queued |
| IJZ prints the zero of the P-number as a letter O (`PO60052`) | `pp_batch` and `batch_key` fold it; every new chunk's keywords carry the digit-zero form; both extractor prompts now ask for both spellings |
| Gemini: five keys live, one (`GEMINI_API_KEY`) reported leaked by Google | the runner rotates the five; the dead one is never read |

### Model matrix (run 2)

| Role | Model |
|---|---|
| RAGFlow parser (all formats) | gpt-4.1 @ openai-vlm @ OpenAI |
| Extractor: questions | gpt-4o-mini @ openai-vlm @ OpenAI |
| Extractor: keywords | kimi-k2.6 @ MOONSHOT_API @ Moonshot |
| Embedding | voyage-3-large (unchanged) |
| Runner read A / read B | gpt-5 / gemini-3.6-flash (unchanged) |

### Tooling added

- `ingest_new_documents.py` — `setup` (restore the agent's models, flatten prompts), `upload`, `run NAME…|--all` (ingest with integer `run: 1`, poll to a terminal state, gate), `status`. PDFs come from `ECOA_PDF_DIR`.
- `post_ingest.py` — `keywords` (add the digit-zero P-number to every new chunk, verified by re-read), `prompts` (the P-number rule in both extractor prompts).
- `deliverables/qc_gap_analysis/tracker/new_instances_from_records.py` — records + manifest → testing instances for the tracker builder.

## Identity rulings (Head of QC) — `identity_decisions.tsv`

A ruling on a document's identity — which batch a certificate belongs to — is not a
parameter value, so it does not belong in the value ledger `decisions_*.tsv`. It is recorded
in `identity_decisions.tsv` (date, document, certificate, field, confirmed value, what it
rested on before, who ruled, on what basis), and the record itself is stamped:
`confirmed.batch_canonical` names the person and the date, and the caveat the extraction
left behind ("batch_canonical read by only one model") is cleared.

**07.09.2026 — 197-9-K-26 and 197-9-M-26 belong to GG1024_01.** The Farmahem retest pair of
07 and 10.08.2026 had its batch from one read only; the other read was silent, and the
attribution otherwise rested on the filename (`P050092_…`). The Head of QC read both pages:
**GG1024_01 is printed on each.** The attribution stands, now on a page read rather than a
single model.

Two naming rules confirmed with it, and already in the code: **GG1024_01, GG1024/01 and
GG1024-01 are one batch** (`batch_id.py` folds the separator), and **GG1024 is a different
lot from GG1024_01** — an R&D batch is never folded into its production batch. So the R&D
lot GG1024 has no cannabinoid assay of any kind on file: no CNP certificate, no Farmahem
retest, only the in-house Report of Analysis of 23.04.2025 (13.34 %), which is not an eCoA.
Of the six R&D lots, four were retested (BG1024, BSS1024, HPA1024, OPM1024); GG1024 and
CJ1024 were not.

## Run 3 — 10.10.2026: eCOA_PIPE → eCOA_INGEST (prepared, blocked on vision credit)

### What was found

| Found | Done |
|---|---|
| eCOA_PIPE pointed at `gpt-5.4-mini@OPEN_AI_SERV` (key 401) and `openai-vlm` / `GEMINI_BN` (gone) | parser → `anthropic/claude-sonnet-5.5@OPENROUTER@OpenRouter`; questions + keywords → `deepseek-v4-flash@DEEPSEEK@DeepSeek` |
| eCOA_DB_agent had been edited to `nemotron-4-340b` (NVIDIA 404), `phi-3-vision` and the deleted `OPEN_RAUT` instance | same models as eCOA_PIPE; its 2048-token chunk kept (its 283 documents were built with it) |
| Both extractor `prompts` re-nested again (trap 2) | flattened, verified by GET |
| OpenRouter instance `OPEN_RAUT` no longer existed | new instance `OPENROUTER` from `OPEN_ROUTER_API_KEY`; `model_info` must use `model_name` with `model_type` as a list |
| **DeepDOC reads these certificates as Latin gibberish** ("BkyneH6poj raOu HMyBJIM" for "Вкупен број габи и мувли") and drops the exponent ("4,2x104") — measured on 320/0587/25 | DeepDOC is never the PDF parser for eCoAs; only a vision model |
| A dataset-level `layout_recognize` VLM is silently ignored for these model ids (DeepDOC ran instead) | the VLM belongs in the pipeline Parser |
| **NVIDIA vision models cannot parse in RAGflow v0.26.4** — dataset parser and pipeline Parser both fail with "Cannot mix str and non-str arguments" (Kimi K2.6, Kimi K3, Nemotron Parse 2.0, Llama 3.2 90B Vision). Chat through the same key works. | NVIDIA stays outside RAGflow: the runner's layered reads (`ECOA_LAYERED_OCR_DESIGN_2026-10-10.md`) call it directly |
| OpenAI credit exhausted; OpenRouter $0.38 left of $329 (402 on the first pilot page); Moonshot quota exhausted | run blocked until a vision provider is funded |

Prompts: both extractors now carry "Rules learned from this corpus" — homoglyph/separator spellings
(К/K, ППК/PPK, ГС/GS/LoD, PO→P0), laboratory names in both languages, the closed strain list,
values and per-row limits copied exactly with `x 10^n`, no numbers from footnotes or specification
lines, ND ≠ not tested, stability time points named as such, nothing from an unreadable page.

Corpus source: Drive `eCoA_DATABASE` (`1SmOicCRa8KEqoB-YlCojdap161YMQ-Di`), 480 ACTIVE files per
`_eCoA_DATABASE_INDEX.xlsx` (41 redacted in-house QCCoAs and 1 superseded file excluded, ruling 16).
File ids come from `https://drive.google.com/embeddedfolderview?id=<folder>` (one fetch, all ids);
every download is accepted only if its SHA-256 equals the index's. Ingest one document at a time
(`migrate_to_ecoa_pipe.py run NAME`), never the whole list in one call (no swap on KVM4).
### Run 3, unblocked (10.10.2026): NVIDIA via the OpenAI-API-Compatible provider

All set through the RAGflow API: `PUT /api/v1/providers {"provider_name":"OpenAI-API-Compatible"}`, then
`POST /api/v1/providers/OpenAI-API-Compatible/instances` — instance `NVIDIA_OAI`, base URL
`https://integrate.api.nvidia.com/v1`, the `nvapi-` key. Instance creation verifies one chat model within
`LLM_TIMEOUT_SECONDS` = 10 s: Kimi K3 (reasoning, ~9 s, empty content at low max_tokens) fails it, so the
instance was verified on `nvidia/nemotron-parse-2.0` (0.4 s) and the vision models added afterwards
(`POST …/instances/NVIDIA_OAI/models`, `model_type: image2text`).

Direct bake-off on the pilot pages (NVIDIA account, 10.10.2026):

| model | 320/0587/25 TYMC | 1032/1851/25 | 946/1684/25 | ППК25139 THCA / total |
|---|---|---|---|---|
| **moonshotai/kimi-k3** | 4,2×10⁴ ✓ | 4,9×10⁴ ✓ | 3,6×10⁴ ✓ | 26.52 / 23.79 ✓ |
| nvidia/nemotron-3-nano-omni | ✓ | ✓ | (503) | ✓ but "Д9" for "Δ9" |
| google/gemma-4-31b-it | 4,2×10¹ ✗ | | | |
| meta/llama-3.2-90b-vision | columns shifted ✗ | | | |
| kimi-k2.6, gemma-3-12b, mistral-nemo | not enabled for the account (404) | | | |

Kimi K3 is the parser of eCOA_PIPE and eCOA_DB_agent and the tenant image2text default. Through the
pipeline each certificate is one chunk, ~5 min, Cyrillic intact, each result in its row beside its limit.
The keyword extractor is told to keep values out of keywords (a decimal comma split "5,1 x 10^4" into two).

### Run 3 moves to KVM4 (10.10.2026)

A cloud session's container is reclaimed when idle, which stopped the background runner after 7 of 480.
The run is unattended on KVM4 instead: `run_ecoa_ingest_kvm4.sh` (venv + `fetch_ecoa_corpus.py`, then
two one-at-a-time passes; log `/opt/ecoa_ingest/run.log`). It refuses to start while another ingest runs —
two runners against one dataset could upload the same certificate twice.

**Started 10.10.2026 17:52 UTC** as container `ecoa-ingest` on KVM4 (reached through kvm4-runner `POST /shell`
with `RUNNER_TOKEN`; `/exec` is not the route):

    docker run -d --name ecoa-ingest --restart unless-stopped --memory 1g \
      --env-file /opt/ecoa_ingest/.env -v /opt/ecoa_ingest:/work -w /work python:3.12-slim bash /work/entry.sh

`/opt/ecoa_ingest/app` = `ingestion/ecoa_runner` + `ingestion/common` (tar, SHA-256 checked on the host);
`.env` (mode 600) holds `RAGFLOW_API_KEY`; `entry.sh` = `ecoa_ingest_container_entry.sh` — idles after writing
`/work/ALLDONE`. Progress: `/opt/ecoa_ingest/run.log`, per-document detail `/opt/ecoa_ingest/migrate.log`.

### Run 3 on Claude (11.10.2026) — NVIDIA dropped

NVIDIA's hosted Kimi K3 became the bottleneck (14 of 18 failures were 504s after 15 min; 104–143 s per page
direct). The parser is now **Claude Sonnet 5.5 on the Max-plan API credits** (Head of QC: use the subscriptions
he pays for). Findings and the route:

- The Max plan's login cannot power a pipeline (Anthropic usage policy); its **API credits** can: $100 (Max 5x) /
  $200 (Max 20x) a month, linked to a Console org, **expiring each billing cycle**, no payment method needed.
- The credential is a user-scoped `sk-ant-usr` key; Anthropic answers 400 unless `anthropic-workspace-id` is sent,
  and RAGFlow's clients cannot add headers. The shared LiteLLM on KVM4 (`/opt/stacks/litellm`, network `ai-net`,
  also used by Letta and the WWF stack — **not** idle) now carries explicit `claude-{sonnet,opus,haiku}-5-5`
  routes that add the header and drop `temperature`/`top_p` (Claude 5.5 rejects both, RAGFlow sends both). New
  variable `ANTHROPIC_USR_KEY`; the older `ANTHROPIC_API_KEY` (invalid on 11.10) and the `anthropic/*` wildcard
  are untouched. Backups `config.yaml.bak-20261011-0244-claude`, `.env.bak-20261011-0244-claude`.
  Routes: `ingestion/litellm/DEPLOYED_CLAUDE_ROUTES_2026-10-11.yaml`.
- RAGFlow: provider OpenAI-API-Compatible, instances `CLAUDE_GW` (vision: sonnet, opus; chat: haiku) and
  `CLAUDE_GW_CHAT` (chat: sonnet, opus, haiku) at `http://litellm:4000/v1` (`register_claude_gateway.py` — keys are
  read on the server, never printed). One model name = one type per instance, hence two instances; an instance
  is verified with a chat model (RAGFlow's vision check sends a tiny image that Claude rejects).
- eCOA_PIPE and eCOA_DB_agent parse with `claude-sonnet-5-5@CLAUDE_GW@OpenAI-API-Compatible`; extractors stay on
  DeepSeek V4 Flash; tenant image2text default is the same model.
- Measured: Sonnet/Opus/Haiku 5.5 each read 5 of 5 test pages correctly in 2–6 s ($0.001 / $0.0125 / $0.03 a
  page). `BG1024_FHM_197-1-M-26`, which failed twice under NVIDIA, ingests in 63 s.

### Parser moved from Sonnet 5.5 to Haiku 5.5 (11.10.2026)

Measured on the 21 certificates of `ecoa_extraction_agent.json` `acceptance_tests` (10 hand-verified TYMC values
+ 11 must-not-flag): **Haiku 5.5 and Sonnet 5.5 both reproduce all 10 ground-truth values exactly and agree on the
other 11** (TYMC row only, microbiology certificates only; CNP potency and Farmahem mycotoxin tables are not
covered by this test). Cost per page: Haiku $0.0009, Sonnet $0.0124. The 4.x models were not tested because they
are dearer than their 5.5 equivalents (Sonnet 4.6 $3/$15 vs Sonnet 5.5 $2/$10; Opus 4.8 $5/$25 vs Opus 5.5 $4/$20;
list prices). RAGFlow allows one type per model name per instance, so Haiku vision lives in its own instance
`CLAUDE_GW_VIS` (verified with a Sonnet chat call). Sonnet and Opus stay registered for chat and as a second reader.

### Extractors on Haiku 5.5, and the editor trap (11.10.2026)

Questions and keywords now run on `claude-haiku-5-5@CLAUDE_GW_CHAT` (was DeepSeek V4 Flash). On 8 certificates of
every lab and type, with the pipeline's own prompts: code in every spelling in the keywords 8/8 for both; Haiku wrote
the English *and* Macedonian name of every parameter (DeepSeek mostly Macedonian only), more keywords (33 vs 26) and
the code in more questions (9.6 vs 8.5 of ~10); no number fragments in either. $0.0022 a certificate for both steps.
Judged by counts and by reading two certificates, not by a retrieval test.

**The editor trap.** A pipeline has two copies of each extractor's prompt: `components[...].params` (what runs) and
`graph.nodes[...].data.form` (what the editor shows). An API edit that touches only `components` is silently reverted
by the editor's autosave, which rebuilds `components` from the form — and re-nests `prompts`, so every ingest then
fails with "expected string or bytes-like object, got 'list'". On 11.10.2026 an open editor tab did exactly that every
~20 s (03:53 UTC, ingest stopped after 4 failures). Rules: edit pipelines through the API, write BOTH copies, and
keep the editor tab closed while a load runs; before restarting a load, GET the pipeline and check prompts are FLAT.
Haiku leaves blank lines between question pairs; the questions prompt now says not to.
