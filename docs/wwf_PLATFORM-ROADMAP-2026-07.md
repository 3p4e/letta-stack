# Purely Plant Unified Platform — Master Analysis & Implementation Roadmap

**Date:** 2026-07-16 · **Owner:** Purely Plant GmbH (Macedonian EU-GMP medical-cannabis facility)
**Author:** engineering · **Status:** living document — the single source of truth for sequencing every module

> This document exists because the platform's scope expanded rapidly: a document
> engine, a next-generation task manager, and **six imported repositories** now
> all target one system. Grinding them out ad-hoc would multiply data models and
> CoA pipelines. This roadmap fixes a **logical, dependency-aware, GxP-safe
> order** and a **repeatable method**, so every module lands additively on one
> spine, test-first, with the owner gating production.

---

## 1. Executive summary

**One platform. One login. One URL. One database spine.** Everything absorbed
into the live WWF/GrowFlow foundation by the **strangler-fig** pattern
(`docs/UNIFICATION-ANALYSIS-2026-07.md`, Option B) — never a second app, never a
forked stack, always the same containers so executives keep the same links.

Three things are already true and verified:

1. **The foundation is mature and in production** — FastAPI over two Postgres
   DBs (`wwf_users` + `wwf_tasks`), row-level security, per-request identity
   GUCs, hash-chained tamper-evident audit triggers, 13-role model, bilingual
   MK/EN vanilla-JS PWA. ~25 real users. 289 backend tests, path-scoped CI,
   disciplined test→prod deploys on kvm4.
2. **The DocEngine is built and running on the test server** — a dedicated
   Letta-powered FastAPI service that adopts the production pp-document-suite
   formatting engine completely and merges the questionnaire→SOP/annex authoring
   workflow. Verified end-to-end on wwf_mass (a real questionnaire→annex round
   trip produced a `RESULT: PASS` controlled .docx).
3. **The task-management upgrade (priority #1) is complete on the test server**
   — T1–T4 (dependency graph, node-kind task tree, cross-department handoff
   lifecycle, in-app team digest, AI-native planning) built, tested, and
   deployed to wwf_mass.

**Status as of 2026-07-16:** the module-consolidation program is essentially
**done on the test server**. The central §3 finding held — **CoA_TRACK, COQ_GEN,
and the CoA/COQ parts of the QC-LIMS corpus collapsed into a single certificate
pipeline built on the DocEngine** (Phase 3, complete), never triplicated.
Phases 0–3 all live + live-smoked on wwf_mass; the QC LIMS module carries five
units (U1–U5). What remains is **owner-gated** — acceptance tests + the staged
prod promotion (§8) — plus a few deferred low-priority QC leaves.

---

## 2. Current state

> **⚠️ The table below is a 2026-07-16 SNAPSHOT and its version numbers are all
> superseded. `docs/DEPLOY.md` is the authoritative record of live image tags and
> migration heads** — it is updated on every deploy, this table was not, and two
> copies of a version number will always drift. Kept for the environment shape
> and the standing rules underneath it, not for the numbers.
>
> Two things in it are wrong in kind rather than degree, verified against the
> host on 2026-07-30:
>
> - **There is no `wwf_mass` test stack any more.** No running container, no
>   stopped container. Three `wwf_mass_*` *volumes* survive the name — and one of
>   them, `wwf_mass_letta_pgdata`, is the **live production Letta data volume**
>   despite what it is called, while `wwf_mass_qms_output` holds 238 generated QMS
>   documents. Do not reason from those names to "leftover test data", and do not
>   remove them.
> - The DocEngine column says `v3`; it is running `v8`.

| Environment | Backend | Frontend | tasks-DB | Extra services | Notes |
|---|---|---|---|---|---|
| **Production** `wwf_app` (`https://wwf…hstgr.cloud`) | **v54** | **v76** | alembic **0027** | `growflow-docengine:v3` | The 25-user live system. **Cut over 2026-07-16** to the full unified stack (TMS + QC LIMS U1–U6 + certificate pipeline U1–U4 + DocEngine). Migrations 0017–0027 applied additively (existing task data intact); pre-cutover DB dump taken. Live-smoked green. **+ SUMA audit-prep tracker promoted 2026-07-16** (backend v53→v54 / frontend v74→v76, **no migration** — pure read over `tasks.tags`; scheduler left on v53; 556 tasks intact; live-smoked). |
| **Test** `wwf_mass` (`https://wwf-mass…`) | **v53** | **v74** | alembic **0027** | `qms-api:v1`, `growflow-docengine:v3` | DocEngine + TMS (T1–T4) + QC LIMS **U1–U6** + the full certificate pipeline (Phase 3 **U1–U4**) all live + live-smoked, **+ a Phase 4 hardening pass** over the QC surface. Migrations 0017–0027 applied. |

**Standing rule (owner, non-negotiable):** every upgrade deploys to **wwf_mass
only**; production is promoted **solely** after the owner's own tests +
**explicit approval**. This document never proposes a prod deploy without that
gate.

**Governance boundary (`docs/SCOPE.md`, "one roof two zones"):** the Operations
zone (tasks, weekly reports, facility, analytics) is **non-GMP / informational**;
the QMS Studio + QC zones are where **GMP records** live, on their own
service/lifecycle. This boundary is structural and must survive every merge.

---

## 3. Asset inventory & overlap analysis *(the analytical core)*

Every source now in hand, classified by domain and by what it uniquely
contributes vs what it duplicates:

| Asset | What it is | Domain | Unique value | Overlaps / verdict |
|---|---|---|---|---|
| **WWF/GrowFlow** (this repo) | Live ops + weekly-reporting PWA | Foundation + Operations | The spine: auth, RLS, audit, roles, PWA, notifications | — (base) |
| **pp-document-suite v1.7.0** | House-style bilingual .docx engine | Document generation | The canonical formatting core (navy #2B547E, 6pt floor, `pp_verify` PASS gate) | Vendored into `docengine/` (**done**) |
| **Cannabis-EU-GMP-QMS-Creator** → `qms-creator/` | Questionnaire-driven SOP/annex authoring + 13 Letta agent personas | QMS authoring | The Mode-A workflow shape (questionnaire → section agents → regulatory check) | Instruction texts superseded by the DocEngine canon; **workflow shape kept** (**done, in DocEngine pipeline**) |
| **ACME_SOP** | Engine lineage + `build_from_md.py`/`[[FORM:grid]]` | Document generation | The Jul-14 `fixed()` layout brain + grid adapter | Folded into DocEngine canon (**done**) |
| **QC_LIMS_Ao** → `qc-lims-ao/` | React+FastAPI QC LIMS prototype | **QC LIMS** | Richest QC domain model: samples, specs, CoA, OOS, CAPA, stability, transport, water, Annex-11 audit, barcode | **Primary source for the QC LIMS module.** Its TMS-lifecycle bits feed the TMS. |
| **QC_LIMS_APP** | RSA sampling form + GMP-QC HTML + roadmap | QC LIMS (sampling) | Sampling process detail (QC RSA form) | Merges into QC LIMS module — sampling sub-domain |
| **QC_APP** | LIMS README stub | QC LIMS | (near-empty) | Placeholder — folds into QC LIMS module |
| **cannabis-sample-tracker-89871** | Lovable React sample-tracker SPA | QC LIMS (samples) | A sample-tracking UI reference | UI ideas for QC LIMS sample views; not a separate app |
| **CoA_TRACK** | React+FastAPI+Letta CoA management (v3.0.0, "production") | **Certificates** | CoA ingestion (Drive), AI PDF extraction, Annex-11 controls, 9 routers/services | **Merges into the unified certificate pipeline** — do NOT stand up separately |
| **COQ_GEN** | eCOA→Certificate-of-Quality generation engine (design-first) | **Certificates** | The COQ release-certificate generation rules + OCR/visual-parse ingestion | **Same pipeline as CoA_TRACK + DocEngine** — reconcile, don't triplicate |

### The central finding

The nine assets reduce to **four capability layers**, not nine products:

```
┌─────────────────────────────────────────────────────────────┐
│  SHARED SPINE  (exists)                                       │
│  auth · RLS · hash-chained audit · roles · PWA · Letta fleet │
├───────────────┬───────────────┬─────────────────────────────┤
│  DocEngine    │  Notifications│  (cross-cutting services)    │
│  (done)       │  (v1 done)    │                              │
├───────────────┴───────────────┴─────────────────────────────┤
│  DOMAIN MODULES  (on the spine, sharing the services above)  │
│  1. TMS (priority #1)                                        │
│  2. QC LIMS      ← qc-lims-ao + QC_LIMS_APP + QC_APP + tracker│
│  3. Certificates ← CoA_TRACK + COQ_GEN + QC-LIMS CoA parts    │
│     └─ ONE extract→verify→generate pipeline on the DocEngine │
└─────────────────────────────────────────────────────────────┘
```

**Design consequence:** the certificate pipeline (CoA in, COQ out) is built
**once**, on the DocEngine's formatting core and Letta fleet, consumed by both
the QC LIMS module (per-batch CoA/COQ) and any standalone certificate view.
Building CoA_TRACK and COQ_GEN as separate services would duplicate ingestion,
extraction, verification, and rendering that the DocEngine already centralizes.

---

## 4. Target architecture — the unified spine

- **Data:** two-DB split retained. New domains get their **own schema** inside
  `wwf_tasks` (e.g. `docengine`, later `qc_lims`, `certs`) or a dedicated DB per
  the Phase-2 plan — never a parallel Postgres cluster. Every table carries
  org-isolation RLS + the hash-chained audit trigger (the `id`-surrogate-PK rule
  learned in T1: the shared audit trigger records `NEW.id`).
- **Services (shared, internal-only, fronted by the WWF backend's authed
  proxy):** DocEngine (all document/certificate generation), the Letta `gf_*`
  fleet (additive — existing ~54 agents never blind-flipped), Notifications,
  Audit, Gotenberg (DOCX→PDF).
- **UI:** one bilingual PWA; zones surfaced as nav groups (Operations · QMS
  Studio · QC LIMS · Certificates), each role-gated. Same shell, same SW, same
  URL.
- **AI:** one Letta server; every module's agents namespaced `gf_*`; the
  DocEngine's fleet pattern (Postgres-backed jobs, additive ensure-loop) is the
  template for all future agent work.

---

## 5. Method — the structured, repeatable approach

Every module follows the **same disciplined loop** (proven on DocEngine + TMS T1):

1. **Delta-first analysis.** Before writing code, diff the imported prototype
   against what the platform already has (T1's Explore-agent delta report is the
   template). **Never rebuild what exists.** Build only the genuine gap.
2. **Additive migrations + schema lockstep.** New tables/columns only; regenerate
   `schema.tasks.sql` from alembic-head via pg_dump; the CI drift gate enforces
   lockstep; every migration must downgrade cleanly.
3. **GxP guardrails, always on.** Never fabricate pharmaceutical data — unknown
   values stay blank for a human. Controlled documents ship only on
   `pp_verify → RESULT: PASS`. Every GMP record is audited and RLS-scoped.
4. **Test-first, offline where possible.** pytest for backend, node --check +
   Playwright for frontend, faked-Letta client for pipeline logic. Full local
   gate before any deploy.
5. **wwf_mass only → live smoke → owner approval → prod.** Live verification on
   the test stack (real Letta, real DB, tt.* accounts) before the owner-gated
   promotion. Prod is never touched autonomously.
6. **Adversarial verification for correctness-critical work** (canon decisions,
   regulatory checks, cycle guards).

---

## 6. Sequenced roadmap (dependency-ordered)

### Phase 0 — DocEngine ✅ *(complete, on test)*
Dedicated Letta doc-AI service; pp-document-suite adopted completely;
questionnaire→SOP/annex pipeline; hard PASS gate; deployed + live-verified on
wwf_mass. Remaining: owner acceptance → prod.

### Phase 1 — Task-Management System (priority #1) ✅ *(complete on wwf_mass)*
The owner's explicit #1-to-production. All four increments built, tested,
deployed, and live-verified against real auth + real data on wwf_mass
(backend v44 / frontend v66 / migration 0017):
- **T1** — node-kind task tree, dependency graph with a cycle guard, and the
  pre-existing `handoffs` table surfaced as a full propose/accept lifecycle.
- **T2** — in-app "what did my team do" digest + a real stale-regex bug fix
  in the notifications inbox filter. Emailed digests / quiet-hours push
  explicitly deferred (no SMTP/push channel exists — see
  docs/RESEARCH-NOTIFICATIONS-2026-07.md's own v2 path); building either now
  would be unenforceable dead code.
- **T3** — AI-native planning reusing the existing data-driven agent catalog
  (`app/api/ai.py`): `workload_balance` + `next_week_plan` catalog entries,
  and `dependency_advisor` scoped to a single task's family.
- **T4** — full gate: 298/298 backend tests, zero schema drift, DEPLOY.md
  promotion checklist.
**Exit:** awaiting the owner's tests + explicit approval to promote to prod
(`docs/DEPLOY.md` "Task-Management System v2" section has the exact steps).

### Phase 2 — QC LIMS module ✅ *(U1–U6 on wwf_mass, 2026-07-16)*
Assimilate the QC-domain corpus (`qc-lims-ao` primary + `QC_LIMS_APP` +
`QC_APP` + `cannabis-sample-tracker`) into ONE native module: sample lifecycle
(sample→test→result→OOS→CoA→release), specifications, sampling requests, custody,
Annex-11 audit. Regulatory authority where prototype and SOPs disagree =
**approved QCSOP 001–024** (Drive `1oPEIlNTWMutZIineO6Pb…`).
**Depends on:** DocEngine (controlled forms/CoA), TMS (lifecycle patterns).

Six units built, tested, and deployed to wwf_mass (migrations 0018–0026) —
see `docs/DEPLOY.md`'s "QC LIMS module" section for the full breakdown:
- **U1** specifications (0018), **U2** samples + lifecycle/genealogy (0019),
  **U3** CoA + test results with the auto-quarantine hook (0020),
- **U4** OOS investigations + CAPA (0021),
- **U5** custody cluster — sampling requests (RQS, 24h window) + field records
  (SFR) + chain of custody (0025),
- **U6** the three standalone JSONB leaves — `qc_water_tests` /
  `qc_stability_studies` / `qc_sample_transports` (0026), no cross-dependencies.

The QC-LIMS domain rebuild is now feature-complete against the `qc-lims-ao`
prototype. Prod promotion is owner-gated, pending explicit approval.

### Phase 3 — Certificate pipeline (CoA in → COQ out) ✅ *(complete on wwf_mass, 2026-07-16)*
`CoA_TRACK` + `COQ_GEN` + the QC-LIMS CoA parts reconciled into **one**
extract→verify→generate pipeline on the DocEngine core — built once, **not** two
separate services. Four units (migrations 0022–0024, 0027):
- **U1 — COQ out** (0022): `POST /qc/certificates/{id}/coq` renders a RELEASED
  certificate to a PASS-gated bilingual `.docx` Certificate of Quality via the
  DocEngine; QP-gated + a GxP data gate (every result must comply).
- **U2 — CoA in** (0023): register an incoming supplier/contract-lab CoA,
  transcribe + server-grade its fields against the spec, discover unknown labels
  in an adaptive review queue (map-once → auto-map), promote into a DRAFT ECOA
  certificate + results carrying source provenance.
- **U3 — verify loop** (0024): reconcile a promoted certificate against its
  source eCoA; auditable `qc_coa_verifications` record (VERIFIED/DISCREPANCY).
- **U4 — retrieval Q&A** (0027): `qc_coa_chunks` (Postgres FTS `tsvector` + GIN)
  with `POST /coa-qa` returning **cited** passages as a grounded answer — an
  app-local, records-zone retrieval over ingested CoAs that never fabricates a
  synthesis (no match → `grounded=false`, empty answer). Free-form document
  authoring still belongs to the DocEngine's Letta fleet.
Full flow live-verified end-to-end.

### Phase 4 — Cross-cutting hardening + production cutover — IN PROGRESS (owner-gated cutover)
A first **hardening pass over the QC + certificate surface is done on wwf_mass**
(backend v53 / frontend v74, 2026-07-16): an adversarial backend + frontend
review (authz, SQL-injection, transaction atomicity, jsonb/date, enum guards,
second-person review all verified clean) plus a batch of fixes closing a
write-side FK-validation class (unknown/cross-org ids now 422 instead of a raw
500 / dangling reference), a `generate_coq` TOCTOU re-assert, batch-size caps,
and frontend robustness (null-guarded transport forms, displayed water
parameters, escaped retrieval numerics). Nav coherence was verified (all seven
QC views register uniquely under the QMS-Studio group — no defect). See
`docs/DEPLOY.md` → "Phase 4 hardening". Nav coherence was verified (all seven
QC views register uniquely under the QMS-Studio group — no defect).

**✅ Production cutover DONE (2026-07-16):** on the owner's explicit go, the full
validated stack was promoted to `wwf_app` (the live 25-user system) — backend
`v53` / frontend `v74` / migrations 0017–0027 (additive; existing data intact) +
the `growflow-docengine` container. Backup-first, live-smoked (existing task
flows + new QC + DocEngine all green). See `docs/DEPLOY.md` → "Production
cutover".

**✅ qms-api retired + Letta sprawl resolved (2026-07-16):** the low-value,
internally-inconsistent Phase-1 `qms-api` registry was **formally retired**
(owner chose the lighter path over re-implementing it) — removed from wwf_mass
(`QMS_API_KEY` blanked, container dropped); the registry/knowledge tabs now show
an honest "retired — use Document Studio" panel (frontend v75). DocEngine Studio
is the sole live QMS surface. Retiring it removed the source of the `GMP *`
Letta-agent duplication; after a `letta` DB snapshot, the **45 orphaned `GMP *`
agents were deleted (107 → 62)**. See `docs/DEPLOY.md` → "qms-api … retired" and
`docs/LETTA-OPS-BACKLOG.md`.

**Letta ops backlog — all items now triaged (2026-07-16, `docs/LETTA-OPS-BACKLOG.md`):**
agent sprawl ✅ resolved (107→62); PQ1 re-embed ✅ no-action (isolated on a
single-source agent — no dimension conflict); provider-enum normalization ✅
no-action (heterogeneous but all-functional, creation friction already resolved);
0.16→0.17 upgrade ⏸ hold (no driver; prod DocEngine + scheduler depend on this
shared server); master-key rotation ⏸ hold (no compromise trigger; 5-consumer
coordinated swap touching prod). Nothing here warrants execution now.

**SUMA/ISO17verSUMA corpus assimilated (2026-07-16).** The 3 owner repo variants
(`WEEKLY_SUMA_ISO17_v2` canonical / `suma-platform` history / `01_TASKMASTA_ISO17025`
legacy) were deep-analysed. Finding: **SUMA is the ancestor of WWF/GrowFlow**
(`docs/SPEC.md` = "WWF / SUMA") — its task model, roles, workflow, ALCOA+ audit,
and exec dashboard are already surpassed by the platform. The one genuinely-absent,
SUMA-defining delta — the executive **GMP audit-prep readiness** tracker — was
assimilated natively as a **pure read layer over `tasks.tags`** (`GET /reports/
audit-prep` + the bilingual "Audit readiness" view; no migration). Kept a *planning
aid*, not a controlled record (two-zone scope). Cosmetic SUMA schema (e-sigs, report
versioning) dropped — superseded by the DocEngine. Deferred follow-on: activating
the inert `tasks.workflow_state` into a manager submit→approve/reject sign-off + QP-
remark block (a migration-bearing, GxP-scope-sensitive increment). See
`docs/DEPLOY.md` → "SUMA assimilation".

---

## 7. Risk register & open decisions

| Risk / decision | Impact | Mitigation / needs owner input |
|---|---|---|
| **Duplication across imported repos** | Wasted effort, divergent CoA data | The §3 consolidation (one certificate pipeline) is mandatory, not optional |
| **Live prod stability (25 users)** | A bad migration hurts real work | Test-first + owner-gated prod is the hard rule; additive-only migrations |
| **Letta ops fragility** (Rust-bridge decode bug, provider-enum unwritable, master-key rotation, PQ1 outlier) | Agent features can silently degrade | Use direct REST; additive `gf_*` only; backlog documented; back up pgvector before any Letta upgrade |
| **GxP scope creep** onto the ops zone | Regulatory exposure | The two-zone boundary in SCOPE.md stays structural (separate schema/lifecycle/labels) |
| **CoA/COQ regulatory correctness** | A wrong release certificate is a serious GMP event | Never fabricate; PASS-gate; cite real specs; QP sign-off in the workflow |
| **Owner decision — QC LIMS depth** | Determines Phase-2 size | Ask before Phase 2: full LIMS vs CoA-focused first cut |
| **Owner decision — validation posture** | Affects how formal the GMP lifecycle must be | Confirm before Phase 3 e-signature/lifecycle formality |

---

## 8. Immediate next actions (updated 2026-07-30)

Two of the three items this section carried on 2026-07-16 have since been
overtaken by events, and are corrected here rather than left to mislead.

1. **Owner acceptance on prod promotion — still the single biggest outstanding
   decision, but no longer the same decision.** The 2026-07-16 text said prod was
   at alembic `0016` with everything owner-gated and test-only. Several modules
   have since been promoted. **Version numbers are deliberately not repeated here
   any more** — `docs/DEPLOY.md` is the only place live image tags and migration
   heads are recorded, because a number duplicated across two documents is a
   number that will disagree with itself again. What remains true and unchanged:
   **production promotion requires explicit owner approval, every time.**
2. **The cultivation department** is the current development priority (owner
   direction, 2026-07-30) and has its own design record in
   `docs/CULTIVATION-DESIGN-2026-07.md` — identity/lifecycle, the HLVd
   decontamination campaign, the destruction/waste register, and now the
   harvest/yield record with the plant-protection intervals that gate a cut
   (§5f), with a requirement-by-requirement adherence table in §5c that lists
   what is **not** built as prominently as what is. Harvest is the piece that
   joined cultivation to the certificate chain: `qc_batch_genealogy` had carried
   a `relation='CULTIVATION'` slot since 2026-07-21 with nothing upstream
   producing the identifier for it. **The remaining Phase 2 record is
   irrigation/feeding**; Phase 3 (phase transitions generating per-phase task
   sets) has not been started.
3. **Phase 4 hardening** — nav-zone unify, retire the `qms-api` shell once the
   registry read-path fully moves to the DocEngine, a security/correctness pass
   over the QC + certificate surface, doc consolidation, the Letta ops backlog.
4. **Infra: CI is working; the 2026-07-16 note is obsolete.** That note said all
   jobs were dying in seconds at the workflow-startup level and needed an
   owner-side Actions-minutes check. The workflow now runs on a **self-hosted**
   runner (9 jobs) and completes normally — run 341 on this branch finished
   `success` on 2026-07-30. Two things worth knowing about it: the concurrency
   group is `cancel-in-progress`, so **pushing again cancels the run you were
   waiting on** (runs 338-340 are cancellations, not failures), and
   `deploy.yml` gates on CI being green and **fails closed** — no checks at all
   counts as failure, not as skippable.
5. Keep this document current as each phase lands — and prefer a pointer to the
   authoritative file over a copied value.

---

*Guardrails recap (never relax): never commit secrets; never fabricate
pharmaceutical data; ship controlled documents only on `RESULT: PASS`; deploy to
wwf_mass only, prod only on explicit owner approval; never blind-flip the live
Letta agents; back up the pgvector volume before any Letta upgrade.*
