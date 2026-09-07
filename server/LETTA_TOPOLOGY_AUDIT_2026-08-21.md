# Letta topology audit — KVM4, 21.08.2026

Read-only survey taken before any cleanup. **Nothing was changed, stopped or
deleted in producing this document.**

## Headline: there are three Letta stacks on KVM4, not one

| Stack | Compose dir | Agents | Sources | Exposure | Verdict |
|---|---|---:|---:|---|---|
| `letta` + `letta-postgres` | `/opt/stacks/letta` | 66 | 0 | **published :8283** | **OLD — to retire** |
| **`letta-6ou3-letta-1` + `letta-6ou3-db-1`** | `/opt/ai-stack/letta-6ou3-image-override.yml` | 8 | 0 | `https://letta-6ou3.srv1231216.hstgr.cloud` (also :32770) | **NEW letta-code — canonical** |
| `wwf-letta` + `wwf-letta-db` | `/opt/stacks/wwf_letta` | 20 | **4** | internal only | GrowFlow line — owner decision |
| `letta-scy7-letta-1` + `letta-scy7-db-1` | — | — | — | internal only | **out of scope — dedicated to other work** |
| Letta Cloud (`api.letta.com`) | — | 3 | n/a | SaaS | `Letta Code`, `RAG`, `Memo` |

### Owner direction (24.08.2026)

> Use `https://letta-6ou3.srv1231216.hstgr.cloud/`. Leave `letta-scy7-letta-1` and
> `letta-scy7-db-1` alone — they are dedicated to other things.

So the canonical endpoint for every Letta operation is the **hostname**, not the
published port, and the `letta-scy7` pair is excluded from this consolidation
entirely: not to be migrated, repointed, stopped or deleted. It appeared on the
host after this audit was written, which is why the survey above counts three
stacks and the host now runs four.

**Correction to an earlier reading of this estate:** `letta` (created 04.06.2026,
published on :8283) is the OLD deployment. `letta-6ou3` (created 16.08.2026,
published on :32770) is the NEW letta-code deployment and is canonical going
forward. Confirmed by the owner.

The MCP server (`letta-mcp-rust`) resolves `LETTA_BASE_URL=http://letta:8283` —
it is still bound to the **OLD** stack. Every Letta operation performed through
this session therefore ran against the deployment being retired.

## Finding 1 — the cut-over to letta-code was started and never finished

The new deployment is real and working, but only one consumer was moved to it.
Three are still wired to the old stack:

| Consumer | `LETTA_BASE_URL` | State |
|---|---|---|
| `wwf-docengine` | `http://letta-6ou3-letta-1:8283` | **migrated** |
| `letta-mcp-rust` | `http://letta:8283` | **still on old** |
| `wwf-scheduler` | `http://letta:8283` | **still on old** |
| `weekly_weed_flow-backend-1` | `http://letta:8283` | **still on old** |

Agent migration is likewise partial: the 8 `gf_*` agents were recreated on the
new stack on 17.08.2026, but **58 of the 66 agents exist only on the old one**.

`letta-6ou3`'s compose label points at `/docker/letta-6ou3`, which does not
exist — the stack is actually defined by
`/opt/ai-stack/letta-6ou3-image-override.yml`. The stale label should be
corrected so the stack is managable with `docker compose`.

The old `letta` is attached to **14 docker networks**, several belonging to
stacks that are already gone (`label-studio-1dns`, `agent-zero-t4sx`,
`agent-zero-ugsd`, `coa-tracker`, `visual-studio-code-server-7gqe`).

## Finding 2 — Letta is still acting as a RAG engine in `wwf-letta`

The owner rule is that Letta is excluded as a RAG engine and no Letta source is
to be created. `wwf-letta` holds **four live sources**:

| Source | Embedding |
|---|---|
| `DB3_PP_CURRENT_unified` | `text-embedding-3-small` |
| `DB1_REGULATORY` | `text-embedding-3-small` |
| `GrowFlow_Weekly_Snapshots` | `text-embedding-3-small` |
| `GrowFlow_Weekly_Snapshots_MASS` | `text-embedding-3-small` |

Two of these (`DB1_REGULATORY`, `DB3_PP_CURRENT_unified`) look like Purely Plant
QC/regulatory corpora and therefore fall under the RAGFlow-only rule. The two
`GrowFlow_Weekly_Snapshots*` sources belong to the WWF/GrowFlow product line,
which may be a legitimately separate system. **This needs an owner decision, not
an assumption.**

Note the embedding model: `text-embedding-3-small`, not `voyage-3-large`. These
were never part of the RAGFlow corpus.

### Owner decision (21.08.2026)

> `wwf-letta` migrates from the old `letta` to the new letta-code deployment. If
> migration is not possible, rebuilding WWF from scratch is acceptable.

**Migration is feasible — a rebuild is not required.** Verified:

| Check | Result |
|---|---|
| Letta version, all three stacks | **0.16.8** — identical |
| `letta/letta:0.16.8-wwf` | a plain retag; no custom labels or patched layers |
| `text-embedding-3-small` on target | **available** on `letta-6ou3` |
| Volume to move | 20 agents, 4 sources, **372 files** |

Per-source file counts: `DB3_PP_CURRENT_unified` 278, `DB1_REGULATORY` 77,
`GrowFlow_Weekly_Snapshots` 15, `GrowFlow_Weekly_Snapshots_MASS` 2.

**The migration forks, because of the RAG rule.** 355 of the 372 files
(`DB1_REGULATORY` + `DB3_PP_CURRENT_unified`) are Purely Plant regulatory and QC
corpora. Recreating them as Letta sources on the new stack would carry the very
thing the owner rule excludes onto the deployment meant to be clean. They belong
in RAGFlow. Only `GrowFlow_Weekly_Snapshots*` (17 files) is GrowFlow product
data, and whether even that stays a Letta source is a separate call.

Proposed split:

| What | Where | Why |
|---|---|---|
| 20 agents | → `letta-6ou3` | same version, direct export/import |
| `GrowFlow_Weekly_Snapshots` + `_MASS` (17 files) | → `letta-6ou3` sources, **if** GrowFlow needs Letta retrieval | product-line data, not Purely Plant QC |
| `DB1_REGULATORY` + `DB3_PP_CURRENT_unified` (355 files) | → **RAGFlow dataset**, not a Letta source | Purely Plant corpora; Letta is excluded as RAG engine |

Also required, and independent of the above: `wwf-scheduler` and
`weekly_weed_flow-backend-1` still point at `http://letta:8283` and must be
repointed at `letta-6ou3-letta-1:8283` before the old stack is stopped, or the
WWF scheduler and backend lose their Letta the moment it goes down.

## Finding 3 — 30 of 66 agents reference retrieval that no longer exists

On the canonical `letta` stack, 30 agents carry references to deleted Letta
sources or to archival-memory retrieval that has no backing store since the nine
sources were removed on 19.08.2026. They will answer, but from nothing.

Explicitly naming a dead source:

| Agent | Dead reference |
|---|---|
| `ecoa_retrieval_gpt4o` | `ImB_QC_COAs` |
| `imb_qc_coa_agent` | `ImB_QC_COAs` |
| `pq1_water_qc_agent` | `PQ1` |
| `equipment_manuals_agent` | `equipment_manuals` |
| `pp_annex_orchestrator` | `PQ1` |

A further 25 reference `archival memory` or an `attached source` generically:
the `VariationF-*` set (4), the CoA pipeline set (`CoA Ingestion`, `Parameter
Extraction`, `Compliance Analysis`, `Search Assistant`, `Report Generation`,
`CoQ Assembly`, `Specification Advisor`), the `pp_annex_*` set (4), the `qms_*`
set (3), `gmp_rag_agent`, `eu_gmp_compliance_expert`, `pharma_docx_formatter`,
`ecoa-qc-agent`, `gf_reg_checker`, `planner-executive-analytics`,
`warehouse_quarantine_ocr_agent`.

## Finding 4 — dead containers and reclaimable disk

21 of 57 containers are stopped:

| Stack | Containers | Stopped since |
|---|---:|---|
| CVAT (`cvat-ej3w-*`) | 15 | 3–4 weeks |
| ZoneMinder | 2 | 3 weeks |
| `big-agi-1dfu-big-agi-1` | 1 | 4 days |
| `sentinel_trading_agent` | 1 | 4 days |
| `deepseek-tui` | 1 | 4 days (exit 255) |
| `voxcpm-voxcpm-1` | 1 | 4 days |

`docker system df`:

| | Total | Active | Reclaimable |
|---|---:|---:|---:|
| Images | 43 | 41 | **22.94 GB** |
| Containers | 57 | 36 | 0.54 GB |
| Local volumes | 160 | 37 | **8.18 GB** |

**123 of 160 volumes are unreferenced.** Some may hold the only remaining copy
of data from stacks that were torn down — including, potentially, the nine Letta
sources deleted without backup. A blanket `docker volume prune` is therefore
**not** safe and is excluded from every option below.

## RAGFlow stack — healthy, untouched

| Container | Status |
|---|---|
| `ragflow-ragflow-cpu-1` | Up |
| `ragflow-es01-1` | Up (healthy) |
| `ragflow-mysql-1` | Up (healthy) |
| `ragflow-minio-1` | Up (healthy) |
| `ragflow-redis-1` | Up (healthy) |

## Proposed sequence

Ordered so that nothing irreversible happens before a restore point exists.

### Phase 0 — backup — **DONE 21.08.2026**
`/opt/backups/letta/20260821/`, all gzip-verified:

| File | Size |
|---|---|
| `old_letta-20260821.sql.gz` | 140 MB |
| `wwf_letta-20260821.sql.gz` | 86 MB |
| `new_letta6ou3-20260821.sql.gz` | 1.5 MB |
| `old_letta-agents.json` | 66 agents |
| `wwf_letta-agents.json` | 20 agents |
| `new_letta6ou3-agents.json` | 8 agents |

### Phase 1 — repair and redirect (reversible)
Rewrite the system prompt of the 30 orphaned agents so retrieval points at
RAGFlow (`https://ragflow.srv1231216.hstgr.cloud`, datasets `eCOA_INGEST`,
`eCOA_INGEST_SUMMA`, `STABILITY_PROGRAMME`) instead of a Letta source, and state
plainly that Letta holds no corpus. Agents that cannot be given a real retrieval
path are marked deprecated in their description rather than silently left
answering from nothing.

### Phase 2 — finish the cut-over (needs owner decision)
Repoint `letta-mcp-rust`, `wwf-scheduler` and `weekly_weed_flow-backend-1` at the
canonical deployment — `letta-6ou3-letta-1:8283` on the internal network, or
`https://letta-6ou3.srv1231216.hstgr.cloud` from outside it. `letta-scy7` is out of
scope and must not be touched. Decide the fate of the 58 agents that exist only on
the old stack — migrate from `old_letta-agents.json` or retire them. Then
unpublish :8283 and stop the old stack. Decide `wwf-letta`: keep as the GrowFlow
system of record, or migrate `DB1_REGULATORY` and `DB3_PP_CURRENT_unified` into
RAGFlow and drop those two sources.

### Phase 3 — delete deprecated (irreversible)
Remove the 21 stopped containers and their images. Volumes are handled
individually, by name, after confirming each is genuinely unreferenced — never
by `prune`.

## Open decisions

1. The 58 agents that live only on the old stack — migrate to letta-code, or
   retire? (`old_letta-agents.json` holds them.)
2. ~~`wwf-letta` — migrate or rebuild?~~ **Answered 21.08.2026: migrate to
   letta-code; rebuild acceptable if migration fails. Verified feasible, so
   migration it is.** Remaining sub-question: do the two
   `GrowFlow_Weekly_Snapshots*` sources stay Letta sources, or does GrowFlow
   also move to RAGFlow retrieval?
3. CVAT and ZoneMinder — genuinely finished, or paused and expected back?
4. Letta Cloud (`Letta Code`, `RAG`, `Memo`) — in scope for this consolidation
   or left alone?
