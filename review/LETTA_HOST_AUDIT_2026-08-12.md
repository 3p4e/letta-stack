# Letta host — live runtime audit (2026-08-12)

Companion to `LETTA_TECH_REVIEW_2026-08-09.md`, which was static analysis of the repos.
This one is **live-probed**: every fact below was read from the running server on
2026-08-12 via the Letta REST API (health, `/v1/sources`, `/v1/agents`, `/v1/tools`,
`/v1/jobs`) and provider endpoints, cross-checked against the Letta 0.16.8 source and the
committed `docs/openapi_letta.json`. Read-only — nothing on the host was changed.

Where the two reviews overlap (secrets, backups, the embedding outlier), this one confirms
or updates from live state rather than repeating; the new material is the runtime behaviour
the static pass could not see.

## Server — healthy core

| | |
|---|---|
| Version | **0.16.8** (`GET /v1/health/` → `{"version":"0.16.8","status":"ok"}`) |
| Environment | `LETTA_ENVIRONMENT=PROD`, single uvicorn worker, port 8283 |
| Database | PostgreSQL 15 + pgvector, DB `letta`, user `letta` |
| Redis | up (`PING` → `+PONG`) — `localhost:6379` |
| Jobs | **0** in any state — no stuck or orphaned ingestion |
| Sources | 9; every file across all populated sources is `processing_status=completed` |
| Agents | 66 |
| Tools | 33 registered, incl. the custom `pp_ocr_scanned_pdf` (persisted) |
| Chat provider | DeepSeek at `api.deepseek.com/v1`; `deepseek-v4-pro` / `deepseek-v4-flash` **are valid there** (the endpoint serves exactly those two — a proxy/custom deployment) |
| Embeddings | OpenAI `text-embedding-3-small` (1536-d) on 8 of 9 sources |

The core is sound: healthy, migrated, all ingestion complete, no stuck jobs, dependencies
reachable. The findings below are configuration and hygiene, not an outage.

## Findings

### 1. 🔴 The API is unauthenticated — verified, with root cause

An **unauthenticated** `GET /v1/agents` (no `Authorization` header) **succeeded** against the
live server. Auth is not being enforced. There are two independent reasons, both confirmed:

- **Wrong variable name.** The server reads **`LETTA_SERVER_PASSWORD`**; the deployment sets
  **`LETTA_SERVER_PASS`** (live env, and `server/compose/letta-compose.sanitized.yml:48`).
  `LETTA_SERVER_PASSWORD` is therefore unset, so Letta autogenerates a random password
  (`secrets.token_urlsafe(16)`) that nobody holds.
- **No `SECURE` flag.** Even a correctly-named password is only enforced when the image is
  started with `SECURE=true` (which `startup.sh` maps to `--secure`, installing the
  password middleware). The compose sets no `SECURE`, so the middleware is never installed.

The value currently in `LETTA_SERVER_PASS` is also a weak, guessable default-style string.

**Fix:** set `SECURE=true` **and** rename the variable to `LETTA_SERVER_PASSWORD`, with a
strong secret (`openssl rand -base64 32`). Verify afterwards that an unauthenticated request
returns 401/403. Confirm the port's network exposure on the live box (`/opt/stacks/`,
dockge-managed, not in any repo) — if 8283 is reachable beyond localhost/the Docker network,
this is urgent; if strictly internal, it is still wrong but contained.

### 2. 🟠 The model/embedding env vars in the compose are no-ops

Live env and the committed compose both set `LETTA_LLM_MODEL`, `LETTA_LLM_PROVIDER`,
`LETTA_EMBEDDING_PROVIDER`, `LETTA_EMBEDDING_MODEL`. **None of these are settings Letta
reads.** Server-wide defaults come only from `LETTA_DEFAULT_LLM_HANDLE` /
`LETTA_DEFAULT_EMBEDDING_HANDLE`; otherwise model choice is per-agent at creation
(`llm_config` / `embedding_config`).

The proof is in the contradiction: the compose declares `LETTA_EMBEDDING_MODEL=voyage-3`
and `LETTA_EMBEDDING_PROVIDER=voyageai`, but the live sources actually embed with
**openai / text-embedding-3-small**. If those vars did anything, the embeddings would be
Voyage. They aren't. The agents run DeepSeek/OpenAI purely because each agent's config was
set at creation.

**Fix:** delete the four dead vars to stop them implying a control they don't have; if a
server-wide default is wanted, set `LETTA_DEFAULT_LLM_HANDLE` / `LETTA_DEFAULT_EMBEDDING_HANDLE`.

### 3. 🟠 Custom tool code runs in a LOCAL sandbox with full access to host secrets

No `LETTA_E2B_API_KEY` is set, so Letta's tool sandbox falls back to **LOCAL** — custom
tool code executes in a venv **on the server host, inside the server's own process
environment**. Any custom or LLM-authored tool can read `OPENAI_API_KEY`,
`DEEPSEEK_API_KEY`, `MOONSHOT_API_KEY`, `LETTA_PG_URI`, the Postgres password, etc.

This is not hypothetical here: custom tools do run (`pp_ocr_scanned_pdf`, `build_pp_document`),
and the diagnostic tools used for *this* audit demonstrated it directly — a
`run_from_source` function was able to enumerate the full process environment. Letta
recommends E2B precisely to isolate this.

**Fix:** set `LETTA_E2B_API_KEY` (or Modal) so tool code runs off-host; failing that, treat
every tool author as trusted with all server secrets and rotate keys after any untrusted
tool runs.

### 4. 🟡 Embedding-space outlier (confirmed live, isolated — safe for now)

`PQ1 Water Testing Results Report` embeds with **`text-embedding-3-large` (3072-d)**; the
other eight sources are **`text-embedding-3-small` (1536-d)**. An agent and all of its
attached sources must share one embedding model/dimension or cross-source semantic search
breaks. This is safe **only because** the 3072-d source is attached to a single-source agent
(`pq1_water_qc_agent`). Do not attach it to a multi-source agent, and don't attach a 1536-d
source to that agent. (Already noted in the ops backlog; confirmed still true live.)

### 5. 🟡 `imb_qc_coa_agent` — configuration quality

The canonical QC agent (`agent-edf27c5c…`) has several issues, none fatal but all worth fixing:

- **Stale system prompt** — it states the source "contains **50** Certificates of Analysis";
  the source now holds **263**.
- **`temperature: 1.0`** — far too high for a compliance-grade retrieval agent, which should
  run near-deterministic (~0–0.3) to avoid inventing values.
- **Contradictory tool-call setting** — `llm_config.parallel_tool_calls=false` while
  `model_settings.parallel_tool_calls=true` on the same agent.
- **No core-memory blocks** — the verbose payload returns `memory.blocks: []`. Unusual for a
  Letta agent (normally `human`/`persona` are pinned); `agent_type` is `Other`, so it was
  likely created minimally via API. Worth a deliberate check of whether it is meant to carry
  core memory.

Note the routing targets its prompt names (`eu_gmp_compliance_expert`, `qms_gmp_auditor`,
`pq1_water_qc_agent`) and the tool it calls (`semantic_search_files`) **all exist** — those
references are valid.

### 6. 🟡 Orphaned empty source

`CoA_Individual_Split` (`source-aa59e5ef…`) — **0 files, 0 attached agents**, created
2026-05-23, never populated. Dead entry; candidate for deletion once confirmed unneeded.

### 7. 🟡 Environment-config inconsistencies

- `LETTA_DISABLE_SQLALCHEMY_POOLING=true` **and** `LETTA_PG_POOL_SIZE=25` +
  `LETTA_ENABLE_DB_POOL_MONITORING=true` — if pooling is disabled the pool settings are moot;
  pick one posture.
- `POSTGRES_PASSWORD` is 5 characters — weak.
- ClickHouse vars are set (`LETTA_CLICKHOUSE_DATABASE=otel`) but
  `LETTA_TELEMETRY_PROVIDER_TRACE_BACKEND=postgres` — the ClickHouse config appears unused.
- `image: letta/letta:latest` (compose line 36) — unpinned; an image pull can trigger an
  Alembic agent-state migration at boot and a minor bump can break dependents. Pin the tag
  and `pg_dump -Fc` before any upgrade (ties to the still-open backup gap from the 08-09 review).

### 8. ℹ️ There is no source-scoped semantic-search endpoint (corrects an earlier assumption)

The 404 seen earlier on `POST /v1/sources/{id}/passages/search` is correct behaviour: that
route **does not exist** in 0.16.8, and no HTTP endpoint does semantic search scoped to a
single source's passages. The real surface:

- `GET /v1/sources/{id}/passages` — **list only**, pagination (`after`/`before`/`limit`), no
  query. This is what the eCoA-register build used, so its "retrieval" was a passage
  **listing**, not a semantic match — accurate for enumerating the corpus, but it did not
  rank by the query.
- `POST /v1/passages/search` — searches **archive** passages, scoped by `agent_id` or
  `archive_id` (no `source_id`).
- `GET /v1/agents/{id}/archival-memory/search?query=…` — semantic search of an agent's
  archival memory.
- Intended path for semantic search over source content: **attach the source to an agent**
  and let it call `search_file` / `semantic_search_files`.

### 9. ℹ️ The KVM4 MCP wrapper reports false zero counts (tooling bug, not a host fault)

The `mcp__Letta_KVM4_MCP__*` convenience tools return **`file_count: 0` and
`attached_agent_count: 0` for every source**, and **`tool_count: 0` / `tool_ids: []`** for
agents, when the raw Letta API shows non-zero values (ImB_QC_COAs really has 263 files and 2
attached agents; all 66 agents carry tools). Anyone trusting those wrapper fields gets false
emptiness. Prefer the raw endpoints (`/v1/sources/{id}/files`, `/v1/sources/{id}/agents`) or
`run_from_source` probes for counts until the wrapper is fixed.

## Priority order

1. **Enforce auth** (#1) — set `SECURE=true` + `LETTA_SERVER_PASSWORD=<strong>`; verify 401 on
   an unauthenticated call; confirm 8283's network exposure.
2. **Isolate tool execution** (#3) — set `LETTA_E2B_API_KEY`, or accept that all tool authors
   hold every server secret.
3. **Backups** (#7 / carried from 08-09) — a `pg_dump -Fc` cron; pin the image tag.
4. Clean the dead model vars (#2), fix the QC-agent config (#5), delete the empty source (#6),
   reconcile the pooling/telemetry inconsistencies (#7).
5. Keep the 3072-d source isolated (#4).

Everything here is verify-then-change on the live box (`/opt/stacks/`); this audit changed nothing.
