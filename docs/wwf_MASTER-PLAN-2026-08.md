# Master Implementation Plan — 2026-08 (consolidated)

**This document supersedes the open-item lists of every earlier planning
document.** It was produced by reading all 34 docs in `docs/`, the 15
animation plans in `plans/`, the workflow files, and `ops/` — and verifying
**every** "planned / deferred / open" claim against the actual code, because
the planning corpus had drifted badly: of ~210 extracted claims, roughly a
third were already built (the docs just never got updated), a further set
were superseded by deliberate decisions, and the remainder are genuinely
open. Earlier docs stay valuable as *reasoning records*; for **what is still
to be done**, this file is the list. When an item ships, mark it here.

Verification baseline (2026-08-05): production backend `v85` / frontend
`v121`, tasks DB alembic `0054`, users DB `0009`, branch tip `c13fccf`.
Live tags and migration heads remain recorded **only** in `DEPLOY.md`.

---

## 1. What is already done (stop planning these)

Verified built and live — these still appear as "planned/deferred" in older
docs; treat those mentions as stale:

- TMS T5 workflow sign-off (`workflow_state` submit→approve/reject + QP
  block) — migration 0037, `tasks.py`, despite ROADMAP §6 "deferred".
- Cultivation Phase 2 (irrigation 0052) and Phase 3 (tasks↔batches +
  phase-transition task generation, 0054) — despite ROADMAP §8 "not started".
- Automated weekly snapshot (scheduler container, Thu 14:00 Skopje) —
  STATUS.md item 3.
- QC leaves (water/stability/transports, 0026), full QC LIMS (0018–0027),
  Annex-11 e-signatures in the QC zone, CoQ per-batch aggregation (C5),
  QCSOP-012 C1/C3/C6/C7/C8.
- Notifications v1 (inbox, activity feed, digest endpoint, due-soon scan,
  @mentions), bilingual event modeling.
- The entire MASS-WEED-IMPLEMENTATION-SPEC build sequence (chooser, af-modal
  create, notifications, subtask status, design-system CSS pass), the full
  UI-DESIGN-BRIEF surface set (depthome + dept fields + execreport +
  standalone report + board tree rows), the exclusive Mass Weed identity
  (33 legacy themes retired), full-screen Task Detail (v118) and the
  design's task-create page (v120).
- Dedicated Letta cutover, DocEngine canonical engine + gf_* fleet,
  Gotenberg PDF export, watchdog running as its own Docker stack.

## 2. Retired / obsolete (decided, don't re-open without a new driver)

- **React/TS/Vite migration & SUMA design system on React** — decided:
  vanilla-JS PWA shell is the architecture; Mass Weed is the design system.
- **Qdrant + VoyageAI RAG** — superseded by Letta RAG sources + Postgres
  FTS (`/coa-qa`) + DocEngine knowledge search. `qdrant_url` config default
  is dead and can be deleted on the next config touch.
- **35-skin design contract** — superseded by exclusive Mass Weed + hue
  schemes.
- **Nine named Letta agents scheme, self-service password reset, RS256
  JWTs, ops-zone e-signature metadata, wwf_core shared module, per-sample
  A/B/C grading, QP-as-CoQ-issuer, unification Phases 1–2 (federation /
  third DB)** — all superseded by shipped alternatives or explicit
  decisions recorded in DEPLOY.md.

---

## 3. TRACK A — Complete the Mass Weed theme at all app levels (priority)

The owner supplied a complete design system: **59 mockup pages** in
`design/mass-weed-mockup/`. Verified page-by-page against the app
(structural fidelity, not just `.mw-*` token usage — the v117 lesson):

**22 implemented · 19 partial · 4 not implemented · 16 have no backend
(owner decisions) — see §3.4.**

### 3.1 Phase MW-1 — close the 19 partial pages (frontend-only, no new backend)

Each gap below is buildable today against existing APIs. Grouped by size:

**Small (S) — 7 pages:**
| Page | Missing vs design |
|---|---|
| `audit.html` | ✅ **DONE (v123)** — free-text search over entity/actor; explicit "Verify chain" action + verdict strip; chip-style filters |
| `board.html` | kanban-column presentation of cultivation batches by phase; compact strain cards |
| `calendar.html` | ✅ **DONE (v123)** — "Upcoming" strip above the grid; dept-colour legend. (harvest/decon event types deferred — need new api.js bindings, not faked) |
| `execreport.html` | ✅ **DONE (v123)** — 4-KPI band parity (On-time % / Overdue / Logged hours / Complexity) from real document `metrics`. (large dept submission tiles: existing xr-sec sections cover this) |
| `intake.html` | ✅ **DONE (v123)** — two-column layout; char counter; dept accent bars. (source-quote attribution forward-compatible but dormant — backend emits no quote field; register item) |
| `workload.html` | ✅ **DONE (v123)** — 4-KPI band (Open/Overloaded/Available/Avg load); priority dots on chips; per-person capacity |
| `decrypt.html` | ⏸️ **PARKED** — porting `mw-menubtn`/`mw-decrypt` atom CSS that no app view consumes would be dead CSS; not built. Revisit if/when a view actually needs those atoms |

**Medium (M) — 12 pages:**
| Page | Missing vs design |
|---|---|
| `analytics.html` | ✅ **DONE (v124)** — additive yield-domain band from `GET /cultivation/harvests` (dry-flower KPI + WoW delta, yield-per-cycle, yield-by-strain, g/plant-by-room, output composition). g/W, cost/g, graded A/B/C deferred — no wattage/cost/grade field |
| `approvals.html` | ✅ **DONE (v125)** — unified pending/approved/rejected sign-off queue (.mwq-*) with live counts, folding in QC CoQ DRAFT/APPROVED/VOIDED + task acks + draft-doc locks. Additive (approvals-myday.spec.js contract preserved). Declined-ack history deferred (no backend list) |
| `dashboard.html` | ✅ **DONE (v124)** — KPI WoW deltas, real-notification alerts feed with ages, department pipeline lifecycle strip (real task status), resource HUD. QMS module lifecycle / HUD strain-batch-revenue deferred (no in-app field) |
| `coq-print.html` | ✅ **DONE (v126)** — on-screen A4 certificate preview (watermark, verdict header, identity grid, results, signatures) toggled before the .docx/PDF export, from real GET /qc/certificates/{id}. SHA/method/batch-size deferred (no field) |
| `doc-control.html` (L) | document lifecycle state machine (effective/in-review/periodic-review/superseded), review-by KPI, type tabs, detail drawer |
| `ecoa-intake.html` | ✅ **DONE (v125)** — display-only workbench (pipeline stepper, §6.3.1 review countdown, SHA-256 custody bar, promotion/verify gate notes) from real /qc/coa-documents/{id} fields |
| `facility.html` | ⚠️ **DEFERRED — needs contract-preserving rework.** A first redesign (floor plan + corridor + legend + kpiTile band + side panel) was reverted because it broke `web/e2e/tests/facility.spec.js`: that test (and the owner's stated flow) require the `.fac-room`/`.fr-nm`/`.fr-n`/`.fs-nm` room cells, the cell-click→`#fac-room-modal` add-batch flow, and the `.fac-res` phase-totals strip. The jsdom unit suite doesn't cover those selectors, so it must be re-done by LAYERING the floor-plan/legend on top of the existing markup without changing `.fac-room`/`.fac-res` or the room modal. Original still-live gap: floor-plan grid-areas layout + corridor + legend; per-room open tasks (no room↔task FK — backend-data need) |
| `leaves.html` | ✅ **DONE (v125)** — read-only stability drawer + timepoint pull-schedule timeline from real qc_stability_studies (schedule/started/status; CLOSED→done / elapsed→due / else pending). Per-timepoint analytical results deferred (no per-pull table) |
| `my-day.html` | ✅ **DONE (v124)** — greeting hero, visible ⌘K button wired to `GF.cmdk.open()`, 7-day task strip from state |
| `search.html` | ✅ **DONE (v126)** — new rail-reachable full-page grouped search (search-view.js), companion to ⌘K: views/tasks/people + rooms/batches when Facility is loaded. Documents deferred (no always-loaded index) |
| `team.html` | ✅ **DONE (v126)** — hex avatars + real completion-this-week & active-load stat bars. efficiency/shift/zone deferred (need worklog-derived metrics — part owner decision), rendered as an honest note |
| `ui-elements.html` | ⏸️ **PARKED** — an in-app design-atom gallery is dev/QA tooling with no cultivation-staff value; not built (adding a developer gallery to staff's nav isn't warranted). Build only if QA specifically wants an in-app atom reference |

### 3.2 Phase MW-2 — the 4 unbuilt pages with (mostly) existing backends

| Page | What it is | Backend status | Effort |
|---|---|---|---|
| `batch.html` | **Batch dossier** — hero, phase timeline, potency from released CoAs, custody/genealogy log, yield | All data exists (cultivation + harvest + qc_batch_genealogy + certificates) — pure frontend assembly | M |
| `harvest.html` | **Harvest scheduler** — cycle Gantt, predicted harvest dates, est. yields | Derivable from batches (phase + phase_since) + assumed phase durations; prediction model is a small backend addition | L |
| `reports.html` | **Report builder** — pick type/range/sections | Production/Crew types buildable on tasks/sessions/harvest; inventory-valuation + revenue KPIs have no backend (trim scope or owner decision) | L |
| `sop.html` | **SOP step-execution library** | Needs an SOP content model with steps (documents + tasks exist as substrate) — part owner data decision | L |

### 3.3 Sequencing for Track A

1. MW-1 smalls in one batch (one deploy) → 2. MW-1 mediums in 2–3 batches,
   `dashboard` + `facility` + `analytics` first (most-seen screens) →
3. MW-2 `batch.html` dossier (highest leverage: it unblocks `board.html`'s
   card click-through too) → 4. remaining MW-2 by owner priority.

Every batch follows the standing rule: CI green → snapshot → deploy →
verify → record in DEPLOY.md.

### 3.4 Owner-decision register for the 16 no-backend pages

These design pages cover product areas with **no backend at all**. Each
needs a decision: build the domain, park it, or drop the page. Do not treat
them as frontend gaps:

`orders.html` + `order-detail.html` (sales/order management) ·
`packaging.html` · `genetics.html` (breeding/strain registry) ·
`nutrients.html` (recipes) · `environment.html` (sensor telemetry) ·
`cure.html` (curing room mgmt beyond harvest lots) · `automations.html` +
`rule-builder.html` (automation.py is deliberately a fixed 2-rule set) ·
`settings.html` (unified console vs today's scattered controls) ·
`compliance.html` (METRC-style state reporting) · `capa-detail.html` +
`chg-detail.html` (standalone CAPA/change-control record types; CAPA today
lives inside OOS) · `knowledge.html` + `modules.html` (retired stubs) ·
`index.html` (inventory).

---

## 4. TRACK B — Animation & interaction quality (already specced)

`plans/001–015` are complete, self-contained implementation plans (written
2026-08-05, commit-stamped `6bd1f7d`). Execution order and the two known
cross-plan interactions are in `plans/README.md`. Recommended: land 006 →
002 → 001 → 013 (one sitting) → 003/004/007/010/009/008 → rest. Track A
work will touch some of the same files — whoever does MW-1 should check
`plans/README.md` first to avoid churn.

## 5. TRACK C — Product backlog (verified open, deduplicated)

Each item lists its *consolidated* sources — the same task appeared in up
to 5 documents:

| Item | Sources (consolidated) | Effort |
|---|---|---|
| **Email/SMTP channel + digests + quiet-hours push (VAPID) + per-user toggles + setAppBadge** — one notifications-v2 bundle | ROADMAP T2 · REVISION-PLAN P1 · RESEARCH-NOTIFICATIONS v2 · DEPLOY TMS-v2 · notifications.py's own comment | L |
| **File attachments on tasks** (links exist; uploads don't) | STATUS #4 · ARCH-REVIEW §8 | M |
| **Task tree-board UI** over existing `GET /tasks/tree` (backend done, binding unused) | DEPLOY round-2 audit | M |
| **Task status-lifecycle transition map** (statuses cycle freely) | RESEARCH-LANDSCAPE R5 | M |
| **Pagination defaults on list endpoints** (`/tasks` unbounded) | APP-REVIEW P1-8 | M |
| **`department_id` as sole key** (drop text label) | APP-REVIEW-14 M6 | M |
| **`report_windows` table** (Fri→Thu vs ISO weeks) | ARCH-REVIEW §6.1 | M |
| **Viewer (read-only) role** for auditors | AUDIT-TRIAGE §4 | M |
| **Training matrix** (role × SOP join + view) | UNIFICATION §3/§6 | M |
| **SOP-aware automations** (validate `reference_code` against registry; superseded-SOP notify) | UNIFICATION §7 | M |
| **qc_batches master table** (QC batch_id is free text; join to plant_batches) | APP-REVIEW §5.3 | M |
| **Capture-import batching** (per-task txn + dedup in loop) | CODE-REVIEW-28 | M |
| **Barcode/QR sample workflow** (claimed adopted, never built) | ADOPTED-FEATURES §2.5 | M |
| **Checklist subtasks; AI tone selector; parent auto-complete option** — small task-UX cluster | SPEC · REVISION-PLAN P3 · RESEARCH refuted-claim | S each |
| Small QC/GxP closes: eCoA filler≠decider check · RQS role-drift UI hide · Ph.Eur 3028 order guard · qcOosPick retry pattern · C5 legacy-render cutover (owner) · structured iCoA HoQC checklist | CODE-REVIEW-24/-DEEP · QCSOP-012 §3/#4 · DEPLOY round-3 | S each |
| Small backend closes: audit keyset tiebreaker · dependency-cycle lock · report uuid guards · bcrypt/WeasyPrint off event loop · Letta binding registry check · structured outputs vs regex JSON | CODE-REVIEW-DEEP M3/M7 · APP-REVIEW · DEPLOY round-3 · ARCH-REVIEW §4.2 | S each |

## 6. TRACK D — Security & hardening (verified open)

| Item | Sources | Effort |
|---|---|---|
| MFA (TOTP) for signing/elevated roles — AUDIT-TRIAGE's own trigger ("before GxP-lite") has arguably fired | APP-REVIEW P2-13 · AUDIT-TRIAGE · ARCH-REVIEW §2.5 | M |
| Audit-chain external anchoring (HMAC key outside app role) | APP-REVIEW P2-13 · APP-REVIEW-14 M5 | M |
| e-sig hard precondition on APPROVED/RELEASED transitions (endpoint exists; not enforced as gate) | APP-REVIEW F-5 | M |
| Drop CSP `unsafe-inline` (refactor inline handlers — big, ties into Track F modernization) | APP-REVIEW §2 | L |
| Quick wins: `server_tokens off` · HSTS `includeSubDomains` · self-host Google Fonts · `/audit/verify` for QA + `created_at` index · tighten `profiles_self` RLS · AI endpoint throttle · shared `GF.reasonDialog` replacing `prompt()` · non-GMP banner on locked doc view | APP-REVIEW · APP-REVIEW-14 L6/L7/M7 | S each |
| Part-11 e-signature layer (only if GxP posture formalizes — pairs with validation-file execution) | DEPLOY | XL |

## 7. TRACK E — Ops / infra (verified open)

| Item | Sources | Effort |
|---|---|---|
| **Watchdog alert channel** (`WWF_WATCHDOG_WEBHOOK` + GH token for ci-freshness) — the monitor runs but only logs | DEPLOY 2026-08-05 · ops/README · APP-REVIEW F-4 | S |
| **Re-register runner with `--disableupdate`** (the 5-day-outage cause, still unfixed) | ci.yml header · ops/README | S |
| **Disk pressure on `/opt` (97%)** — image retention pruning, owner-gated; 2026-08-05's 100% incident crashed the runner mid-CI | DEPLOY · this session | S |
| Move CI runner off the production host | APP-REVIEW F-7 | M |
| kvm4-runner hardening (token rotation, network restriction, persistent audit log) | ARCH-REVIEW §5.1 · AUDIT-TRIAGE | M |
| CI additions: coverage gate · ruff/mypy + eslint/node--check · image CVE + secret scanning · fn_audit_row throughput benchmark in rehearsal | CODE-REVIEW-DEEP · APP-REVIEW · APP-REVIEW-14 L8 · CULTIVATION §3 | S each |
| Letta Postgres + Qdrant backup coverage (outside WWF backup scope today) | BACKUP.md §Scope | M |
| Redis-backed rate limiter (only when multi-replica) · internal TLS (accepted risk) · load testing | AUDIT-TRIAGE §4 | M |
| Host-rebuild runbook + RTO/RPO statement (restore drill is automated nightly; the *runbook* is the residue) | APP-REVIEW F-8 | M |
| Owner-side ops: re-seed room register post-wipe (script ready) · re-populate production · rclone OAuth client ownership · archive qms-creator/ + orphaned QMS volumes · delete frozen shared-Letta agents | CULTIVATION §5c · DEPLOY | S each |

## 8. TRACK F — Deliberately deferred / on hold (documented, not forgotten)

- **ESM/modernization** (FRONTEND-ESM steps 1–4, Vite/TS, module system,
  monkey-patch retirement): proposal explicitly "not accepted"; Step 0
  (test pinning) is effectively done (21 frontend suites). Re-open only
  with a concrete driver; CSP-inline work (Track D) would be the natural
  co-trigger.
- **Letta 0.17 upgrade + master-key rotation**: HOLD per LETTA-OPS-BACKLOG
  (no driver; touches prod backend+docengine+scheduler simultaneously).
- **OCR/eCoA extraction pipeline (XL)** + **air-gapped/local AI decision**:
  blocked on one owner decision (URS D5) — run local models or amend the
  URS. Until then eCoA stays human-transcription (which validates fine).
- **Offline write-sync/queue-replay** (RESEARCH R4): revisit if facility
  connectivity becomes a real complaint.
- **Doc consolidation**: this file *is* phase 1. Phase 2 (marking stale
  sections in the old docs with pointers here) is an S follow-up.

## 9. Owner-decision register (complete)

Decisions only the owner can make, consolidated from every doc:

1. The 16 no-backend design pages (§3.4) — build/park/drop, each.
2. Per-plant identity: all phases or from flower entry only (CULTIVATION §6).
3. Mother-plant indefinite tracking (CULTIVATION §6).
4. Additional record types: drying-room environmentals, pruning/training logs.
5. C5 cutover: retire the legacy single-cert CoQ render.
6. Air-gap posture (URS D5) → unblocks/kills the OCR pipeline.
7. Validation-file execution: sign URS/IQ/OQ/PQ (with QA) — app-side basis
   is ready.
8. QA signature on the Rooms 1-6 ↔ C180-C185 mapping (controlled document).
9. GxP posture formalization (SCOPE.md three-zone rewrite + MFA + Part-11
   layer as a bundle).
10. Production re-population timing (post-wipe).
11. `/opt` image pruning; orphaned QMS volume archive-then-delete.
12. Ambient brand motion (plans/005 scope note): keep or tame the wordmark
    loops beyond the storm/rave removal.
13. **eCoA §6.3.2 filler≠decider** (attempted 2026-08-05, then reverted): does
    the eCoA review require a *distinct* second person to decide the checklist,
    or may the Head of QC review a checklist they filled? Implementing the
    distinct-person control broke 12 existing single-actor eCoA tests — i.e. the
    established, tested behavior is single-actor — and shipping it would block
    the lab's real workflow if one QC person legitimately does both. Held for an
    owner/SOP decision; if distinct-person is required, it lands with the
    matching test updates (the reverted diff and its test are recoverable from
    git history at the animation/hardening commit's parent).
14. **`facility.html` floor-plan — needs backend data + a CSS untangle**
    (investigated 2026-08-05; a first agent redesign was reverted for breaking
    `web/e2e/tests/facility.spec.js`). Two blockers, both owner/dev decisions:
    (a) **Room layout coordinates.** A faithful floor-plan (the mockup's
    `.fac-stage` with absolutely-positioned rooms + a corridor) needs per-room
    x/y/w/h positions. `GET /facility` returns none — rooms have only
    kind/plant counts/batches. Either add a `layout` field per room (owner
    decides the physical map) or accept the current card-grid (which is what
    ships today) instead of a true floor-plan.
    (b) **A pre-existing `.fac-room` CSS conflict.** `.fac-room` is defined in
    app.css (`display:flex` card), views.css:235 (`position:absolute`
    floor-plan variant — **wins** by load order), and mass-weed.css (clip-path
    only). A full floor-plan+side-panel CSS (`.fac-wrap`/`.fac-stage`/
    `.fac-panel`/`.fac-chip`) already sits UNUSED in views.css from an earlier
    pass. The live card view renders acceptably and passes e2e, but the leaked
    `position:absolute` rule is latent cruft; wiring the real floor-plan means
    reconciling all three files. That touches shared CSS behind the working
    production view, so it is deliberately NOT done as an autonomous change —
    it wants a focused, owner-reviewed facility pass, not a page-batch agent.
    Contract to preserve either way: `.fac-room .fr-nm`/`.fr-n`/`.fs-nm` cells,
    cell-click→`#fac-room-modal`, and the `.fac-res` phase-totals strip
    (`facility.spec.js`).

## 10. Recommended sequence (next 4–6 working sessions)

1. **Session 1**: Track E quick wins (watchdog webhook, runner
   `--disableupdate`, nginx/HSTS/fonts, audit-verify QA+index) + Track C
   S-item sweep (round-3 LOWs, audit tiebreaker, dependency lock, report uuid
   guards). One deploy. *(Shipped 2026-08-05 as backend v86 — see DEPLOY.md;
   eCoA filler≠decider deferred, see decision register #13.)*
2. **Session 2**: MW-1 smalls (7 pages) + animation plans 006/002/001/013.
   One deploy.
3. **Session 3–4**: MW-1 mediums (dashboard, facility, analytics first).
4. **Session 5**: MW-2 batch dossier + board kanban click-through.
5. **Session 6**: notifications-v2 bundle (needs owner SMTP creds) or next
   MW-2 page, per owner priority.
6. Standing: put the §9 register in front of the owner; each answer
   unblocks its track.
