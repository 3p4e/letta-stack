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

## Top open work items (priority order)

1. **Merge the two engine lines into v2.0.0** — graft line B's `kv_block()/cell08()/
   value_span()` (§6D) into line A's `pp_format.py`, reconcile the two "v1.7.0" instruction
   sets (canon vs SKILL.md), regression-test both consumer pipelines, then hash-gated sync
   to the volume. Until merged, do not edit either line without recording it here.
2. **Rotate the exposed credentials**: (a) the four in suma-platform / KVM4_VScode
   (DeepSeek key, Voyage key, letta-postgres password, LETTA_SERVER_PASS) — committed in
   plaintext; (b) the server password also leaks as a hardcoded default in CoA_TRACK
   letta-pq1/letta-db2-gmp files. Purge/fix the source files when rotating.
3. **Recover the authoritative live compose** from the VPS (`/opt/stacks/`, dockge) into
   `server/compose/` (sanitized) — the in-repo copy is a reconstruction with known drift.
4. **Schedule `pg_dump` of letta-postgres** on the VPS with rotation — the single
   highest-value resilience item.
5. Pending pushes from the consolidating session: letta-stack `main` itself (commit
   76d089b, blocked by session repo policy — grant the session repo access or start the
   next session ON letta-stack), the ACME_SOP fix-pack branch (patch in `delete/` here),
   and the ACME_SOP + WWF deprecation pointers.
6. The handover's §10 remainder: Mode B deploy, PP Doc Wiz deploy, orchestrator tool_rules,
   AM02.1 code confirmation by QA, the defunct :8787 sidecar decision.

## Note on this Drive folder

Pre-consolidation files are quarantined in `delete/` — trash that subfolder's originals in
the folder root if still present (Drive API used here cannot delete). Current layer:
START_HERE.md + LETTA_TECH_REVIEW_2026-08-09.md.
