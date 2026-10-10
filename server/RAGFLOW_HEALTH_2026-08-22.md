# RAGFlow deployment and database integrity check — KVM4, 22.08.2026

Read-only. **Nothing was started, stopped, reindexed, reparsed or deleted**, and no
model configuration was touched. Every figure below was measured, not inferred.

Checked at 21:30–21:45 UTC against `https://ragflow.srv1231216.hstgr.cloud`, with
host access through the KVM4 runner.

> **All three findings below were repaired on 24.08.2026.** The verdict is kept as
> written so the record shows what was found; see **Remediation — 24.08.2026** for
> what was done, what it changed, and where two of the findings turned out to be
> wrong.

## Verdict

The deployment is healthy and retrieval works end to end on all three datasets.
Three things need attention, in this order:

| | Finding | Severity |
|---|---|---|
| 1 | **51 chunks that MySQL accounts for are missing from the search index** — `1200.pdf` and `1208.pdf` are under-indexed, so part of their content cannot be retrieved | **acts on retrieval quality** |
| 2 | **6 documents failed ingestion and were never recovered**; 4 of them contribute nothing at all | acts on coverage |
| 3 | `eCOA_INGEST`'s dataset counters are stale — the header says 9 148 chunks where its documents sum to 8 923 | cosmetic, but it is the number the API reports |

Everything else reconciles.

## Deployment

All five containers up, **zero restarts**, started 16:17:33 UTC today.

| Container | Image | State | Health |
|---|---|---|---|
| `ragflow-ragflow-cpu-1` | `infiniflow/ragflow:v0.26.4` | Up 5 h | no healthcheck defined |
| `ragflow-es01-1` | `elasticsearch:8.11.3` | Up 5 h | healthy |
| `ragflow-mysql-1` | `mysql:8.0.39` | Up 5 h | healthy |
| `ragflow-minio-1` | `pgsty/minio:RELEASE.2026-03-25T00-00-00Z` | Up 5 h | healthy |
| `ragflow-redis-1` | `valkey/valkey:8` | Up 5 h | healthy |

Processes inside the app container: `ragflow_server`, **one** `task_executor`
(`-t common`), `admin_server`, `sync_data_source`, three nginx workers. No OOM kill
on any container, and none on the host. Redis holds 756 keys, 751 with a TTL — a
working cache, not a stuck queue.

### Resource headroom

| | |
|---|---|
| Disk | 144 G used of 193 G, **50 G free (75 %)** |
| Host memory | 16 G total, 6.5 G available |
| `ragflow-cpu` | 3.50 GiB |
| **`es01`** | **1.483 GiB against a 2 GiB cap — 74 %** |
| MinIO volume | 7.47 GB · MySQL 993 MB · ES 306 MB · Redis 230 kB |

The Elasticsearch cap is the one number worth watching. 2 GiB is tight for a
13 744-document index carrying 1 024-dimension vectors, and index growth pushes
against it before anything else on this host does.

### Public API

`GET /api/v1/datasets` → **HTTP 200 in 1.34 s**. Retrieval was exercised on all
three datasets with Macedonian queries; the Voyage embedding path is live, since a
query cannot be embedded without it.

| Dataset | Query | Top hit | Similarity |
|---|---|---|---|
| `eCOA_INGEST` | `Страни материи FB032601 не одговара` | `ППК26127-ФИНАЛЕН.pdf` | 0.557 |
| `eCOA_INGEST` | `197-9-K/26 Farmahem канабиноиди` | `197-9-K-26 Pjureli Plant.pdf` | 0.578 |
| `eCOA_INGEST_SUMMA` | `GG1024 Gorilla Glue` | `LIST_OF_COAS_index.txt` | 0.586 |
| `STABILITY_PROGRAMME` | `стабилност 25C 60RH` | `STABILITY_GrapePie_P050022_m6_25C-60RH_PPK26032.pdf` | 0.565 |

Every top hit is the correct document. First query 9.1 s cold, then 1.0–1.6 s.

### Log

37 lines in five hours. Four `Can't connect to MySQL server … name resolution`
errors between 08:17 and 08:32 UTC — transient DNS during a network event, long
since recovered — and two 404s on `/`. The recurring
`load_user from jwt got exception` warnings are this session's own API-key calls
falling through the JWT path to the token check; all returned 200.

> The app container runs on **UTC+8**, so its log timestamps read eight hours ahead
> of the host. Worth knowing before correlating a log line with an event.

## Database integrity

### The three datasets reconcile on documents, not on counters

| Dataset | Docs (header) | Docs (actual) | Chunks (header) | Chunks (Σ documents) | Drift |
|---|---:|---:|---:|---:|---:|
| `eCOA_INGEST` | 389 | 389 | 9 148 | 8 923 | **−225** |
| `eCOA_INGEST_SUMMA` | 81 | 81 | 1 583 | 1 583 | 0 |
| `STABILITY_PROGRAMME` | 10 | 10 | 357 | 357 | 0 |

`STABILITY_PROGRAMME`'s token counter is wrong in the other direction — the header
says 11 787 where its documents sum to 23 741. Counters only; no data is affected.
The API reports the header value, so `eCOA_INGEST` advertises 9 148 chunks it does
not have.

### Referential integrity — clean

| Check | Result |
|---|---:|
| Documents pointing at a non-existent dataset | 0 |
| `file2document` rows with no document | 0 |
| `file2document` rows with no file | 0 |
| Datasets with no tenant | 0 |
| Documents with an empty storage location | 0 |
| Duplicate document name within one dataset | 0 |
| Documents with no `file2document` row | 81 |

The 81 are exactly `eCOA_INGEST_SUMMA`'s document count — that dataset was
populated through the API rather than the file manager, so its documents have no
entry in the file tree. Consistent, and not a fault.

All three datasets are pinned to `voyage-3-large@VOYAGE_AI@Voyage AI`. No mixed
embedding models.

### Index versus database

The index holds **13 744 documents** against a database total of 10 863 chunks.
That gap is almost entirely explained, and the unexplained remainder is the finding.

| Layer | Count |
|---|---:|
| Elasticsearch index total | 13 744 |
| — knowledge-graph entities and relations (no `doc_id`, `eCOA_INGEST` only) | 2 351 |
| — chunks carrying a `doc_id`, across 476 documents | 11 393 |
| MySQL `Σ document.chunk_num` | 10 863 |
| **difference** | **+530** |

Of that surplus, **447 chunks are marked `available_int: 0`** — excluded from
retrieval and from `chunk_num`, but still resident. `STABILITY_PROGRAMME` carries
exactly three per document, a uniform pattern that reads as parser output rather
than someone disabling chunks by hand. The rest is residue on five documents that
were parsed more than once.

**There are no true orphans**: every `doc_id` in the index has a row in the
database. Nothing is being retrieved from a document that no longer exists.

### Finding 1 — 51 chunks the database claims and the index does not hold

Two documents run the other way, and this is the one that costs retrieval quality:

| Document | `chunk_num` | In the index | Missing |
|---|---:|---:|---:|
| `1200.pdf` | 122 | 98 | **24** |
| `1208.pdf` | 112 | 85 | **27** |

Both are in `eCOA_INGEST`. The register believes those chunks exist; a search
cannot return them. They are the only two documents in the whole corpus in this
state, so the fix is narrow — reparse those two files and re-compare.

### Finding 2 — six documents failed and were left failed

All six are in `eCOA_INGEST`, all at `run=4`, `progress=-1`, from 21.08. Two
distinct failure modes, both silent terminations:

| Document | Chunks | Where it stopped |
|---|---:|---|
| `1220.pdf` | 54 of 71 generated | `Embedding chunks (8.20s)` — then nothing |
| `1377.pdf` | 64 of 75 generated | `Embedding chunks (3.13s)` — then nothing |
| `700094-5-2026 …` | **0** | `Finish parsing.` — never chunked |
| `700094-6-2026 …` | **0** | `Finish parsing.` — never chunked |
| `700094-8-2026 …` | **0** | `Finish parsing.` — never chunked |
| `700094-25-2026 …` | **0** | `Finish parsing.` — never chunked |

The four `700094` documents are State Phytosanitary Laboratory pesticide reports
and **contribute nothing to retrieval at all** — no chunks in the database, none in
the index. `1220.pdf` and `1377.pdf` are partially present, which is worse than
absent: a search returns some of the document and silently omits the rest.

The task table agrees — 481 tasks, 6 unfinished, 6 failed, newest 21.08 20:30:50.
Nothing has been queued since.

### MinIO

14 590 objects, 6.9 GiB across 14 buckets. Three buckets are the live datasets;
ten belong to knowledge bases that no longer exist.

| Bucket | Objects | Size | Belongs to |
|---|---:|---:|---|
| `2700caec…` | 13 773 | 6.8 GiB | `eCOA_INGEST` |
| `2e15c4ea…` | 367 | 163 MiB | `STABILITY_PROGRAMME` |
| `e2db9712…` | 81 | 108 KiB | `eCOA_INGEST_SUMMA` |
| `imagetemps` | 347 | 23 MiB | scratch |
| ten others | 22 | ~11 MB | **no such knowledge base** |

The orphaned buckets are all from 16.08 and hold 22 objects between them —
housekeeping, not a storage problem. `eCOA_INGEST` averages ~35 objects per
document because the vision parser stores a rendered image per page alongside the
source file; that is where 6.8 of the 7.5 GB sits.

## Recommended, in order

1. **Reparse `1200.pdf` and `1208.pdf`**, then re-compare index count against
   `chunk_num`. 51 chunks of certificate content are currently unsearchable.
2. **Requeue the four `700094` documents.** They parsed cleanly — all six pages
   each — and died before chunking, so a retry is likely to succeed. Then
   `1220.pdf` and `1377.pdf`, whose partial state should be cleared before the
   retry rather than added to.
3. **Refresh the `eCOA_INGEST` counters** so the API stops advertising 9 148
   chunks against 8 923, and `STABILITY_PROGRAMME`'s token count with it.
4. **Raise the Elasticsearch memory cap** above 2 GiB before the next large
   ingestion. At 74 % it has little room, and the corpus is about to grow.
5. Delete the ten orphaned MinIO buckets — by name, after confirming each is
   unreferenced. Low value, but they are pure residue.

Items 1 and 2 are write operations on the corpus and are **not** started here.

## Remediation — 24.08.2026

Owner authorised fixing everything fixable. What follows is what was done, what it
changed, and where the original diagnosis turned out to be wrong.

### Two failure modes, not one

The six failures had **two distinct causes**, and only the second leaves a message.

**Executor kills.** Queueing the eight documents produced three task-executor
restarts in five minutes (16:53:53, 16:56:33, 16:58:09 container time; before that,
restarts were ~14 h apart). No traceback precedes any of them — the process
vanishes and a fresh one initialises, the signature of an external kill rather than
a fault. Host memory was down to **985 MB available with `SwapTotal: 0`**, on a
16 GB box carrying 30 containers. Run the same document alone with memory free and
it completes: `700094-6` failed four times inside the queue, then finished in
isolation with 128 chunks in 578 s.

**Embedding-provider resets.** `700094-5` failed once with an explicit error:

> `[ERROR]Generate embedding error: Embedding request failed for VoyageEmbed.
> Error: Error communicating with VoyageAI: ('Connection aborted.',
> ConnectionResetError(104, 'Connection reset by peer'))`

178 chunks were generated and the embedding call was reset by the peer. A plain
retry cleared it. This is almost certainly what killed `1220.pdf` and `1377.pdf`
originally — both died immediately after an `Embedding chunks (Ns)` line.

Neither cause is a data problem. Both are recoverable, and **queueing heavy
documents one at a time recovered every one of them.**

### Correction — the Elasticsearch cap was a misread

The earlier finding said ES sat at 74 % of a 2 GiB cap with "little room". That
figure was container RSS, which is mostly Lucene page cache and is *expected* to
fill. The number that matters:

| | |
|---|---:|
| JVM heap max | 1 073 741 824 (1 GiB) |
| JVM heap in use | 178 355 264 |
| **heap utilisation** | **17 %** |

Elasticsearch is not under memory pressure, and raising `MEM_LIMIT` — shared by
five services in `/opt/stacks/ragflow/.env` — while the host itself was starved
would have made the executor kills *more* likely. **The cap was left alone.** The
metric to watch is heap, not container RSS.

### Correction — the ingestion cost has a cause worth knowing

`eCOA_INGEST` runs with **both** `raptor.use_raptor: true` **and**
`graphrag.use_graphrag: true`, on top of per-page vision parsing with
`gpt-4.1@openai-vlm`. GraphRAG is what produces the 2 351 knowledge-graph entities
and relations, and the combination is what makes a seven-page report expensive
enough to be killed.

It has a consequence the reparse exposed: **a document reparse rebuilds base chunks
only.** RAPTOR summary chunks are not regenerated until the dataset-level tree is
rebuilt, so a reparsed document legitimately returns fewer chunks than the register
recorded. No certificate text was lost — retrieval was re-tested and is unchanged.

### What was repaired

| Document | Before | After |
|---|---|---|
| `1200.pdf` | 122 claimed, 98 indexed | **56, consistent** |
| `1208.pdf` | 112 claimed, 85 indexed | **45, consistent** |
| `1220.pdf` | failed, 54 of 71 | **62, consistent** |
| `1377.pdf` | failed, 64 of 75 | **65, consistent** |
| `700094-5-2026` | failed, 0 chunks | **122** |
| `700094-6-2026` | failed, 0 chunks | **128** |
| `700094-8-2026` | failed, 0 chunks | **133** |
| `700094-25-2026` | failed, 0 chunks | **121** |

Dataset counters were then realigned to the documents they contain:

| Dataset | chunk_num | token_num |
|---|---|---|
| `eCOA_INGEST` | 9 880 → **9 303** | 958 587 → **937 761** |
| `STABILITY_PROGRAMME` | 357 (unchanged) | 11 787 → **23 741** |
| `eCOA_INGEST_SUMMA` | 1 583 (unchanged) | 46 180 (unchanged) |

Ten orphaned MinIO buckets were deleted. Each was first confirmed referenced
nowhere in `knowledgebase`, `document.kb_id`, `file.parent_id` or
`file.source_type`; all 22 objects were mirrored to
`/opt/backups/ragflow/20260824/minio_orphan_buckets.tar.gz` (10.8 MB, 33 entries,
gzip-verified) before removal. MinIO now holds four buckets: the three live
datasets and `imagetemps`.

### Verified end state

| Check | Before | After |
|---|---:|---:|
| Documents in a failed state | 6 | **0** |
| Documents with no chunk in the index | 4 | **0** |
| Documents where the index holds fewer chunks than the database claims | 2 (51 chunks) | **0** |
| Index `doc_id` values with no database row | 0 | **0** |
| Documents present in both database and index | 476 of 480 | **480 of 480** |
| Residual counter drift | 3 datasets | **none** |
| MinIO buckets for datasets that no longer exist | 10 | **0** |

Retrieval was re-tested on all three datasets. Every previous probe returns the
same document at the same similarity, and a new probe against the recovered water
reports —"Колиформни бактерии 700094 Генлајт вода" — now returns
`WATER_TESTING/7.8.6, 700094-25-2026` at 0.515, content that was unreachable
before.

The remaining index surplus of **+570** over the database total is the expected
population: chunks explicitly marked unavailable, plus RAPTOR summaries on
documents that were not reparsed. Neither is retrievable-but-unaccounted.

### Left undone — needs an owner decision

**Adding swap.** A 4 GB swapfile with `vm.swappiness=10` is the correct remedy for
a swapless host that kills its ingestion worker under load. The attempt was
**refused by this session's permission policy** and was not worked around. Until
swap exists — or roughly 2 GB is freed by stopping services — a bulk ingestion that
coincides with a memory spike will lose whichever document is in flight. The
working practice today is to queue heavy documents **one at a time**, which
recovered all eight here.

**Whether RAPTOR and GraphRAG both need to be on.** They are the reason ingestion
is expensive enough to be fragile, and the reason a reparse cannot restore a
document to its previous chunk count on its own. Turning either off changes
retrieval behaviour, so it is a QC decision, not a maintenance one. If they stay
on, the dataset-level RAPTOR tree should be rebuilt after any bulk reparse.

## Not RAGFlow, but found while looking

A **fourth Letta stack** now exists on this host: `letta-scy7-letta-1` and
`letta-scy7-db-1`, created roughly two hours before this check.
`server/LETTA_TOPOLOGY_AUDIT_2026-08-21.md` documents three. The audit's consolidation
plan is written against an estate that has since changed.
