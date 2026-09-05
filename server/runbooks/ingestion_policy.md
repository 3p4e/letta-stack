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

Three QC-authored records were destroyed with the rest and are to be
re-authored in RAGFlow as part of the rebuild: `QC_ERRATA_micro_OCR_defect_notice`,
`QC_ERRATA_potency_OCR_defect_notice`, and
`QC_QUERY_PPK26127_FatBastard_FB032601_foreign_matter_seed`. They were
commentary on source documents that are all still in Drive — the FB032601
query derives from certificate ППК26127, which is on file — so they are
re-authored from the evidence like everything else, not recovered.

The deleted Letta water source recorded, in its own description, that **Voyage
was the original target** and OpenAI was a fallback "because Letta 0.16.x has
no voyage provider type". RAGFlow supports Voyage, so the move also resolves
that mismatch. One Letta object still uses Voyage: the `pq1_water_qc_agent`
**archival memory** (`voyage-3-large`, 1024d) — agent memory, not documents,
and therefore untouched by this policy.

## Code retired with the sources (29.08.2026)

The owner's rule is that what was physically deleted from the server is
discarded from the code too. These ingested **into the deleted Letta sources**,
so they could not work and would have violated the rule above if they had:

| Removed | Fed |
|---|---|
| `ingestion/coa_track/letta-imb-coas/deploy.sh` | created the `ImB_QC_COAs` source + `imb_qc_coa_agent` |
| `ingestion/coa_track/letta-imb-coas/ingest_imb_coas.py` | `ImB_QC_COAs` |
| `ingestion/coa_track/letta-imb-coas/ingest_imb_coas_v2.py` | `ImB_QC_COAs` (OCR variant) |
| `ingestion/coa_track/letta-pq1/` (whole bundle) | created and filled `PQ1 Water Testing Results Report` |
| `ingestion/coa_track/pq1-pipeline/fix_c71.py` | renamed 6 files inside that same source |

Two orphans went with them — `ingestion/coa_track/kvm4-runner/gdrive_pull.py`
and `ocr_batch.py`. Neither had a caller anywhere in the repository, and
`ocr_batch.py`'s single-model OCR role is superseded by the documented chain in
`ingestion/ragflow/README.md`.

`scripts/policy_check.py` rule 2 was widened in the same change to read shell
scripts as well as Python. It had only ever scanned `.py`, so the two
`deploy.sh` files created Letta sources over `curl` without tripping it —
the rule now covers the way this repository actually did it.

### Provenance labels: corrected, not repointed

About a dozen builders carry `ImB_QC_COAs` in a provenance string. They split
two ways, and the difference matters because these are QC deliverables:

- **Present-tense claims** — "the authoritative results remain the ImB_QC_COAs
  knowledgebase", "a result can be uploaded to the source directly". These are
  now false, and the second one instructs the reader to do what this policy
  forbids. **Corrected.**
- **Dated verification records** — "4,134 passages scanned live", "263 files,
  all completed (verified live 13.08.2026)", and the weekly QC activity report's
  account of deduplicating against the live source. Those checks were really
  performed, against a store that really existed on those dates. Repointing them
  at RAGFlow would assert a verification that was never run there — a worse
  defect than a stale name. **Left standing, annotated** with the retirement so
  no one chases a source id that no longer resolves.

Where a name is an extraction stamp (`build_ecoa_register.py`'s `SOURCE`), the
historical name stays and a separate `RETIRED` note carries the rest, rather
than the retirement clause being wedged into a value that gets interpolated into
several different sentences.

### Dataset naming — `CoA_DATABASE_2026` is canonical

The same RAGFlow dataset, id `f29f8f58a13c11f1858cf58865604f65`, appears under
two names in this repository: **`CoA_DATABASE_2026`** in
`ingest_coa_database_2026.py` and `reclassify_watcher.py`, and
**`eCoA_DATABASE`** throughout `deliverables/qc_register/` and the potency
methodology.

`CoA_DATABASE_2026` is the dataset's actual name in RAGFlow and is therefore
canonical; `eCoA_DATABASE` is an alias the deliverables adopted. The alias is
**not** being renamed across the issued deliverables — that would churn the text
of regulated artifacts to no benefit. Use the canonical name in new code, and
read the two as one dataset.

What was **kept**, and why the deletion rule does not reach it:

- The builders in `letta-imb-coas/` read local and Drive data and emit
  deliverables. Some still carry `ImB_QC_COAs` in a provenance label; the label
  is stale lineage, not a live dependency.
- `rewire_agents.py` / `rewire_via_rest.py` set agent `llm_config`. They touch
  no sources, and the agents are still in service.
- `server/manifests/2026-08-09/**` is a dated snapshot. Deleting the record of
  what existed would destroy the evidence that it was deleted.
- The four sources on the **`wwf-letta`** stack (`DB3_PP_CURRENT_unified`,
  `DB1_REGULATORY`, `GrowFlow_Weekly_Snapshots`, `…_MASS`) are live. The
  19.08.2026 deletion hit the old `letta` stack, not that one.

## Before ingesting anything

1. Confirm the target dataset in RAGFlow and its embedding model — never create
   a second dataset for documents that belong in an existing one.
2. Diff against what the dataset already holds; ingest only what is genuinely
   new, and never re-upload a document under a second name.
3. Verify after upload: parse status and chunk counts per document, and report
   any document that parsed to zero or truncated content rather than counting
   it as ingested.
