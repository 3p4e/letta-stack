# START HERE — letta-stack (initial instruction)

**This repo is the dedicated home of ALL Letta technology for Purely Plant, and the ONLY
place it is developed from now on** (owner decision, 2026-08-09). It is self-contained:
normal development never requires cloning any other repository — everything Letta-related
was consolidated here after an in-depth scan of all 35 `3p4e` repositories
(`review/LETTA_TECH_REVIEW_2026-08-09.md` is the evidence and the map).

GitHub: https://github.com/3p4e/letta-stack · this Drive folder is the human/recovery layer.

## Read in this order

1. `review/LETTA_TECH_REVIEW_2026-08-09.md` — where everything came from; the two engine
   lines; the security findings. (Copy in this Drive folder.)
2. `docs/HANDOVER_PP_DocEngine_Letta.md` — the full system handover (engine, server, RAG).
3. `server/runbooks/` — how to touch the live server safely (sync, quirks, render routes).
4. `docs/wwf_DOCENGINE-CANON-2026-07.md` + `docs/wwf_LETTA-DEDICATED-PLAN.md` — the WWF
   line's binding canon and the dedicated-instance architecture plan.

## The map

| Path | What it is |
|---|---|
| `pp-document-suite/` | **Engine line A** — the deployed master (= live Letta volume, hashes verified 2026-08-08) |
| `apps/wwf-docengine/` | **Engine line B** — the WWF fork (§6D kv-primitives) + its declarative `gf_*` Letta fleet app |
| `apps/ppdocwiz/` | wizard/chat front-end for line A |
| `server/` | live-server governance: sanitized compose, dated config manifests, runbooks |
| `ingestion/` | corpus ingestion + QC gates (CoA_TRACK tooling; QMS-Creator lineage incl. the DB1/DB2 ingesters and 11-agent definitions) |
| `docs/` | system handover, Letta OpenAPI v0.16.8, key WWF platform/Letta docs |
| `scripts/export_manifests.py` | run after EVERY deliberate live-config change; commit the dated output |

## Standing rules

1. **Self-contained development.** Letta work happens here. Other repos consume the Letta
   server; they do not develop its technology. The old homes (ACME_SOP `pp-document-suite/`,
   WWF `docengine/engine/`) are frozen mirrors once their deprecation pointers land.
2. **No secrets, ever.** Env-var names only. The export tool hard-aborts on suspected secrets.
3. **Config drift must be visible**: live change → `export_manifests.py` → commit. Manifests
   are additive by date.
4. **Engine changes**: edit here → hash-gated volume sync (`server/runbooks/engine_sync.md`)
   → smoke test PASS → export + commit.
5. Deliverable QC/QMS documents (SOPs, CoAs, specs) do NOT live here — only the machinery.

## Top open work items

**The list lives in `review/OPEN_DECISIONS_2026-08-29.md`** — 24 items, each with what
the thing does, why it is open, the options, a recommendation and what changes. Read that
rather than a summary here, because a summary is what let the previous version of this
section go stale: it still had the engine merge as item 1 and said nothing about the
Letta source deletion, RAGFlow, or the security batch.

What needs a decision most urgently, as of 29.08.2026:

| | Item | Owner |
|---|---|---|
| A1 | kvm4-runner is internet-facing with root-equivalent access; the hardening is committed but **not deployed** | host |
| A2 | RAGFlow MCP authenticates no client and is publicly routed (accepted risk, 25.08.2026) | host |
| A3 | The Letta API is unauthenticated — `LETTA_SERVER_PASS` vs `LETTA_SERVER_PASSWORD`, and no `SECURE` flag | host |
| A4 | The RAGFlow API key is still in history at `83ae904` — rotate, then drop the gitleaks allowlist entry | host |
| B1 | ~13 certificates released against failing results need deviation records | QC |
| B2 | 30 of 66 agents retrieve from sources deleted 19.08.2026 — they answer from nothing | host |
| D3 | The engine sync runbook is **on hold** — syncing today would remove working table sizing from the engine that builds controlled documents | host |
| E1 | RAGFlow has no swap and loses the in-flight document under memory pressure | host |
| E4 | Still no scheduled `pg_dump` of letta-postgres — the highest-value resilience item, and the sources were already lost once | host |

Also standing, and not in that register because it is a build task rather than a
decision: recover the authoritative live compose from `/opt/stacks/` into
`server/compose/` (sanitized) — the in-repo copy is a reconstruction with known drift.

## Note on this Drive folder

Pre-consolidation files are quarantined in `delete/` — trash that subfolder's originals in
the folder root if still present (Drive API used here cannot delete). Current layer:
START_HERE.md + LETTA_TECH_REVIEW_2026-08-09.md.
