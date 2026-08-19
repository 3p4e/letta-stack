# Ingestion & RAG policy — RAGFlow on KVM4 is the pipeline

**Owner rule (18.08.2026, QC Manager).** All document ingestion and every RAG
pipeline runs on the **RAGFlow instance in Docker on the KVM4 server**. This
applies to the **results database** and to **all future databases**. Do not
create or extend a knowledge base anywhere else without the owner saying so.

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

## What this replaces

Ingestion has historically gone into **Letta sources** on the same host
(`https://ui.srv1231216.hstgr.cloud/v1/sources/...`, `LETTA_API_KEY`). Those
sources still exist and are still readable, but they are **not** the pipeline
going forward:

| Letta source | Records | Embedding | Status under this rule |
|---|---|---|---|
| `ImB_QC_COAs` | 263 | `openai/text-embedding-3-small` 1536d | legacy — migrate |
| `PQ1 Water Testing Results Report` | 148 | `openai/text-embedding-3-large` 3072d | legacy — migrate |
| `DB1_REGULATORY`, `DB2_GMP_PRO`, `DB3_PP_CURRENT_unified`, others | — | `text-embedding-3-small` 1536d | legacy |

Note the Letta water source records, in its own description, that **Voyage was
the original target** and OpenAI was a fallback "because Letta 0.16.x has no
voyage provider type". RAGFlow does support Voyage, so moving the pipeline
there also resolves that.

Exactly one Letta object uses Voyage today: the `pq1_water_qc_agent` **archival
memory** (`voyage-3-large`, 1024d) — the agent's own memory, not its documents.

## Before ingesting anything

1. Confirm the target dataset in RAGFlow and its embedding model — never create
   a second dataset for documents that belong in an existing one.
2. Diff against what the dataset already holds; ingest only what is genuinely
   new, and never re-upload a document under a second name.
3. Verify after upload: parse status and chunk counts per document, and report
   any document that parsed to zero or truncated content rather than counting
   it as ingested.
