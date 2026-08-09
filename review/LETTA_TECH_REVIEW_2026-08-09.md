# Letta technology review — all Purely Plant repositories (2026-08-09)

Scope: all 35 repos under `3p4e` were enumerated; 12 candidates were cloned and swept for
Letta / pp-document-suite technology; findings were compared against the latest development
state (the ACME_SOP handover v2.0 + the 2026-08-08 live verification of the KVM4 server).
This report is the analytical basis for the letta-stack consolidation.

## 1. Where Letta technology lives — repo by repo

| Repo | Letta content | Verdict |
|---|---|---|
| **ACME_SOP** | `pp-document-suite/` — the engine line synced to the live Letta volume (hashes `a8a35700`/`1be84f35`/`1d54edab`/`a2060978`, verified on the volume 2026-08-08); Mode B deploy material; `ppdocwiz`; `openapi_letta.json`; the system handover | **Engine line A (deployed).** Copied to letta-stack; ACME_SOP to become a frozen mirror |
| **WEEKLY_WEED_FLOW** (updated 2026-08-08) | `docengine/` — a **diverged engine fork** (`build_from_md dfdd5271`, `pp_report 86feab6a`, `pp_format 7aa1d076` + `pp_format_layout_addons.py`) driven by a declarative Letta fleet (`agents/fleet.yaml`, `app/fleet.py`, ~11-call pipeline); `docs/DOCENGINE-CANON-2026-07.md` (binding canon, "SKILL v1.7.0"), `LETTA-DEDICATED-PLAN.md`, `LETTA-OPS-BACKLOG.md`, platform unification docs | **Engine line B (active, newest edits).** App + fork copied to `apps/wwf-docengine/`; key docs copied to `docs/wwf_*` |
| **Cannabis-EU-GMP-QMS-Creator** | `CONTENT_CREATOR_FRAMEWORK/` — the ORIGIN of the Letta RAG line: `letta_service.py`, `letta_tools.py`, `letta_workflow.py`, `agent_definitions.py` (11 agents: 10 chapter + 1 assembler), `letta_ingest_db1/db2.py`, `enrich_existing_passages.py` | **Lineage + still-referenced ingest tooling.** Letta files copied to `ingestion/qms-creator-framework/` |
| **CoA_TRACK** | `scripts/letta-imb-coas` (v2 ingester + integrity gate wiring + agent model policy), `letta-db2-gmp`, `letta-pq1`, `pq1-pipeline`, `qc_audits`, `kvm4-runner`, `network-shared`; `docs/ops/` verification record | **Current QC-side Letta tooling.** Copied to `ingestion/coa_track/` |
| **suma-platform** | `ISO17verSUMA/infrastructure/letta-stack/docker-compose.yml` — the ORIGINAL deploy compose of the live server; `letta_client.py`; suma-api agent code | ⚠️ **SECURITY: that compose is committed WITH live plaintext secrets** (DeepSeek key, Voyage key, Postgres password, LETTA_SERVER_PASS). See §4. Sanitized rewrite at `server/compose/` |
| **KVM4_VScode** | duplicate of the same `infrastructure/letta-stack/` compose (same exposure) | same as above |
| **COQ_GEN** | gateway/core_api with `LETTA_BASE_URL`/`LETTA_TOKEN` config — a Letta *consumer* | consumer only; nothing to move |
| **QC_LIMS_Ao** | `backend/app/services/letta_service.py` + CoA_TRACK integration planning docs | consumer only; nothing to move |
| **dev-environment-backup** (daily, 22:00) | Claude/MCP settings incl. Letta MCP references; **no pp-document-suite skill copy** | context only |
| Kade, EQ_MAN, EUGMPQMSAutomationPlatform | no Letta hits (Kade despite its "coa-tracker-rag-app" branch name — pre-Letta RAG) | nothing |

Not scanned (clearly unrelated by name/type): resiniverse-store, big-agi*, O2nail, xperia,
trichome*, tric, Verdict, swift-spider, instantly-ageless, cannabis-sample-tracker,
bigagitiny11, WEEKLY_SUMA_ISO17_v2(-main), T_PLAN, 01_TASKMASTA, AIRWAVE, 3p4e,
dev-env-config, QC_APP, QC_LIMS_APP, suma-platform beyond its infra dir.

## 2. THE central finding — two divergent engine lines

The "unified" pp-document-suite has quietly forked:

| | **Line A — ACME_SOP master** (= live Letta volume) | **Line B — WWF docengine fork** |
|---|---|---|
| build_from_md.py | `a8a35700` · 14 055 B | `dfdd5271` · 14 242 B |
| pp_report.py | `1be84f35` · 32 842 B | `86feab6a` · 25 640 B |
| pp_format.py | `1d54edab` · 16 538 B | `7aa1d076` · **33 404 B** |
| extra | — | `pp_format_layout_addons.py` (re-export shim) |
| Unique features | 2026-07 **layout brain**: data-driven `fixed()` compression (data never wraps), word-boundary entry-column matching, MK/EN-max label sizing, bulk full-width blocks, `[[FORM:grid]]` packing in `emit_form`, `[[PAGEBREAK]]`, landscape PAGE_W 27.16 | 2026-06-30 **§6D compact layout** promoted into pp_format: `kv_block()`/`cell08()`/`value_span()` first-class primitives (Head-of-QC corrections: value cells sized to expected hand-entry, minimal label cells, 6-col pack, 0.8 line spacing, section merge) |
| Driven by | `build_pp_document` Letta tool; ACME_SOP/CoA_TRACK document threads | `gf_*` agent fleet (declarative fleet.yaml), wizard pipeline, DOCENGINE-CANON |
| Deployed | `/root/.letta/pp-document-suite` (hash-verified 2026-08-08) | wwf docengine container(s) (`wwf_letta` compose project live on KVM4) |

**Neither is a superset.** Line A's layout-brain upgrades are absent from B; B's §6D
kv-primitives are absent from A. A real unification = merging B's `kv_block/cell08/value_span`
into A's `pp_format.py` + reconciling B's canon with A's SKILL — tracked as the top item in
START_HERE.md. Until then both lines live in letta-stack side by side (`pp-document-suite/` = A,
`apps/wwf-docengine/engine/` = B) and neither may be edited in its old home repo.

**Version-number collision:** WWF's canon calls its instruction set "SKILL v1.7.0"
(2026-07); the 2026-08-08 fix pack independently bumped ACME_SOP's `SKILL.md` to 1.7.0
with different content. The merged engine must issue as **v2.0.0** to clear the ambiguity.

## 3. Agent/source ownership map (66 agents, 9 sources — live 2026-08-08)

Corroborated by WWF's own read-only inventory (`docs/wwf_LETTA-DEDICATED-PLAN.md`):
- **Doc-engine fleet (letta-stack's concern):** qms_* / pharma_docx_formatter / pp_annex_* (9–10 agents), tools `build_pp_document`/`fetch_pp_document`, block `pp_house_rules`.
- **WWF app fleet:** `gf_*` (8, declaratively regenerable from fleet.yaml) + `planner-*` (5) + legacy `wwf_*`; sources DB1, DB3, GrowFlow_Weekly_Snapshots.
- **QC fleet (CoA_TRACK thread):** imb_qc_coa_agent, ecoa-qc-agent, ecoa_retrieval_gpt4o, pq1_water_qc_agent, equipment_manuals_agent, warehouse_quarantine_ocr_agent; sources ImB_QC_COAs (206 files), PQ1, Equipment_Manuals_PP, CoA_Individual_Split.
- **Other/legacy:** sentinel_*, VariationF*, ars_*, CoA/CoQ standalone pipeline agents.
- Embedding outliers (cannot cross-search): PQ1 source (text-embedding-3-large, 3072-dim), pq1_water_qc_agent archives (voyage-3-large), ecoa-qc-agent archives (letta-free).

Known shared-server pain (WWF ops backlog): ONE Postgres + ONE master key across ≥5
consumers → key rotation and the 0.16.8→0.17 upgrade are on HOLD; sprawl incidents
happened (45 orphaned agents once cleaned). WWF's answer is a dedicated instance per app;
letta-stack is the governance home where such splits get planned and the shared core is
versioned.

## 4. Security findings (action required by owner)

1. **The Letta server password ALSO leaks as a hardcoded default** in `3p4e/CoA_TRACK`
   (`scripts/letta-pq1/README.md` + `deploy.sh`, `scripts/letta-db2-gmp/README.md`) — the
   copies in letta-stack are scrubbed; fix the CoA_TRACK originals when rotating.
2. **Committed live secrets** in `3p4e/suma-platform` (`ISO17verSUMA/infrastructure/letta-stack/docker-compose.yml`) and duplicated in `3p4e/KVM4_VScode`: DeepSeek API key, Voyage API key, Postgres password, LETTA_SERVER_PASS — in git history, plaintext. **Rotate all four**, then purge or rewrite those files. (Values are NOT reproduced anywhere in letta-stack.)
3. The live compose on the VPS (`/opt/stacks/`, dockge-managed) is in NO repo — recover it via SSH/dockge into `server/compose/` (sanitized) so the deployment is reproducible.
4. `letta-postgres` has no known backup schedule — a `pg_dump` cron on the VPS is the single highest-value resilience item (all 30 archives + agent memory live there).

## 5. What was consolidated into letta-stack (and from where)

- `pp-document-suite/` ← ACME_SOP @ e9872c9 (engine line A, = live volume).
- `apps/wwf-docengine/` ← WEEKLY_WEED_FLOW @ HEAD 2026-08-08 (engine line B + fleet app).
- `apps/ppdocwiz/` ← ACME_SOP.
- `ingestion/coa_track/` ← CoA_TRACK (imb-coas v2 + integrity gate, db2-gmp, pq1, pipelines, kvm4-runner, network-shared).
- `ingestion/qms-creator-framework/` ← Cannabis-EU-GMP-QMS-Creator (Letta lineage: services, tools, 11-agent definitions, DB1/DB2 ingesters, passage enrichment).
- `server/manifests/2026-08-08/` ← FIRST live config export (66 agents, 9 sources, block, tools).
- `server/runbooks/` ← engine sync, bridge/REST quirks, render routes, 2026-08-08 verification.
- `server/compose/letta-compose.sanitized.yml` ← sanitized reconstruction (see §4 caveats).
- `docs/` ← system handover, Letta OpenAPI (v0.16.8), and the six key WWF platform/Letta docs.
- From the consolidating chat (previously untracked knowledge, now codified): the
  server-side build+render recipe and REST caps (runbooks), the manifest export tool, the
  live fixes of record (pp_house_rules path, gotenberg:3000), the A1/A2 render evidence.
