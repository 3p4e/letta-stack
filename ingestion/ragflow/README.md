# RAGFlow ingestion tools

RAGFlow on KVM4 is the ingestion and RAG pipeline for every database — see
`server/runbooks/ingestion_policy.md`. Letta is not a RAG engine.

Environment: `RAGFLOW_API_KEY`, `RAGFLOW_API_SERVER`.

**Picking up the eCoA pipeline? Start with
[`HANDOVER_ECOA_INGESTION_2026-08-30.md`](HANDOVER_ECOA_INGESTION_2026-08-30.md)** — what
the 29–30.08.2026 verification found, what is already built, what is not, and the twelve
traps that each produced a confident wrong answer first. Then
[`ECOA_RECTIFICATIONS_2026-08-30.md`](ECOA_RECTIFICATIONS_2026-08-30.md) for every
inconsistency found in `eCoA_DATABASE` with its correction and evidence, and
`ECOA_RAG_PIPELINE_2026-08-30.md` for the design.

## Identity is read off the page, never off the filename

`doc_identity.py` decides whether we already hold a report by what is printed
on it, not what the file is called:

```
Лаб. број: 1468/2026          -> lab number, the dedup key
Датум на земање: 14.05.2026   -> sampling date, cross-check
Мерно место: ... -RO-E84-014  -> sampling point
Страна 1 од 4                 -> how long the report should be
```

A **scan** has no text layer, so its pages are rasterised and read by a vision
model, per `AGENT_MODEL_POLICY.md`:

    OCR / document vision -> kimi-k2.6 -> moonshot-v1-128k-vision-preview -> gpt-4o

Classical OCR is deliberately **not** used. These certificates are Macedonian
Cyrillic mixed with Latin chemical symbols, Greek letters and superscripts —
the case classical OCR handles worst — and the reasoning is already recorded in
`letta_host_tools/pp_ocr_scanned_pdf.py`, which was verified against GG1024 to
reproduce all 29 register rows exactly. The prompt carries that tool's rules:
transcribe verbatim, never improve, preserve Cyrillic, and pin chemical and
unit symbols to Latin so a Cyrillic-surrounded model does not return "ТНС" for
"THC".

Verified live: the identical report as a digital export and as a
differently-named image-only scan both resolve to `lab_no 1233/2026, sampled
04.05.2026, 3 of 4 pages` — one via the text layer, one via the vision chain.
So a scanned copy of something already ingested is recognised as the same
record and replaces it; it is not added alongside. (On that run Moonshot
answered 429 on both models and the chain fell through to `gpt-4o`, which is
what the fallback exists for.)

Where both forms exist, `better_of()` keeps the one with more pages, and on a
tie prefers the digital original over the scan (OCR text is a lossy reading).

A document whose lab number cannot be read even by OCR is **rejected**, not
guessed at — it cannot be matched against the corpus, so ingesting it would
risk exactly the duplication this is meant to prevent.

## `replace_reissued.py` — swap a truncated lab report for its reissue

A reissued report **replaces** its predecessor. It is never appended to it:
RAGFlow chunks on a token window rather than page boundaries, so there is no
page-level anchor to append against, and a reissue may amend an earlier page
as well as complete the report. One lab number, one document, one record.

```bash
python3 replace_reissued.py --index <dataset_id>          # build the content index
python3 replace_reissued.py --check reissue.pdf           # gate only, no writes
python3 replace_reissued.py <dataset_id> reissue.pdf ...  # replace + verify
```

`--index` reads every document already in the dataset and caches
`lab number -> document id`. That index is what makes filename-independent
matching possible; refresh it with `--refresh` after bulk changes.

Per file, stopping at the first failure:

1. **Completeness gate** — these reports state their own length in the footer
   (`Страна N од M`). A PDF holding fewer pages than it declares is still
   short: rejected, nothing touched.
2. **Diff against the ingested copy** — page by page. Identical earlier pages
   are reported. A **changed** page halts the replacement and prints which
   pages differ; an amended result is a QC event and a human decides
   (`--force` to proceed once reviewed).
3. **Replace** — delete the old document by id, upload the reissue.
4. **Verify** — parse, then require `chunk_count > 0`. A zero-chunk parse is
   never reported as ingested.

That last gate matters: 128 of 389 documents in `eCOA_INGEST` were sitting
unsearchable with zero chunks, most of them marked `DONE`. Status alone lies —
always check the chunk count.

## Known-incomplete water reports (audited 19.08.2026)

Verified by comparing each PDF's page count against the page total the
laboratory prints in its own footer. Awaiting reissue from ЦЈЗ Куманово:

| Lab no. | State |
|---|---|
| 1181, 1296, 1466 | blank export — no text at all (1466 = sampling point E43-012) |
| 1468 | 2 of 4 pages (E84-014) |
| 1233, 1253, 1340, 1400, 1402, 1403 | 3 of 4 pages |

The six 3-page reports are the quiet ones: they parse, produce chunks and look
healthy, but page 4 carries the closing results and signature block, so
retrieval answers from them while silently missing the tail. File size is not
a reliable tell — 1289, 1291 and 1361 are the same ~150 KB and are complete.

## eCOA_INGEST repair, 19.08.2026

The dataset held 389 documents of which **128 had zero chunks** — present but
unreachable by retrieval, and most of them marked `DONE`, so no status roll-up
would have flagged them. 115 of the 125 water reports were among them.

Every failure died at the same step, `"Start to generate meta-data for every
chunk"`, which costs ~45-60 s per document and calls an LLM per chunk. The
original bulk load swamped it. Re-parsing repairs them, but only at low
concurrency:

| Approach | Hit rate |
|---|---|
| 6 documents per batch | ~25% |
| 3 per batch, 10 s apart, two passes | 92 + 17 of 123 |
| 1 at a time, server idle | 10 of the last 14 |

**Result: 385 of 389 searchable.**

Four remain, all from the same family — `700094-5`, `-6`, `-8`, `-25`. They
are not defective: full text layers (13-15 k characters), and parsing itself
completes ("Finish parsing", all pages processed). They are simply larger than
the rest — 6 pages and 24-42 embedded images against 4 pages and 8 — so they
generate more chunks and therefore more metadata calls. `700094-7`, the
largest of the family at 697 KB, succeeded on retry with 82 chunks, so the
step is marginal for this size rather than incapable.

**Two levers if they matter enough to chase:**

1. Turn off `enable_metadata` on the dataset. Every one of the 128 failures
   died at that step, so this removes the failure mode outright. It costs the
   `update_time` / `file_name` chunk metadata, which is minor — both are
   already document attributes. It is a dataset config change on the server.
2. Check which model RAGFlow has bound to metadata generation. It is an LLM
   call, and this estate has had provider trouble: Moonshot was suspended for
   insufficient balance, then began returning 401 after recharge.

**Never trust `run` status alone.** `1464.pdf` reported `run=FAIL` while
holding 56 usable chunks, and 84 documents reported `DONE` with none. Gate on
`chunk_count`.
