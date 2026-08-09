# Letta ops backlog — live server maintenance (2026-07-16)

The GrowFlow platform's AI layer runs on a **live, shared Letta server**
(`letta` container, `http://host.docker.internal:8283`). As of the production
cutover it has **two production dependents**: the weekly-AI `scheduler`
(weekly snapshot → digest → Letta) and the newly-promoted `wwf-docengine`
(its regulatory-checker fleet). Any change here can degrade both — so each item
below is its own **separately-confirmed operation**, not a bundle.

## Live state (read-only diagnostic, 2026-07-16)

- **Server version:** `0.16.8`, health `ok`.
- **Agents:** **107** (the plan estimated ~54 — roughly doubled).
- **Sources: 9.** Eight are 1536-dim; **`PQ1 Water Testing Results Report` is
  3072-dim** — the known outlier. The others: `DB1_REGULATORY`,
  `DB2_GMP_PRO`, `DB3_PP_CURRENT_unified`, `ImB_QC_COAs`,
  `CoA_Individual_Split`, `Equipment_Manuals_PP`, `Superior_Primary_Packaging`,
  `GrowFlow_Weekly_Snapshots`.

## Backlog (each = its own confirmed operation)

| # | Item | Risk | Reversible? | Notes / recommended approach |
|---|------|------|-------------|------------------------------|
| 1 | **PQ1 3072-dim re-embedding → ✅ NO ACTION (investigated 2026-07-16)** | Med | — | PQ1 (3072-dim) is attached to **exactly one dedicated single-source agent** (`pq1_water_qc_agent`) — verified against the live server. Since it never mixes with a 1536 source, **there is no dimension conflict and nothing to fix**; the outlier is correctly isolated. Re-embed would be destructive for zero benefit. Revisit only if PQ1 must join a *multi-source* agent. |
| 2 | **Agent sprawl — 107 agents → ✅ RESOLVED 2026-07-16** | — | Done (snapshot taken) | **Root cause** (read-only enumeration): the old **qms-creator** (`qms-api`) re-created its section-author fleet on each run **with no ensure-by-name dedup** → **11 `GMP *` roles × 4 copies = 45 agents**. **Resolved:** `qms-api` was retired (see roadmap / DEPLOY.md), removing the source; then, after a `letta` DB snapshot (`pg_dump -Fc`, 198 MB, `/root/letta-pre-gmp-cleanup-*.dump`), the **45 orphaned `GMP *` agents were deleted (45/45, 0 failures)** → **107 → 62 agents**. The DocEngine `gf_*` fleet (8, one each) and the `planner-*`/`wwf_*` agents were untouched and verified intact. |
| 3 | **0.16.8 → 0.17 server upgrade → ⏸ HOLD (preflighted 2026-07-16)** | **High** | Hard (image swap + on-disk agent-state migration) | Server runs `letta/letta:latest` (= 0.16.8) from `/opt/stacks/letta/docker-compose.yml`, healthy. **No specific driver** for 0.17 was identified, and the **production DocEngine + weekly-AI scheduler now depend on this shared server** — a minor-version bump does on-disk agent-state migration that could break them. **Recommendation: hold** until there's a concrete need + a maintenance window. When done: snapshot `letta-postgres` (superuser `letta`, DB `letta` — NOT `postgres`), pin the target version (don't ride `:latest`), recreate, then re-validate the weekly-AI + both DocEngine paths end-to-end with rollback ready. |
| 4 | **Master-key rotation → ⏸ HOLD (preflighted 2026-07-16)** | **High** | New key must propagate everywhere atomically | Server auth = `LETTA_SERVER_PASS` on the `letta` container; the app's `LETTA_API_KEY` derives from it. Rotating invalidates the key across **five live consumers at once** — wwf_mass `backend`+`docengine`, prod `backend`+`docengine`, and the `scheduler` — each needing its `app.env`/`docengine.env` updated + container recreated, touching **production**. **No compromise indication**, so the risk/benefit doesn't favour rotating now. **Recommendation: hold** unless the key is believed compromised; then do it as one coordinated pass across all five consumers with the Letta server updated first. |
| 5 | **Provider-enum / temperature normalization → ✅ NO ACTION (audited 2026-07-16)** | Low–Med | — | Audited `llm_config` across all 62 live agents: **all have a valid model and function** (0 with no model). Config is heterogeneous — two working DeepSeek providers (`deepseek` native ×39, `openai`+BYOK `deepseek-prod` ×17), 6 legacy `gpt-4o` agents, one `voyage-3-large` embedding agent — but **not a defect**. The creation-time friction the handover flagged is already resolved (the `gf_*` fleet exists and runs, `letta:true`). Forcing normalization on live, prod-dependent, working agents is churn-with-risk. **No action** absent a concrete failure. |

## Standing guidance

- **Read-only first** for every item — inventory and confirm the exact defect
  before any mutation.
- **Snapshot `letta-postgres`** before items #2 (bulk delete), #3 (upgrade).
- **Never** rotate the master key or upgrade the server version without first
  enumerating every caller (`scheduler`, `wwf-docengine`, plus any external
  integration) and having the re-key / re-validate steps staged for all of them.
- These were deliberately deferred throughout the unification because they are
  operations on a live shared AI, orthogonal to the app build. The production
  cutover **increased** the blast radius (the DocEngine now depends on this
  server), so the bar for touching it is now higher, not lower.
