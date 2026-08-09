# Dedicated Letta per stack — design & migration plan (2026-07-19)

Owner question: *"isn't it better that we build a dedicated Letta database and
dedicated app shared memory — all Letta server features but enabled just for
the app we are building — and not get mixed up with other Letta memory created
during other Letta use; also, depending on user credentials and access levels
there should be differences in the agent capabilities."*

**Answer: yes, a dedicated Letta instance per stack is the right architecture,
and it is unusually cheap for this app because everything the app needs on
Letta is regenerable from this repo plus the app's own Postgres.** The
role-capability half is an app-layer concern and is already implemented
(see §4 — shipped 2026-07-19).

## 1. Why dedicated (evidence from the live shared server)

Read-only inventory of the shared instance (letta 0.16.8, KVM4):

- **65 agents, of which the app uses ~13**: the `gf_*` DocEngine fleet (8),
  the `planner-*` binding targets (5), plus legacy `wwf_*` coordinators. The
  other ~50 belong to unrelated projects (sentinel_*, VariationF*, pp_annex_*,
  ars_*, standalone CoA/CoQ agents, equipment/water/OCR agents…).
- **9 sources, of which the app uses 3**: `DB1_REGULATORY`,
  `DB3_PP_CURRENT_unified`, `GrowFlow_Weekly_Snapshots`.
- One Postgres `letta` DB and ONE master API key span all of it — five live
  consumers documented (mass+prod backend & docengine, weekly scheduler),
  key rotation and the 0.16.8→0.17 upgrade are both HOLD items *because* of
  that sharing (docs/LETTA-OPS-BACKLOG.md).
- Sprawl incidents have already happened on the shared box (the 45 orphaned
  `GMP *` agents cleaned in PR #33).

Isolation buys: (a) app conversation/archival memory can never mix with other
projects' RAG or context; (b) blast-radius containment both ways — other
projects' sprawl/upgrades can't break the app, and app fleet churn (ephemeral
reg-checker clones every wizard run) never pollutes the shared box; (c)
per-stack API keys (rotating one no longer risks five consumers); (d) GxP
data segregation — weekly snapshots carry operational data that today sits in
the same DB as unrelated experiments; (e) upgrade freedom per consumer.

## 2. Why it's cheap — everything is regenerable

| Asset on shared Letta | Rebuild path on a fresh instance |
|---|---|
| `gf_*` fleet (8 agents) | **Declarative**: `docengine/agents/fleet.yaml` + `ensure_fleet()` recreates by name on first use |
| `planner-*` agents | `backend/scripts/planner_prompts.py` (personas) — recreate + apply, then rebind via Settings→AI (ai_agent_bindings rows point at agent ids) |
| `GrowFlow_Weekly_Snapshots` source | Regenerable from the tasks DB: `weekly_snapshot.py run_all` re-derives every digest |
| `DB1_REGULATORY`, `DB3_PP_CURRENT_unified` | Two options: **(a) passage-level copy** — pg_dump the shared `letta` DB's sources/files/passages rows filtered to the two source ids and restore into the dedicated DB (preserves embeddings byte-for-byte, zero re-embedding, read-only on the shared server); **(b) re-ingest** from the original corpus (`1stDataKnowledge` folder on the host / Drive; ingest scripts vendored at `qms-creator/scripts/ingest_regulatory_db1.py`) |

## 3. Target architecture

One dedicated Letta per stack, internal-only:

```
wwf_mass stack                          wwf_app (prod) stack
  wwf-mass-letta   (letta 0.16.8 pinned)  wwf-letta
  wwf-mass-letta-db (postgres, own vol)   wwf-letta-db
  ← backend LETTA_BASE_URL                ← backend LETTA_BASE_URL
  ← docengine LETTA_BASE                  ← docengine LETTA_BASE
  ← scheduler (weekly snapshots)          ← scheduler
```

- No published ports; same-stack internal network only; per-stack
  `LETTA_SERVER_PASS` secret (ends the shared-master-key coupling).
- Pin the image to the same 0.16.8 line first (identical API behavior);
  the 0.17 upgrade becomes a per-stack decision afterwards, decoupled from
  every other project.
- The shared server keeps serving the OTHER projects untouched. App agents
  on it are retired later as a separately-confirmed cleanup op.

### Cutover runbook (wwf_mass first, prod owner-gated)

**STATUS 2026-07-20: steps 1-6 EXECUTED on wwf_mass** — see the
"Dedicated per-stack Letta" section in docs/DEPLOY.md for the full record
(vector-extension bootstrap, BYOK provider-row copy, the two fleet.py
fixes → docengine v8, memory caps, rollback). Prod (step 7) remains
owner-gated on the shared server.

1. Add `letta` + `letta-db` services to the stack compose (internal network,
   own volume, healthcheck).
2. Migrate the two corpus sources: passage-level copy (option a) —
   `pg_dump --data-only` of `sources/files/file_contents/passages` rows
   `WHERE source_id IN (DB1, DB3)` from the shared letta DB → restore into
   the dedicated DB (schema created by first letta boot). Verify passage
   counts match.
3. Point the stack's backend/docengine/scheduler `LETTA_*` env at the local
   instance; recreate those containers.
4. `ensure_fleet` runs on first wizard use (or trigger once); run
   `planner_prompts.py` to recreate planner agents; re-set the org's
   ai_agent_bindings to the new agent ids (Settings → AI).
5. Re-upload the current week's snapshot (`weekly_snapshot.py run_all`).
6. Smoke: SOP wizard end-to-end (reg-checker must cite DB1/DB3 passages),
   one planner invoke, assistant ping.
7. Prod: same steps at the owner's go; keep the shared-server agents frozen
   (not deleted) until both stacks have run a full week clean.

Rollback at any step = point `LETTA_*` env back at the shared server and
recreate the three consumers — the shared-side state is untouched throughout.

## 4. Role-differentiated agent capabilities (SHIPPED 2026-07-19)

Letta has no per-end-user auth — the app backend is the broker, so
capability differences are enforced there:

- **Access tier** — `FUNCTION_ROLES` in `backend/app/api/ai.py`: personal
  tier (voice_capture, translate_bilingual, draft_description) for every
  authenticated user; the nine corpus/planning functions require an elevated
  role. `invoke()` 403s below tier; `/ai/functions` filters its catalog so
  each role's UI only offers what it may use.
- **Grounding breadth** — the existing M2 `dept_scope` mechanism: the same
  elevated function grounds ONLY on a dept-scoped manager's department, but
  org-wide for executives/ADMIN/QP.
- **Authoring gates** — DocEngine generation stays behind the QMS_AUTHOR
  roles (`qms.py`); binding administration stays ADMIN (`ai.py`).
- Tests: `backend/tests/test_ai.py` (24, incl. the 5 matrix tests).

Future refinement on the dedicated instance: per-tier agents (e.g. a
USER-facing assistant with a narrower persona/memory than the manager one)
become trivial — new fleet.yaml entries + catalog rows, no shared-box risk.
