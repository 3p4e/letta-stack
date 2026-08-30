# eCOA_DB corpus run — consolidated plan (30.08.2026)

Single source of truth for the from-scratch run over the 291 documents in
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
| 15 | `desktop.ini` (Drive sync junk) deleted from the dataset — the corpus is **291** certificates, matching the legacy dataset |

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

1. **Regression gate** — re-run the 12-doc pilot set through the current runner;
   require: all previously confirmed values reproduced, `ППК25050` cert_code
   now captured, IJZ 752/2025 rows carry `method_accredited=false`.
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

## Outside this session's reach (needs the user)

- LiteLLM deploy on KVM4 (`ingestion/litellm/README.md`, three commands).
- `docker logs` on the 5 failed executor tasks.
- Register edits: B-row cert codes; F3 (ППК25139 second analysis) decision.
- `SUPERSEDED_CRITERIA['loss_on_drying'].until` changeover date from the
  specification version history.
