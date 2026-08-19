# RAGFlow ingestion tools

RAGFlow on KVM4 is the ingestion and RAG pipeline for every database — see
`server/runbooks/ingestion_policy.md`. Letta is not a RAG engine.

Environment: `RAGFLOW_API_KEY`, `RAGFLOW_API_SERVER`.

## `replace_reissued.py` — swap a truncated lab report for its reissue

A reissued report **replaces** its predecessor. It is never appended to it:
RAGFlow chunks on a token window rather than page boundaries, so there is no
page-level anchor to append against, and a reissue may amend an earlier page
as well as complete the report. One lab number, one document, one record.

```bash
python3 replace_reissued.py --check reissue.pdf          # gate only, no writes
python3 replace_reissued.py <dataset_id> reissue.pdf ...  # replace + verify
```

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
