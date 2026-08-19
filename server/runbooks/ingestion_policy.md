# Ingestion & RAG policy — RAGFlow on KVM4 is the pipeline

**Owner rule (18.08.2026, QC Manager).** All document ingestion and every RAG
pipeline runs on the **RAGFlow instance in Docker on the KVM4 server**. This
applies to the **results database** and to **all future databases**. Do not
create or extend a knowledge base anywhere else without the owner saying so.

**Letta is excluded as a RAG engine (19.08.2026).** RAGFlow supersedes it in
every respect. Letta agents remain in service, but they read from the **RAGFlow
databases** — they do not carry document sources of their own. Never create a
Letta source, and never upload a document to one, including from a
letta-code deployment.

## The target

| | |
|---|---|
| Service | `ragflow` compose project on KVM4 (`crimson.blaze`) |
| Containers | `ragflow-ragflow-cpu-1`, `ragflow-es01-1`, `ragflow-minio-1`, `ragflow-mysql-1`, `ragflow-redis-1` |
| Host ports | `8090 -> 80`, `8493 -> 443`; Elasticsearch `1200 -> 9200`; MySQL `3306`; Redis `6379` |
| Public URL | `https://ragflow.srv1231216.hstgr.cloud` (routed via the `traefik` container) |
| API base | `https://ragflow.srv1231216.hstgr.cloud/api/v1` |
| Version | `v0.26.4` — verified live 18.08.2026 (`GET /api/v1/system/version` -> `{"code":0,"data":"v0.26.4"}`) |
| Auth | `Authorization: Bearer <RAGFLOW_API_KEY>` — **not currently in this environment**; `/api/v1/datasets` returns 401 without it |
| Embeddings | Voyage (`VOYAGE_API_KEY` is set in the environment) — confirm the model on the dataset before ingesting |

Direct `IP:8090` is **not** reachable from a Claude Code sandbox (outbound is
proxied and non-standard ports are blocked). Use the HTTPS hostname.

## What this replaced — and the clean start

Ingestion historically went into **Letta sources** on the same host
(`https://ui.srv1231216.hstgr.cloud/v1/sources/...`, `LETTA_API_KEY`).

On the owner's instruction, **every Letta source was deleted on 19.08.2026
with no backup**, so the RAGFlow databases are built from a clean start. All
nine were removed (`DELETE /v1/sources/<id>` -> 200 each) and the source list
now returns **0**. What was destroyed:

| Deleted Letta source | Records | Rebuild path |
|---|---|---|
| `DB3_PP_CURRENT_unified` | 278 | from the QMS document tree |
| `ImB_QC_COAs` | 263 | re-extract from the per-batch eCoA PDFs in Drive |
| `PQ1 Water Testing Results Report` | 134 | re-ingest from the WATER_TESTING folder in Drive |
| `DB1_REGULATORY` | 77 | from the regulatory source documents |
| `DB2_GMP_PRO` | 74 | from the GMP source documents |
| `Equipment_Manuals_PP` | 34 | from the Memmert manuals |
| `GrowFlow_Weekly_Snapshots` | 6 | from the GrowFlow exports |
| `Superior_Primary_Packaging` | 4 | from the supplier qualification pack |
| `CoA_Individual_Split` | 0 | — |
| **Total** | **870** | |

**Three records had no source document anywhere** and were destroyed with the
rest, to be re-authored directly in RAGFlow: `QC_ERRATA_micro_OCR_defect_notice`,
`QC_ERRATA_potency_OCR_defect_notice`, and
`QC_QUERY_PPK26127_FatBastard_FB032601_foreign_matter_seed` (the FB032601
foreign-matter OOS query). Re-authoring them is outstanding work, not a
completed migration — treat the FB032601 query as an open QC record until it
exists again.

The deleted Letta water source recorded, in its own description, that **Voyage
was the original target** and OpenAI was a fallback "because Letta 0.16.x has
no voyage provider type". RAGFlow supports Voyage, so the move also resolves
that mismatch. One Letta object still uses Voyage: the `pq1_water_qc_agent`
**archival memory** (`voyage-3-large`, 1024d) — agent memory, not documents,
and therefore untouched by this policy.

## Before ingesting anything

1. Confirm the target dataset in RAGFlow and its embedding model — never create
   a second dataset for documents that belong in an existing one.
2. Diff against what the dataset already holds; ingest only what is genuinely
   new, and never re-upload a document under a second name.
3. Verify after upload: parse status and chunk counts per document, and report
   any document that parsed to zero or truncated content rather than counting
   it as ingested.
