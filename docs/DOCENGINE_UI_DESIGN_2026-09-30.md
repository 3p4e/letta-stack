# DocEngine Studio — Advanced UI Design & Platform Architecture

- **Date:** 2026-09-30
- **Author:** Agent Zero (analysis of `letta-stack` @ `96fdd163`, branch `agent-zero/workspace`)
- **Status:** Design proposal (not yet reviewed by owner)
- **Scope:** A from-scratch, advanced user interface for the Purely Plant DocEngine, plus the
  platform architecture that lets the same capability be exposed as an **MCP server** and as a
  **pluggable component** to external platforms later. Includes a feasibility analysis of a
  dual retrieval system (RAGFlow vs Letta) and a full model-to-function mapping (Moonshot vs DeepSeek).
- **Sources:** `START_HERE.md`, `README.md`, `CLAUDE.md`, `docs/wwf_*` canon/roadmap/master-plan/
  dedicated-plan/unification, `docs/HANDOVER_PP_DocEngine_Letta.md`, `docs/ENGINE_CONSOLIDATION_2026-08-29.md`,
  `review/OPEN_DECISIONS_2026-08-29.md`, `review/APP_SECURITY_REVIEW_2026-08-29.md`, `server/runbooks/*`,
  `pp-document-suite/**`, `apps/wwf-docengine/**`, `apps/ppdocwiz/**`, `ingestion/ragflow/**`.

---

## 0. Executive summary

Purely Plant's platform is a single EU-GMP operations + quality system ("One platform. One login.
One URL.") built on the mature GrowFlow (WWF) vanilla-JS PWA. The **DocEngine** is the capability at
its center: it turns a questionnaire into an approved, bilingual (MK/EN), house-styled controlled
`.docx`, and it drives the certificate pipeline (CoA in → CoQ out).

This document designs **DocEngine Studio** — a role-gated zone of the existing GrowFlow PWA — from
scratch, against the real pipeline (no simulated progress, no client-side document codes, no
fabricated values). It then specifies the architecture that keeps the engine private behind one
authed backend while exposing the same capability over **MCP** and to **external platforms** through
a versioned, capability-scoped API and an embeddable web component.

Two architectural questions raised by the owner are answered inside:

1. **Dual-system RAG** — RAGFlow as the *evidence/official* retrieval lane, Letta as the *general
   assistance* lane: **feasible and recommended**, with hard lane-routing and a no-silent-fallback
   rule. (§7)
2. **Multi-model mapping** — every AI function bound to either the **Moonshot ALEGRETTO
   subscription API** or the **DeepSeek API**, with per-function technical justification. (§8)

---

## 1. Repository analysis

### 1.1 What the platform is

Purely Plant GmbH is a Macedonian EU-GMP medical-cannabis facility. The repository `letta-stack`
is the dedicated, self-contained home of **all Letta technology** for that platform (owner decision
2026-08-09), consolidating work previously spread across 35 GitHub repositories.

The governing product string, repeated across the roadmap documents, is
**"One platform. One login. One URL. One data spine."** Everything is absorbed into the live
GrowFlow foundation by **strangler-fig** replacement — "never a second app, never a forked stack,
always the same containers so executives keep the same links." Two halves are being unified:

- **QMS Creator** authors the *controlled world*: SOPs, forms, RACI, training, regulatory knowledge.
- **GrowFlow / WWF** runs the *operational world*: tasks, sessions, weekly locked records,
  notifications, analytics.

The platform foundation is already in production: FastAPI over two Postgres databases, row-level
security, hash-chained tamper-evident audit triggers, a **13-role model**, and a **bilingual MK/EN
vanilla-JS PWA** with ~25 real users.

### 1.2 The DocEngine (what the UI exists to drive)

A dedicated Letta-powered document-generation capability. It adopts the production
`pp-document-suite` formatting engine and merges the questionnaire → SOP/annex authoring workflow.
Its non-negotiable contract, stated in the canon:

- **Never fabricate pharmaceutical data.** If a value is not in the source, the field stays blank
  for a human to fill — never guessed.
- A document is shipped only when `pp_verify.py` prints **`RESULT: PASS`**.
- The DocEngine **never returns a document on FAIL** (Line B deletes the artifact; Line A streams
  422 but leaves the file on disk — a quirk the UI must not expose).

Three modes define the engine's behavior:

| Mode | Meaning |
|---|---|
| **A** | Develop content from scratch via questionnaire (multi-round, pre-populated, most-compliant defaults) → approval gate → Mode B. |
| **B** | Format approved content into a controlled `.docx`. |
| **C** | Restyle already-drafted text into house style (content-preserving). |

### 1.3 Two engine lines

**Line A — `pp-document-suite/` (repo root).** The engine the live Letta stack actually runs
(hash-verified against the live volume). Consumers: the live Letta tools `build_pp_document` /
`fetch_pp_document` (attached to `qms_docx_formatter`, `pharma_docx_formatter`, five `pp_annex_*`
agents), ~7 deliverable builders, and the `ppdocwiz` app. Uniquely carries the **glyph guard**
(`pp_assets.py`: `missing_glyphs()`, `audit_docx()`) — the fix for a real incident where subset
Carlito webfonts scrambled Macedonian Cyrillic into tofu. Has an open, unauthenticated FastAPI
service (`integrations/service.py`, port 8600) and a separate live REST front (`qms-api`, :8500).

**Line B — `apps/wwf-docengine/` ("GrowFlow DocEngine").** A dedicated internal-only FastAPI service
(port 8000, `X-API-Key`, no published ports). It vendors a *canonical merged* copy of the engine and
adds: **questionnaire banks**, a declarative **`gf_*` Letta agent fleet**, a **Postgres-backed job
pipeline**, and a **document registry** (`docengine.jobs`, `docengine.documents`). It re-implements
the build contract natively (direct Letta REST, not the MCP bridge) and publishes a document
atomically only after PASS. Its sole intended caller is the GrowFlow backend's `/qms` proxy.

**Consolidation status (2026-08-29):** a regression where commit `593e7f7` accidentally reverted the
content-aware `fixed()` table algorithm was found and surgically restored; root now carries **both**
contested capabilities (glyph guard *and* the restored `fixed()`), covered by
`pp-document-suite/tests/test_layout.py`. The bake-off between the lines is still the owner's call;
the working hypothesis is a merge, not a pick.

### 1.4 Existing front-ends

| Front-end | State | Notes |
|---|---|---|
| **GrowFlow PWA** (WWF product) | Live, ~25 users | The surviving UI shell. Vanilla JS, no build step, bilingual, PWA service worker, ⌘K palette, approvals/audit/dashboards. Its backend proxies `/qms` → DocEngine. Still points at the *old* Letta stack. |
| **`apps/wwf-docengine`** | Live (internal) | **API-only, no frontend.** Humans reach it only via the GrowFlow app. |
| **`apps/ppdocwiz`** | Built, **not deployed** | Standalone single-file SPA + FastAPI gateway embedding engine Line A. Two tabs (Wizard with raw-text micro-syntax editors, Chat with a Letta agent) + a lock screen. MVP scope; no registry, no persistence, no `[[FORM:grid]]`. |
| **`qms-api` (:8500)** | Live (legacy) | Older REST front; registry/knowledge tabs retired in favor of DocEngine Studio. |
| **RAGFlow UI**, **Letta ADE**, **`qc_register_artifact.html`** | Live/tools | Operational tooling, not the product UI. |

### 1.5 Topology and services (high level)

Single VPS (kvm4, Hostinger), **one nginx entry**, one FastAPI backend, one PWA. Stacks:
test `wwf_mass` → prod `wwf_app`, promoted only with explicit owner approval. Supporting services:

- **Letta server** (pinned **0.16.8**), `gf_*` fleet, `pp_house_rules` / `gf_house_rules` memory blocks.
- **DocEngine** (Line B) — internal :8000.
- **Gotenberg** :3000 in-stack — DOCX→PDF (`/forms/libreoffice/convert`).
- **RAGFlow** — the eCoA ingestion/retrieval pipeline (`ingestion/ragflow/**`), with an MCP surface.
- **LiteLLM** — provider configuration for the Letta fleet.
- **Two Postgres DBs** (`wwf_users`, `wwf_tasks`); new domains get their own schema inside `wwf_tasks`
  (e.g. `docengine`, `qc_lims`, `certs`) — never a parallel cluster; additive migrations only.
- **letta-mcp-rust :6507** — the existing MCP bridge; **unreliable** (reproduced decode bug
  `missing field 'package'`; truncation; false aggregates). Direct REST is the working path.

### 1.6 Binding constraints

**Tech-stack mandates (do not re-open):**

- **Vanilla-JS PWA shell is the architecture.** React/TS/Vite migration is **decided dead**; the
  imported React `qms-ui-v2` stays in-repo as reference until parity, then is archived.
- **"Mass Weed"** is the exclusive design system (33 legacy themes retired).
- Backend: FastAPI + Postgres + alembic. Documents: **python-docx** (legacy Node docx-js rejected).
- Modular monolith, deliberately: no micro-frontends / module federation at this scale.
- Frontend tests: `node --check` + Playwright e2e; backend pytest; a **faked-Letta client** for
  pipeline logic.

**GxP / regulatory constraints that shape UI behavior:**

- Unknown values render **blank for a human**; never fabricated.
- Documents ship only on `pp_verify → RESULT: PASS`; the engine never returns a FAILed document.
- **COS:** the COQ (Certificate of Quality) render has a GxP data gate + **QP sign-off**; CoA→CoQ
  intake is **human transcription** (OCR pipeline blocked on an owner decision / air-gap posture).
- Two-zone boundary is structural: **Operations** (non-GMP/informational) vs **QMS Studio + QC**
  (GMP records) — separate schema/lifecycle and an **explicit zone label in the UI**.
- House typography is binding for anything previewed or rendered: house navy **`#2B547E`**; palette
  label `#EDF2F7`, zebra `#F7FAFC`, pass `#E2EFDA`, fail `#FCE4D6`, caution `#FFF2CC`, gridline
  `#B0BEC5`; Calibri body / Arial Narrow annex headers; **6 pt font floor**; shading `clear`
  (never `solid`); gray `#E8E8E8` SOP section headers (never green); Cyrillic must render.
- Bilingual **Macedonian-first**: inline `MK | EN`, separator omitted when EN empty, **decimal
  commas** in Macedonian numbers, abbreviations untranslated.

**Security/posture constraints affecting the UI:** JWT auth + forced-password lifecycle, 13 roles,
row-level security with per-request identity GUCs, hash-chained audit triggers on every table,
"preserve authentication and CSRF protections", no external IdP at 25 users. Open hardening items
that bound design: MFA (TOTP) for signing/elevated roles; e-signature as a *hard precondition* on
APPROVED/RELEASED transitions (endpoint exists, not enforced); drop CSP `unsafe-inline`; HSTS
`includeSubDomains`; self-host Google Fonts; AI endpoint throttle. `service.py` (:8600) has **no auth**
and must never be exposed directly.

---

## 2. Requirements extracted from the repository

These are the owner/product requirements found **in the repository itself** — the "requests" the
design must satisfy.

### 2.1 Product / UX requirements

1. **One shell, nav groups, each role-gated:** *Operations · QMS Studio · QC LIMS · Certificates ·
   System* (surfaced under the existing GrowFlow shell, service worker and URL).
2. **DocEngine Studio is the sole live QMS surface.** The retired `qms-api` registry/knowledge tabs
   show an honest "retired — use Document Studio" panel. **Honest panels over mock data.**
3. **QMS Studio view order:** registry browser → knowledge search → training-matrix view →
   **authoring wizard**.
4. **The authoring wizard must be rebuilt honestly** against the real pipeline:
   *metadata → questionnaire → generation progress → QA review → DOCX*. The prior React wizard was
   "partially simulated — fake `setInterval` progress for two agents, client-side `Math.random()`
   document codes, silent mock fallbacks when AI calls fail." None of that is acceptable.
5. **Document controls:** `doc-control.html` — lifecycle state machine (effective / in-review /
   periodic-review / superseded), review-by KPI, type tabs, detail drawer.
6. **Certificate preview:** `coq-print.html` — on-screen **A4 certificate preview** (watermark,
   verdict header, identity grid, results, signatures) toggled **before** the `.docx`/PDF export.
7. **eCoA intake workbench:** `ecoa-intake.html` — display-only workbench with **pipeline stepper**,
   §6.3.1 review countdown, **SHA-256 custody bar**, promotion/verify-gate notes, from real
   `/qc/coa-documents/{id}` fields.
8. **SOP step-execution library:** `sop.html` — an SOP content model with steps (documents + tasks
   exist as substrate).
9. **Training matrix view:** role × SOP join; approval chain maps to QA_MGR → reviewer → QP.
10. **Adaptive review queue** for CoA ingestion: discover unknown labels → **map-once → auto-map** →
    promote into a DRAFT ECOA certificate + results carrying **source provenance**.
11. **Retrieval Q&A surface:** `POST /coa-qa` returns **cited** passages as a grounded answer; no
    match → `grounded=false`, empty answer — the UI must handle the honest no-answer state.
12. **Verify-loop UI:** reconciliation produces auditable `qc_coa_verifications` records with
    **VERIFIED / DISCREPANCY** verdicts.
13. **Unified approvals queue** (`approvals.html`): pending/approved/rejected sign-off, live counts,
    folding in QC CoQ DRAFT/APPROVED/VOIDED + task acks + draft-doc locks.
14. **Audit view** (`audit.html`): free-text search over entity/actor, explicit **"Verify chain"**
    action + verdict strip, chip-style filters — the hash-chained trail is user-inspectable.
15. **Role-differentiated AI:** `/ai/functions` **filters its catalog so each role's UI only offers
    what it may use**; `invoke()` 403s below tier. Personal tier (voice_capture, translate_bilingual,
    draft_description) for everyone; nine corpus/planning functions require elevated roles;
    org-wide grounding for executives/ADMIN/QP, department-scoped for dept managers.
16. **Authoring gates:** generation stays behind QMS_AUTHOR roles; binding administration stays ADMIN.
    Authoring = QP + QA_MGR (+ADMIN); reading = managers/execs.
17. **Settings → AI** admin screen: manages `ai_agent_bindings` (planner-agent rebinding after fleet
    recreation).
18. **Bilingual from day one** — the EN/MK translation catalog is complete; new QMS Studio views must
    consume it.
19. **Non-GMP banner on locked doc views**; the zone label is a hard requirement, not cosmetic.
20. **Existing shell features the new zone must live inside:** ⌘K command palette, grouped search,
    notifications inbox/activity feed, KPI dashboards, calendar, kanban, batch dossier, task
    tree-board, offline-capable PWA, file attachments (links today, uploads pending).
21. **Platform name stays GrowFlow** — no rebrand; QMS ships inside the existing deployment at the
    same URLs.

### 2.2 Integration requirements (MCP & external platforms)

1. **MCP must be a first-class exposure path** — but the existing `letta-mcp-rust` bridge is
   unreliable; the working integration is **direct REST**. Any MCP surface must therefore be a
   purpose-built adapter over the app backend's API, not a wrapper around that bridge.
2. **RAGFlow is the MCP-enabled ingestion surface** (`server/RAGFLOW_MCP_ENABLE.md`,
   `server/ragflow/docker-compose.override.yml`) — currently it **authenticates no client and is
   publicly routed** (accepted risk 2026-08-25), which must be fixed before external exposure.
3. **One backend fronts everything:** DocEngine, the Letta `gf_*` fleet, Notifications, Audit and
   Gotenberg are internal-only services "fronted by the WWF backend's authed proxy". The UI talks to
   one backend — never directly to DocEngine or Letta.
4. **The live Letta tool contract** the engine reproduces: `build_pp_document(markdown, out_name)` →
   `{ok, verify, path, bytes}`; `fetch_pp_document(path)` → base64 `.docx`.
5. **Planned QMS API surface (~10 endpoints):** registry CRUD, generate/workflow, rag-query,
   downloads, training matrix — replacing the old 38-endpoint monolith.
6. **Letta has no per-end-user auth — the app backend is the broker**; all capability enforcement
   (tiers, dept scoping, QMS_AUTHOR gates, ADMIN binding) lives in the app layer.
7. **Weekly snapshots** feed the QMS facility archive (`db2`), giving the SOP generator awareness of
   live operations; `GrowFlow_Weekly_Snapshots` is a regenerable Letta source.
8. **Gotenberg :3000** is the only reliable DOCX→PDF path from inside the stack.

### 2.3 Constraint-derived requirements

- Never expose DocEngine or Letta directly; all traffic goes through the authed backend, with
  capability scoping and audit.
- Never mint document codes client-side (server-issued `PREFIX-XX.YY.00`).
- Every AI answer that is not grounded renders its honest empty state (`grounded=false`), never a
  guessed answer.
- Permission and feature gaps must surface as honest panels, not silent mocks.

---

## 3. UI vision & principles

**Vision.** *DocEngine Studio* is a calm, auditable workspace where a QA Manager, QP or QC analyst can
move a document from a questionnaire to an effective, bilingual, GMP-controlled record — and where
an auditor can later reconstruct exactly what happened, with which model, on which sources — without
ever seeing a fabricated value or a fake progress bar.

**Principles (each traceable to a constraint above):**

1. **Truthful states.** Real job stages, real verify reports, real error payloads. Failures render as
   worklists, not toasts.
2. **Human-in-the-loop by default.** AI proposes; a human approves. Unknown values are empty inputs,
   highlighted for completion.
3. **Zone-clear.** Every screen carries its zone label (Operations = non-GMP / QMS-Studio, QC = GMP).
4. **Bilingual, Macedonian-first.** `MK | EN` everywhere, decimal commas, catalog-driven.
5. **Provenance or nothing.** Every generated assertion is either cited to a retrieved passage or
   marked unverified.
6. **One URL, one shell.** No second app; new screens are routes/components inside the GrowFlow PWA.
7. **Capability-aware.** The UI only offers functions and gates the server will allow a role.
8. **Composable surface for machines.** The same capability is a stable, versioned API — the UI is
   just one client of it (this is what makes MCP and external embedding possible).
9. **Audit is a feature, not a report.** Actions record actor, model, sources, and result as they
   happen.

---

## 4. Information architecture

The GrowFlow shell gains a first-class **QMS Studio** nav group. Proposed sitemap:

```
Operations            (non-GMP)
  Dashboard · Calendar · Board · Search · Notifications
QMS Studio            (GMP-controlled)          ◀ the DocEngine zone
  Studio Home
  Registry            (documents)
  Author              (wizard: Mode A)
  Build               (Mode B/C: paste/upload markdown)
  Knowledge           (corpus search, cited)
  Doc Control         (lifecycle, review-by)
  Training Matrix     (role × SOP)
  Approvals           (unified sign-off queue)
QC LIMS               (GMP-controlled)
  Samples · Results · OOS/CAPA · Instruments
Certificates          (GMP-controlled)
  eCoA Intake · Verify Loop · CoQ Print · CoA-QA
System
  Audit · Settings (incl. Settings → AI) · Admin
```

Routing: hash routes (`#/qms/registry`, `#/qms/author/:jobId`) inside the existing shell; each route
declares `zone`, `requiredCapability`, and `bilingualKeys`. A route guard hides (never disables)
nav items a role cannot use; the server independently 403s — the UI hiding is a convenience, the
server check is the control.

---

## 5. Screen-by-screen design

All screens are vanilla-JS ESM modules under `webui/js/qms/`, rendered into the existing shell with
**Mass Weed** tokens. Each declares `{zone, capability, titleKey}`. Shared components are listed in
§5.12.

### 5.1 Studio Home (`#/qms`)

A landing dashboard, QMS-Studio zone-labelled, composed of cards that are **all backed by real
endpoints** — a card whose data source is unavailable renders an honest empty state, never placeholder
numbers.

| Card | Data | Purpose |
|---|---|---|
| Authoring queue | `GET /workflows?status=running,awaiting_review` | Jobs in flight, with live stage |
| My drafts | `GET /documents?state=draft&mine=1` | Resume where you left off |
| Awaiting my approval | `GET /approvals?assignee=me` | Sign-off load |
| Doc control alerts | `GET /doc-control/alerts` | Superseded references, overdue periodic review |
| Recent certificates | `GET /certificates?limit=5` | QC handoff |
| AI usage (admin) | `GET /ai/usage` | Model/spend/health, links to Settings → AI |

### 5.2 Registry browser (`#/qms/registry`)

The master list of controlled documents.

- **Toolbar:** full-text search (Postgres FTS), type tabs (SOP / ANNEX / FORM / CHECKLIST / LOG /
  REPORT), family filter (code prefix), lifecycle state filter, ``from``/``to`` date, owner, review-by.
- **Table columns:** code · MK title · EN title · type · version · state · owner · effective date ·
  review-by · last job · actions.
- **Detail drawer** (right slide-over, deep-linkable `#/qms/registry/:code`): metadata header
  (server-issued code, version, zone label), **version history timeline**, linked tasks, linked
  certificates, the full `pp_verify` report of the latest artifact, and a **"Provenance" panel**
  showing which job, which agents, which sources and which model produced the current text.
- **States:** the lifecycle machine from `doc-control` is rendered inline as a compact stepper.
- **Actions (capability-gated):** Open in Word-compatible preview · Download `.docx` · Render PDF ·
  New version · Start periodic review · Supersede · Compare versions (diff of MK/EN text).

### 5.3 Author wizard — Mode A (`#/qms/author`)

The flagship flow, rebuilt **honestly** against `POST /workflows` and `GET /workflows/{id}`.

**Step 1 — Metadata.** Doc type, code family (server validates and issues the number — the client
never mints a code), MK title, EN title, version, orientation, parent SOP. Inline validation with the
registry's uniqueness rules.

**Step 2 — Questionnaire.** Rendered dynamically from `GET /questionnaires/{key}`: rounds as
accordion sections, `multi: true` as checkbox groups, `{v, default: true}` options pre-selected and
visually marked "compliant default". A progress meter counts *answered* questions, not elapsed time.
An **"Answers summary"** side panel lets the author review every choice before submitting.

**Step 3 — Generation (live).** Submitting calls `POST /workflows` and navigates to
`#/qms/author/:jobId`. The stepper mirrors the **real** pipeline stages emitted by the engine:

```
generate  →  generate 1.0 … generate 9.0  →  regulatory-check  →  regulatory-check n
   →  bilingual-check  →  qa-audit  →  format  →  done
```

Rules that make this honest:

- Progress is **derived from `stage`/`updated_at` polling**, never a client-side timer.
- Each completed section shows its own **regulatory verdict chip** (OK / GAP / CONFLICT / NO-FINDING)
  with the **citation** the engine returned — clicking a citation opens the retrieved passage.
- If a stage stalls, the UI shows the raw `updated_at` age and, after 60 min, renders the
  **abandoned-job** state the reaper writes ("no progress for 60 minutes"), with a *Retry* action that
  starts a fresh job.
- Transport is **SSE** (`GET /workflows/{id}/events`) with polling fallback every 3 s; polling is on
  `updated_at`, not just `status`.

**Step 4 — QA review.** On `done` the job payload is rendered as four panes:

1. **Draft preview** — the assembled bilingual Markdown rendered as styled HTML (house typography:
   navy `#2B547E` headers, MK 11 pt | EN 7–8 pt, `clear` shading, 6 pt floor) with a toggle to raw
   Markdown.
2. **Section editor** — per-section MK and EN fields side by side; edits are local until "Re-run
   verify" or "Save as new revision". Unknown values are **empty highlighted inputs**, never
   back-filled with AI guesses.
3. **Regulatory findings** — the `regulatory: []` array as a checklist; each finding links to its
   source passage; unresolved findings block submission.
4. **QA audit** — the `qa_audit` verdict text; a `FIX` verdict shows the issue list and a "Regenerate
   section" action that re-runs only the affected section.

**Step 5 — Render & register.** "Build controlled document" → `POST /build` (Mode B) → on PASS the
registry row appears and both `.docx` and PDF downloads are offered. On **422** the UI renders the
**full `pp_verify` report** as the review surface (it is QC feedback, not an error toast), with the
failures grouped: structure / typography / bilingual / §5A fidelity.

**Failure taxonomy the wizard must render distinctly:** verify-failed · §6A audit failed · bilingual
gaps (`bilingual_gaps: ["5.0 (no EN)"]`) · Letta/transport error · abandoned job.

### 5.4 Build — Mode B/C (`#/qms/build`)

For power users and for restyling existing drafts.

- Left: a **bilingual Markdown editor** with grammar assistance: syntax highlighting for
  `[[TABLE:mode]]` / `[[FORM:grid]]` / `~~` / `|||`, a snippet palette (table, form grid, kv_block,
  status grid, page break, sign-off block), and a lint panel warning about grammar hazards (e.g. a
  literal `-->` inside HEADERDATA meta values, which hard-fails the job).
- A **structure helper** renders the parsed document as a form-like editor (fields, grids, tables) for
  authors who should not touch micro-syntax; edits round-trip to Markdown.
- Right: live **verify panel** — run `POST /build` (dry-run flag) to see the PASS/FAIL report without
  registering a document; a `bilingual: no` escape hatch is surfaced **loudly** (banner + audit note)
  because it disables a QC check.
- Mode C entry point: upload `.docx`/text → "restyle to house format" → produces Markdown diff for
  human review before build.

### 5.5 Knowledge (`#/qms/knowledge`)

Cited corpus search over the regulatory sources used by generation (DB1_REGULATORY,
DB3_PP_CURRENT_unified — **PQ1 excluded**, 3072-dim embedding outlier).

- Query box → results as passages with source, document, section and similarity.
- "Ask" mode returns a grounded answer with inline citations; **no match renders the honest
  `grounded=false` empty state** with the message that no passage supports an answer.
- A "use in authoring" action pins a passage into the current wizard job's context, recorded in
  provenance.

### 5.6 Doc Control (`#/qms/doc-control`)

Lifecycle management, as specified in the master plan.

- State machine: **draft → in-review → approved → effective → periodic-review → superseded**.
- KPI band: effective count, in-review count, overdue periodic reviews, superseded-this-quarter,
  orphaned references.
- **Review-by KPI** with a red list of documents past review date.
- Type tabs and a detail drawer identical to the registry's.
- **Automation surfacing:** "task references a superseded SOP version → notify QA" appears as an
  alert card with the offending task list.

### 5.7 Training Matrix (`#/qms/training`)

Role × SOP grid: rows = the 13 roles, columns = active SOPs, cells = required/trained/expired.
Backed by the QMS training-distribution matrix; the approval chain maps to **QA_MGR → reviewer → QP**.
Export to XLSX for the training file.

### 5.8 Approvals (`#/qms/approvals`)

A single queue folding: QC CoQ DRAFT/APPROVED/VOIDED · task acknowledgements · draft-document locks.

- Live counts per category; filter by "assigned to me".
- Every approval opens a **decision sheet**: what changed, the evidence, the source job, then
  Approve / Reject with a mandatory reason (the shared `GF.reasonDialog`, replacing `prompt()`).
- **E-signature:** signing requires re-authentication and, once MFA ships, a TOTP challenge; the UI
  must be built so an e-signature is a **hard precondition** on APPROVED/RELEASED transitions — the
  design assumes the gate is enforced server-side and renders it as a blocking dialog, not a
  confirmation toast.

### 5.9 Certificates (QC zone)

- **eCoA Intake (`#/qc/ecoa-intake`)** — display-only workbench: pipeline stepper, §6.3.1 review
  countdown, **SHA-256 custody bar**, promotion/verify-gate notes. Human transcription workbench; the
  46 approved scans are the source of truth (the scan wins over any register, never re-OCR'd).
- **Adaptive review queue** — unknown label discovered → **map-once → auto-map** → promote into a
  DRAFT ECOA certificate + results **carrying source provenance**.
- **Verify Loop** — reconciliation records with VERIFIED / DISCREPANCY verdicts.
- **CoQ Print (`#/qc/coq-print`)** — on-screen **A4 certificate preview** (watermark, verdict header,
  identity grid, results, signatures) toggled **before** the `.docx`/PDF export; QP-gated render with
the GxP data gate (every result must comply).
- **CoA-QA** — `POST /coa-qa` cited answers; `grounded=false` renders as an explicit no-answer state.

### 5.10 Audit (`#/system/audit`)

Free-text search over entity/actor, chip filters (entity type, actor, action, date), and an explicit
**"Verify chain"** action with a verdict strip. Because the platform's audit is hash-chained, the UI
shows the chain segment per record and the recomputation result.

### 5.11 Settings → AI (`#/system/ai`)

ADMIN-only. Manages `ai_agent_bindings` (rebinding planner agents after fleet recreation), the model
routing table of §8, per-function enable/disable, spend and latency caps, and the **retrieval lane
routing** of §7. Every change is audited.

### 5.12 Component library (Mass Weed extensions)

| Component | Behaviour |
|---|---|
| `mw-bilingual-field` | MK/EN pair with linked resize; MK-first tab order; decimal-comma input for MK numbers |
| `mw-grid-editor` | Structured editor for `[[FORM:grid]]` / `[[TABLE]]`: add/remove rows and columns, MK~~EN cells, live width-pressure indicator that mirrors the engine's `fixed()` compression |
| `mw-status-grid` | Checkbox grids from single-select option lists |
| `mw-job-stepper` | Renders real stages with per-section verdicts and stall/abandoned states |
| `mw-verify-report` | Grouped PASS/FAIL viewer (structure, typography, bilingual, §5A fidelity) with machine-readable detail |
| `mw-provenance-chip` | Shows model · sources · job · timestamp for any generated span; click opens the source passage |
| `mw-custody-bar` | SHA-256 custody display for certificates and documents |
| `mw-blank-for-human` | Highlighted empty field state meaning "not in source — human must fill"; blocks export if marked mandatory |
| `mw-esign-dialog` | Blocking re-auth + signature dialog; records reason and identity |
| `mw-zone-badge` | Zone label (Operations non-GMP / QMS Studio GMP / QC GMP) on every screen header |
| `mw-grounded-answer` | Answer block that renders citations inline or the explicit no-answer state |

---

## 6. Platform architecture (UI, MCP, external embed)

The single most important architectural decision: **the UI is one client of a capability API**, not the
system. Everything below is designed so the same operations are reachable by the PWA, by an MCP server,
and by external platforms — with one policy engine in front.

### 6.1 Layers

```
┌──────────────────────────── clients ────────────────────────────┐
│  GrowFlow PWA (Zone: QMS Studio)   │  MCP clients (Claude, IDEs) │
│  External platforms (embed / API)  │  Future native apps         │
└───────────────┬────────────────────┴──────────────┬────────────┘
                │  HTTPS · JWT (users)             │  OAuth2 client-credentials (machines)
                ▼                                  ▼
┌──────────────────────── DocEngine Gateway (FastAPI) ────────────┐
│  AuthN/AuthZ · capability scopes · rate limits · audit            │
│  Job orchestration · provenance recording · SSE events            │
│  Retrieval lane router (§7) · Model router (§8)                   │
│  MCP adapter  ·  Embed/Widget API  ·  Public API v1               │
└───┬───────────────┬───────────────┬──────────────┬──────────────┘
    │               │               │              │
    ▼               ▼               ▼              ▼
┌─────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│DocEngine│   │  Letta    │   │  RAGFlow  │   │ Gotenberg │
│  :8000  │   │  server   │   │  evidence │   │   :3000   │
│ (line B)│   │  gf_* /   │   │   lane    │   │ DOCX→PDF  │
│ X-API-K │   │  general  │   │  authz on │   │           │
└─────────┘   └───────────┘   └───────────┘   └───────────┘
```

Hard rules carried from the current posture:

- DocEngine (:8000) and the Letta server are **internal-only**, reached only by the gateway. The
  unauthenticated `service.py` (:8600) is **never** exposed; if used at all it is loopback + gateway.
- The gateway is the **only** holder of `DOCENGINE_API_KEY`, `LETTA_API_KEY`, `RAGFLOW_API_KEY`.
- Every mutating operation writes an audit row (actor, capability, inputs hash, model, sources,
  result) into the existing hash-chained audit chain.
- Direct REST to Letta is the working path; the `letta-mcp-rust` bridge is not used.

### 6.2 Gateway API (`/api/v1`)

Versioned, capability-scoped, JSON. Draft contract:

| Method | Path | Capability | Purpose |
|---|---|---|---|
| GET | `/documents` | `qms.read` | Registry list (filter, cursor pagination) |
| GET | `/documents/{id}` | `qms.read` | Detail incl. verify report + provenance |
| GET | `/documents/{id}/versions` | `qms.read` | Version timeline + diffs |
| GET | `/documents/{id}/download` | `qms.read` | `.docx` |
| GET | `/documents/{id}/pdf` | `qms.read` | PDF via Gotenberg |
| POST | `/documents` | `qms.author` | Register a document record (server-issued code) |
| POST | `/documents/{id}/versions` | `qms.author` | New version (supersede + link) |
| POST | `/doc-control/{id}/transition` | `qms.control` | Lifecycle transition (guarded) |
| GET | `/questionnaires` · `/questionnaires/{key}` | `qms.author` | Question banks |
| POST | `/workflows` | `qms.author` | Start Mode A job |
| GET | `/workflows/{id}` | `qms.author` | Job state + result payloads |
| GET | `/workflows/{id}/events` | `qms.author` | SSE stage stream |
| POST | `/workflows/{id}/cancel` | `qms.author` | Cancel job |
| POST | `/build` | `qms.author` | Mode B/C build (422 carries verify report) |
| POST | `/build/dry-run` | `qms.author` | Verify without registering |
| POST | `/query` | `qms.read` | Cited retrieval (lane-routed, §7) |
| GET | `/approvals` · POST `/approvals/{id}/decision` | `qms.approve` | Sign-off queue + decisions |
| POST | `/signatures` | `qms.sign` | E-signature (re-auth + MFA) |
| GET | `/training-matrix` | `qms.read` | Role × SOP |
| GET | `/certificates*` | `qc.*` | CoA/CoQ surface |
| GET | `/ai/functions` | any | Catalog filtered by role tier |
| POST | `/ai/invoke` | any | Invoke a capability (403 below tier) |
| GET | `/ai/usage` | `admin.ai` | Model/spend/health |
| PATCH | `/admin/ai/bindings` | `admin.ai` | Agent/model bindings |

**Conventions:** idempotency keys on POSTs; `ETag`/`If-Match` on document mutations; RFC 9457
problem+json errors carrying machine-readable codes; cursor pagination; every response includes
`zone`, `provenance_id`, and `grounded` where applicable.

### 6.3 Machine identity & capability model

Users authenticate with the existing JWT. **Machines** (MCP clients, external platforms) use
**OAuth2 client-credentials**:

- Clients are registered as `api_clients` (name, owner, redirect not needed, `scopes[]`, `rate_limit`,
  `expires_at`, `allowed_ips`, `status`).
- Tokens are short-lived JWTs signed by the gateway, carrying `sub=client:<id>`, `scopes[]`, `zone`.
- Scopes are **capability** strings (`qms.read`, `qms.author`, `qms.build`, `qms.approve`,
  `qms.sign`, `qc.read`, `qc.write`, `certs.render`, `knowledge.query`, `admin.ai`) — never roles.
  A client can be granted `knowledge.query` without any document access, which is exactly what an
  external "ask our SOPs" integration should get.
- **Confused-deputy protection:** the gateway never lets a client act *as* a user. Actions are
tagged `actor_type=client` with the owning user recorded as sponsor; approvals and signatures are
  never available to client credentials.
- Scopes that are GMP-critical (`qms.approve`, `qms.sign`, `certs.render`) require an explicit admin
  grant plus a second reviewer (two-person rule), recorded in audit.

### 6.4 Events

`GET /workflows/{id}/events` (SSE) emits `stage`, `section`, `regulatory`, `bilingual`, `audit`,
`verify`, `done`, `failed` frames. Consumers that cannot hold SSE (most MCP clients) poll
`GET /workflows/{id}`; the contract guarantees the same state. This is the single source of truth for
UI progress — no simulated progress anywhere.

### 6.5 MCP server design

The MCP surface is a **purpose-built adapter inside the gateway** (`/mcp`, streamable HTTP + stdio
shim for local clients), not a wrapper around the broken Rust bridge.

**Tools exposed** (names, argument sketches):

| Tool | Args | Returns |
|---|---|---|
| `docengine_search_documents` | `query?, type?, state?, limit` | registry rows |
| `docengine_get_document` | `id or code` | metadata + verify report + provenance |
| `docengine_download` | `id, format: docx\|pdf` | resource link / base64 |
| `docengine_ask` | `question, lane?` | grounded answer + citations + `grounded` flag |
| `docengine_build` | `markdown, out_name` | `{ok, document_id, verify, bytes}` |
| `docengine_verify` | `markdown` | verify report (no registration) |
| `docengine_list_questionnaires` | – | banks index |
| `docengine_start_workflow` | `questionnaire, answers, meta` | `{job_id}` |
| `docengine_get_workflow` | `job_id` | job state + result |
| `docengine_list_pending_approvals` | `assignee?` | approvals (read-only) |

**Resources:** `docengine://documents/{id}` (metadata), `docengine://documents/{id}/markdown`,
`docengine://questionnaires/{key}`, `docengine://verify/{id}`.

**Design rules:**

- Tools are **capability-scoped** by the client token; a tool not covered by scope is simply absent
  from `tools/list` (capability filtering mirrors the existing `/ai/functions` behaviour).
- **Never** expose approve/sign over MCP in v1. Human sign-off stays in the authenticated UI.
- **Provenance and model identity are returned in tool results** so an MCP client's answer can be
  audited back to a job, a model and a source passage.
- Long operations return job handles, never block; the client polls (MCP clients are poll-friendly,
  unlike browsers).
- Idempotency on `docengine_build` to avoid duplicate registry rows on retries.

**Why not `letta-mcp-rust`:** reproduced decode failure (`missing field 'package'`), tool-name
prefix instability, ~500-char block truncation, false aggregates, empty streaming responses, 405s on
`open_file`/`reset_messages`. Wrapping it would import all of that into the product surface.

### 6.6 External platform integration (later phase)

Two supported integration modes, both over the same gateway:

1. **API/SDK integration.** An external platform authenticates with client credentials, calls
   `/api/v1/*`, and receives document metadata, downloads and cited answers. Domain events are pushed
   by webhook (`document.created`, `document.approved`, `workflow.failed`) with HMAC signatures and
   replay protection. An OpenAPI 3.1 spec is generated from the gateway and is the single source of
   truth for SDK generation (Python, TypeScript, PHP).
2. **Embedded widget.** A single `<script>` tag mounts a **web component** (`<docengine-widget>`)
   that runs the Doc Studio UI in an iframe against the gateway. Authentication uses a short-lived,
   purpose-scoped **embed token** minted by the host platform's backend; the widget never sees the
   host's session. `postMessage` events let the host react (`docengine:document-created`). The widget
   must be usable for exactly the low-risk flows — ask (cited), build/verify, list documents — and
   must **not** offer approvals, signatures, or admin.

Both modes are gated by the same capability engine, so onboarding an external partner is a
configuration change, not a code change.

### 6.7 Data model additions (schema `docengine` inside `wwf_tasks`)

Existing: `docengine.jobs`, `docengine.documents`. Additive migrations only.

```
docengine.documents      + state, effective_at, review_by, supersedes_id, owner_role,
                           zone, provenance_id, family
 docengine.document_versions  (id, document_id, version, markdown, artifact_path, verify, created_by, created_at)
 docengine.provenance        (id, job_id, section, agent, model, lane, sources jsonb, created_at)
 docengine.approvals         (id, document_id, kind, assignee_role, state, reason, signed_by, signed_at, sig_id)
 docengine.signatures        (id, actor, method, reauth_at, mfa, meaning, hash, created_at)
 docengine.api_clients       (id, name, owner, scopes[], rate_limit, allowed_ips, status, expires_at)
 docengine.audit_links       (id, entity, entity_id, chain_hash, created_at)   -- joins the platform chain
 docengine.model_routing     (function_key, primary_model, fallback_model, max_tokens, temp, enabled)
 docengine.lane_router       (intent, lane, evidence_required bool)
```

### 6.8 Deployment deltas

The gateway is a module inside the existing FastAPI backend (modular monolith — no new service to
run, no new entry point). What is added to the stack:

- Route blocks in nginx: `/api/v1/*` and `/mcp` on the existing host; **nothing new is published**
  from DocEngine/Letta/RAGFlow.
- `RAGFLOW_API_KEY` stored only in the gateway env; RAGFlow's client auth enabled (§7) before any
  external exposure.
- New Postgres schema `docengine` (already exists for jobs/documents) extended by additive alembic
  migrations, CI-checked for lockstep.
- SSE endpoint must be allowed through nginx with buffering off (documented quirk: the existing
  topology runs behind nginx, and SSE requires `proxy_buffering off;`).

---

## 7. Dual-system RAG: RAGFlow for official results, Letta for everything else

**Question:** Can RAGFlow be used exclusively for generating official, verified results, while Letta
handles all other RAG-based tasks and general queries?

**Answer: Yes — feasible and recommended — but only with hard lane separation, explicit evidence
tagging, and a no-silent-fallback rule.**

### 7.1 What the repository already implies

The repo already contains two distinct retrieval stacks, used for different purposes:

| Stack | Current use in the repo |
|---|---|
| **RAGFlow** | The **eCoA ingestion + retrieval pipeline** (`ingestion/ragflow/**`: `ECOA_RAG_PIPELINE_2026-08-30.md`, `doc_identity.py`, `replace_reissued.py`, `validate_ecoa_limits.py`). It is the *evidence* lane for certificates. It has an MCP enablement path (`server/RAGFLOW_MCP_ENABLE.md`). |
| **Letta sources** | Generation grounding for the `gf_*` fleet: `DB1_REGULATORY`, `DB3_PP_CURRENT_unified`, `GrowFlow_Weekly_Snapshots`. Letta is also the general assistant (`gf_app_assistant`). |

Critically, the master plan already records a retrieval-stack decision: **"Qdrant + VoyageAI RAG — superseded
by Letta RAG sources + Postgres FTS (`/coa-qa`) + DocEngine knowledge search"** — i.e. the platform has
already accepted *multiple coexisting retrieval mechanisms*. A dual-lane design is therefore not a new
architecture; it is a **formalization** of what exists.

### 7.2 The proposed lane model

Introduce an explicit **retrieval lane router** in the gateway (§6.1). Every retrieval call declares an
intent, and the router maps intent → lane. This is the load-bearing mechanism: official results are
*never* produced by an ad-hoc model call.

| Intent | Lane | Grounding | Output rule |
|---|---|---|---|
| Certificate/report **verification** (CoA vs limits, identity, reissue checks) | **RAGFlow (official)** | Ingested, identity-resolved certificate corpus with provenance | Result may carry **VERIFIED / DISCREPANCY**; may become a GMP record |
| **Regulatory citation** for authoring (DB1_REGULATORY, DB3) | **Letta sources (generation grounding)** | Attached Letta sources; citations returned per section | Cited passage required; **NO-FINDING** is a valid, honest outcome |
| **General questions**, drafting help, translation, app assistant | **Letta (`gf_app_assistant`, `gf_translator_mk_en`)** | Conversation + attached sources | Marked **advisory — not a controlled result** |
| **CoA Q&A** (already implemented) | **Postgres FTS `POST /coa-qa`** | The certificate record store | Cited or `grounded=false` |
| **Corpus exploration / audit evidence** | **RAGFlow** | Ingestion corpus | Cited passages, read-only |

### 7.3 Why this split is correct

1. **Determinism vs creativity is the real axis.** Official results need *retrieval fidelity* and
   *identity resolution* ("is this the same sample, the same reissue, the same limits?") — RAGFlow's
   ingestion pipeline does document identity, reissue replacement and limit validation
   (`doc_identity.py`, `replace_reissued.py`, `validate_ecoa_limits.py`). A conversational agent stack
   optimizes for fluent synthesis, which is the wrong objective for a controlled result.
2. **Auditability.** An official result must be reproducible: which corpus version, which document
   identity, which limits file. RAGFlow keeps the ingested artifact and its provenance. Letta agent
   conversations do not produce a stable, replayable evidence chain by themselves.
3. **Blast-radius control.** If the general assistant hallucinates, the damage is a wrong draft.
   If the official lane hallucinates, the damage is a wrong certificate. Separate them physically.
4. **The repo has already fought this battle.** The `gf_reg_checker` is explicitly required to *"cite
   real passages; never fabricate a clause"*, and PQ1 was excluded from regulatory sources because of
   an embedding-dimension mismatch (3072-dim outlier). That is a lane-separation instinct already
   present; the proposal just makes it explicit and enforceable.

### 7.4 Integration challenges (and responses)

| # | Challenge | Response |
|---|---|---|
| 1 | **RAGFlow auth is missing.** It "authenticates no client and is publicly routed" (accepted risk 2026-08-25). | Enabling client auth is a **precondition** for the official lane; the gateway holds the only key. Until then, RAGFlow stays internal-only. |
| 2 | **Two embedding spaces.** Letta sources (1536-dim) and PQ1 (3072-dim) already cannot cross-search; RAGFlow has its own index. | Never unify the indexes. The router treats them as separate corpora; cross-lane answers must cite each lane separately. |
| 3 | **Duplicate/contradictory evidence** (same document in both lanes with different text). | A **document identity registry** (RAGFlow's identity decisions, surfaced read-only in the UI) is authoritative for certificates; Letta sources keep only regulatory/operational text, not certificate scans. |
| 4 | **Model behavior differs per lane.** A general model must not be used for official extraction. | Lane-specific model binding in the model router (§8): official/extraction functions pinned to the deterministic model; advisory functions may use the reasoning model. |
| 5 | **"Official" must be a first-class, visible state** — not an internal flag. | Every answer/result carries `lane`, `evidence[]`, `official: bool`, `grounded: bool`. The UI renders a **Verification Lane badge**; external/MCP consumers receive the same fields. |
| 6 | **Latency/availability.** RAGFlow had no swap and lost in-flight documents under memory pressure (OPEN_DECISIONS E1). | The router fails **closed** for official intents ("evidence lane unavailable" — never a silent Letta fallback); advisory intents may degrade to Letta with a visible notice. |
| 7 | **No-silent-fallback is the whole safety property.** | Enforced in the router code path, asserted in tests, and shown in the UI: official requests that cannot reach RAGFlow return a typed error, never an answer. |
| 8 | **MCP exposure of both lanes.** | `docengine_ask(lane=...)` exposes the lane as a required parameter for official intents and defaults advisory intents to Letta; the tool description states the contract. Official-verification tools are scope-gated (`certs.render`, `qc.write`). |

### 7.5 What this changes in the UI

- **Knowledge screen** gains a lane selector (default: *Advisory (Letta)*; *Official evidence (RAGFlow)*
  is a distinct, clearly-labelled mode requiring the right capability).
- **Answers are visually distinct:** advisory answers carry a muted "advisory" badge; official results
  carry the Verification Lane badge, the evidence list and the custody hash.
- **The eCoA intake workbench already is the RAGFlow face**; the design connects it to the same lane
  router so the UI never has two different mental models of "where does evidence come from".

---

## 8. Multi-model architecture: Moonshot ALEGRETTO vs DeepSeek

**Requirement:** every AI function and autonomous agent in the system must be powered by either the
**Moonshot ALEGRETTO subscription API** or the **DeepSeek API**, with a per-function technical
justification.

### 8.1 Decision criteria

| Criterion | Why it matters here |
|---|---|
| **Long-context fidelity** | SOP sections, multi-document corpora, certificate bundles are large; a model that loses the middle of a long prompt produces plausible-but-wrong output. |
| **Instruction adherence / formatting discipline** | The engine consumes a strict micro-syntax; a model that deviates produces grammar errors and failed builds. |
| **Bilingual MK/EN quality** | Macedonian is a low-resource language; translation/mirroring quality is a hard requirement (bilingual from day one). |
| **Determinism / temperature discipline** | Controlled-document generation must be reproducible; extraction and checking must be near-deterministic. |
| **Tool/function-calling reliability** | The `gf_*` fleet is driven over Letta REST; unreliable tool calls break the pipeline. |
| **Throughput & cost on subscription vs metered** | A subscription API is preferred for high-volume, always-on functions (drafting, chat, classification); metered pay-per-token is preferred for low-volume, high-stakes functions (official verification, final QA audit). |
| **Data residency / provider posture** | GMP data sensitivity; the provider must be acceptable for the deployment posture. |
| **Operational maturity** | Retries, rate-limits, streaming, failures — the platform has already had a credit-exhaustion incident (`incident_2026-08-12_openai_credit_exhaustion.md`). |

### 8.2 The two candidates

- **Moonshot ALEGRETTO (Kimi, subscription API).** Notable for very large context handling and strong
  long-document synthesis; subscription pricing makes high-volume drafting and chat economical. Its
  strength is *producing* large coherent bilingual text (SOP bodies, translations, summaries).
- **DeepSeek (API).** Already the *working fleet provider* in this repository (the `gf_*` fleet runs
  on DeepSeek today). Notable for strong reasoning-per-euro, disciplined instruction following, and
  cheap deterministic-ish structured output with low temperature. Its strength is *checking*, *routing*,
  *extracting* and *auditing*.

**A note on the requirement's phrasing.** "Every function must be powered by Moonshot **or** DeepSeek"
means this pair must cover the whole map. Some functions (embedding, reranking) are not chat models at
all and stay on their dedicated providers (Letta's embedding models). The router therefore has two
*chat* providers plus explicitly-declared non-chat services, and §8.4 marks those.

### 8.3 Function → model mapping

Legend: **MS** = Moonshot ALEGRETTO · **DS** = DeepSeek · *(non-chat)* = not a chat provider choice.

#### A. Authoring pipeline (Mode A)

| # | Function | Model | Justification |
|---|---|---|---|
| A1 | Orchestration / job sequencing (`gf_doc_orchestrator`, and the in-code pipeline) | **DS** | Small, high-frequency routing decisions with structured outputs; DeepSeek's instruction adherence and cost make it the right dispatcher. Not a creative task. |
| A2 | SOP section authoring, sections 1.0–9.0 (`gf_sop_author`) | **MS** | Produces long bilingual sections that must remain coherent across 9 sections and the assembled document; Moonshot's long-context synthesis is the strongest fit. Highest token volume → subscription economics. |
| A3 | Annex / form / log drafting with `[[FORM:grid]]` (`gf_annex_author`) | **MS** | Structured-but-narrative; benefits from long-context consistency with the parent SOP, which is part of the prompt. |
| A4 | RACI / responsibilities section (`gf_raci_specialist`) | **DS** | Constrained, schema-like content with a hard rule (never hardcode personnel names). DeepSeek follows explicit constraints reliably. |
| A5 | Regulatory check + citation (`gf_reg_checker` and ephemeral clones) | **DS** | Verification, not generation. Must return `{section, verdict, citation, note}` or NO-FINDING and must not invent clauses. Reasoning discipline beats fluency here; verified as already working on DeepSeek. |
| A6 | Bilingual parity / translation (`gf_translator_mk_en`) | **MS** | Macedonian is low-resource; Moonshot's multilingual synthesis produces better MK↔EN mirroring. Also used interactively (high volume). |
| A7 | §6A QA audit (`gf_qa_auditor`) | **DS** | Final gate before the engine. Must be strict, conservative and deterministic; DeepSeek's checking posture is correct, and using a *different* provider from the authoring model (MS) is a deliberate separation of duties — the auditor should not share the author's failure modes. |
| A8 | Assembly / formatting fallback when the engine's grammar parser rejects | **DS** | Mechanical transformation with a strict target grammar; deterministic repair. |

#### B. Build / verify / registry

| # | Function | Model | Justification |
|---|---|---|---|
| B1 | Markdown grammar repair (preamble stripping, separator fixes) | **DS** | Deterministic transformation; low temperature; cheap. |
| B2 | `pp_verify` interpretation → human-readable failure grouping | **DS** | Classification/summarization of machine output; must not add interpretation beyond the report. |
| B3 | Document metadata suggestion (title EN if missing, family guess) | **MS** | Translation/synthesis; advisory only, flagged as a suggestion for a human. |
| B4 | Version-diff narrative ("what changed in v1.2") | **MS** | Long-context comparison of two bilingual versions; narrative output. |

#### C. Certificates / QC official lane

| # | Function | Model | Justification |
|---|---|---|---|
| C1 | CoA value extraction from transcription records (structure → fields) | **DS** | Extraction with strict schema; must be conservative and traceable; low temperature. |
| C2 | Limit/identity/reissue verification (official) | **DS** | Deterministic checking against RAGFlow evidence; **no creative fallback**; failures are returned as typed results. |
| C3 | CoQ verdict text assembly (from verified fields, no new facts) | **DS** | Constrained templating; must not introduce new data — the strongest argument for the conservative model. |
| C4 | `POST /coa-qa` cited answer synthesis | **MS** | Single-pass synthesis over retrieved passages; long-context helps when several certificates are cited; still policy-gated to citations only. |
| C5 | Adaptive review-queue label mapping (label → analyte, map-once → auto-map) | **DS** | Classification; once mapped it is deterministic — high volume, low creativity, occasional one-off reasoning. |
| C6 | eCoA discrepancy report wording | **DS** | Must state exactly the mechanical difference; no embellishment. |

#### D. General assistant / platform functions

| # | Function | Model | Justification |
|---|---|---|---|
| D1 | `gf_app_assistant` general in-app assistant | **MS** | Conversational, open-ended, frequent; subscription economics; broad knowledge useful. |
| D2 | Voice capture → task/note draft | **MS** | Speech-derived text cleanup and synthesis; frequent, low-stakes, human-reviewed. |
| D3 | `translate_bilingual` (platform-wide UI/notification translation) | **MS** | Same multilingual argument as A6; platform-wide volume. |
| D4 | `draft_description` (task/batch descriptions) | **MS** | Short creative drafting; high volume. |
| D5 | Bilingual notification generation | **DS** | Short, templated, must exactly mirror the source event; conservative model reduces over-writing. |
| D6 | Search query understanding / intent parsing (incl. lane routing, §7) | **DS** | Structured classification with a small schema; wrong routing must be rare; deterministic. |
| D7 | Document/chip classification, tagging | **DS** | Deterministic classification. |
| D8 | Weekly snapshot summarization (operational awareness for the SOP generator) | **MS** | Long-context summarization of a week of operations; narrative. |
| D9 | Training-content generation from an SOP | **MS** | Synthesis over an existing document; long-context fidelity to the source SOP. |
| D10 | Report narrative from calculated datasets (QC weekly, potency) | **DS** | Numbers are computed by `pp_data.py`; the model only narrates them and must never change a figure — conservative model preferred. |

#### E. Non-chat services (declared for completeness)

| # | Function | Provider |
|---|---|---|
| E1 | Embeddings for Letta sources | Letta's configured embedding model (`openai/text-embedding-3-small`, 1536-dim) — **not** a chat model; PQ1's 3072-dim model stays isolated |
| E2 | Reranking / FTS | Postgres FTS + RAGFlow's own retrieval — no chat model |
| E3 | OCR / document conversion | Gotenberg / existing tooling — not a model choice |

### 8.4 The routing principle behind the table

A single rule explains the whole map:

> **Moonshot ALEGRETTO is the *author/producer* model; DeepSeek is the *checker/operator* model.**

That is a separation-of-duties design, not a preference. In a GMP pipeline the entity that *creates*
content should not be the entity that *verifies* it. The mapping implements that:

- **Produce** (long bilingual text, translation, narrative, conversation) → Moonshot.
- **Check, route, extract, audit, template** (structured, conservative, reproducible) → DeepSeek.
- **Audit the author** (`gf_qa_auditor`) runs on DeepSeek while the author runs on Moonshot —
  cross-provider verification.

This also aligns with what the repo already runs (DeepSeek as the working fleet provider) and with the
cost profile (subscription for high-volume generation, metered for surgical checks).

### 8.5 Model router

Implemented as `docengine.model_routing` (§6.7) read by the gateway:

```
function_key      primary   fallback   max_tokens   temp   enabled
sop_section_author   MS        DS         8192       0.3    true
reg_check            DS        DS         2048       0.0    true
qa_audit             DS        DS         2048       0.0    true
translator_mk_en     MS        DS         4096       0.2    true
coa_extract          DS        --         2048       0.0    true
coq_verdict          DS        --         1024       0.0    true
app_assistant        MS        DS         4096       0.4    true
...
```

Rules:

- **No fallback across the produce/check boundary.** An authoring function may fall back MS→DS with
  an audit note; a *checking* function never falls back to the producing model (DS→MS forbidden).
  If the checker is unavailable, the job fails visibly.
- Every call records `function_key`, `model`, `lane`, `sources`, `tokens`, `job_id` into provenance.
- Temperature is 0.0 for every checking/extraction function; GMP-critical checks never run sampled.
- Provider credentials live only in the gateway; the UI and MCP clients never hold them.
- A provider outage surfaces as a typed job failure (":code — provider unavailable"), never as a silent
  downgrade of a GMP result.

---

## 9. Delivery roadmap

Sized as increments that each end in something usable and testable. No phase simulates progress or
touches prod without owner approval.

| Phase | Content | Exit criteria |
|---|---|---|
| **P0 — Gateway skeleton** | `/api/v1` router module in the FastAPI backend, JWT pass-through, audit wrapper, thin proxy to DocEngine `/documents`, `/workflows`, `/build`, Gotenberg PDF. | Auth + audit verified; no new published ports; pytest + a smoke script. |
| **P1 — Studio shell** | QMS Studio nav group, Studio Home, Registry browser + detail drawer, verify report viewer, zone badges, bilingual keys, no-simulated-progress job stepper. | A real Mode A job can be started and watched in the browser end-to-end. |
| **P2 — Author wizard** | Metadata → questionnaire → live stages → QA review → build/register; failure taxonomy rendering; SSE + polling fallback. | A real SOP is authored, verified (`RESULT: PASS`) and registered through the UI. |
| **P3 — Build (Mode B/C) + Knowledge** | Bilingual Markdown editor with grammar assistance; verify dry-run; cited knowledge search with lane selector (§7). | Power users can restyle/build without touching the CLI or `ppdocwiz`. |
| **P4 — Doc Control + Approvals + Audit** | Lifecycle transitions, review-by KPIs, unified approvals queue with reason dialogs, e-signature dialog (enforced once the server gate lands), audit chain viewer. | A document moves draft→effective through the UI with a signed approval. |
| **P5 — Certificates** | eCoA intake workbench, adaptive review queue, verify loop, CoQ preview, CoA-QA cited answers. | A CoA is transcribed, verified and rendered to a QP-gated CoQ. |
| **P6 — Machine surface** | OAuth2 client-credentials, `api_clients`, capability scopes, OpenAPI 3.1, webhooks, MCP adapter (read/build/ask), embed token + `<docengine-widget>`. | An external MCP client lists documents, asks a cited question and builds a document under a scoped token. |
| **P7 — Model router + lane router** | `model_routing` (§8), `lane_router` (§7), RAGFlow client auth, provenance recording, admin Settings → AI. | Official vs advisory intents are structurally separated and audited. |

**Dependencies on owner decisions** (from `review/OPEN_DECISIONS_2026-08-29.md`) that should be
resolved for a clean P5/P7: A2 (RAGFlow MCP auth/routing), A3 (Letta API auth), A4 (rotate the RAGFlow
key, drop the gitleaks allowlist), E1 (RAGFlow swap), E4 (scheduled `pg_dump`), B2 (30 agents
retrieving from deleted sources), D3 (engine sync hold).

---

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Engine drift (master vs live volume) | UI shows one engine, live runs another | Drift check in CI before any release; re-hash per `engine_sync.md` |
| Two engine lines still unconverged | Divergent rendering of the same document | Keep the merge hypothesis as the plan; key UI feature checks off the vendored canon |
| Letta 0.16.8 pinned; 0.17 upgrade on hold | Model/provider changes are constrained | The model router must be able to bind models *through* the current Letta provider config; no upgrade required for §8 |
| RAGFlow lacks auth/swap | Official lane unsafe or flaky | Lane fails closed; no external exposure until auth enabled |
| `awaiting_review` never set server-side | No server-side approval gate today | The UI's approval step is backed by a gateway approval record (`docengine.approvals`) with audit, not by a job status the engine never writes |
| MCP bridge unreliability | External integrations break | Purpose-built MCP adapter over gateway API; bridge unused |
| `-->` in metadata hard-fails a job | Silent user frustration | Grammar lint in the Build editor + lint on questionnaire answers |
| Stale/abandoned jobs | Stuck UI | Poll on `updated_at`; surface the reaper's 60-min abandonment state with Retry |
| Documents list capped at 100, no pagination | Missing documents in UI | Gateway implements cursor pagination over the registry; UI never trusts the raw 100-cap list |
| E-signature not yet enforced as a gate | Compliance gap | Design assumes server-side hard gate; UI blocks on the dialog and records intent; enforcement tracked as a hardening item |

---

## 11. Verification & evidence

What this design is based on, and what would falsify it:

- **Repository facts** (verified by three independent read passes over the repo at `96fdd163`):
  engine API surfaces, job stages, questionnaire banks, fleet composition, document grammar,
  constraints in `OPEN_DECISIONS` and `APP_SECURITY_REVIEW`, topology docs, existing front-ends.
- **Assumptions that need a live check before implementation:**
  - `qms-api` :8500 endpoint specs (not in repo); verify against the live service if it is to be proxied.
  - The exact GMP gate currently applied at CoQ render (documented as a gate; endpoint behavior should
    be confirmed).
  - RAGFlow's retrieval API shape for the official lane (the repo documents the ingestion pipeline,
    not the query API) — confirm before writing the lane router client.
  - Whether the live GrowFlow backend already exposes any `/qms` proxy contract that the gateway would
    replace or extend.
- **Not run:** no live calls to DocEngine, Letta, RAGFlow or Gotenberg were made for this design; it is
  an architecture proposal, not a verified integration.

---

## 12. Appendix — API surface quick reference

### 12.1 DocEngine (Line B, internal :8000, `X-API-Key`)

```
GET  /health
GET  /questionnaires
GET  /questionnaires/{key}
POST /workflows                        -> {job_id, status: queued}
GET  /workflows/{jid}
POST /build                            -> 200 {ok, document_id, bytes, verify} | 422 {verify}
GET  /documents
GET  /documents/{did}
GET  /documents/{did}/download         -> .docx | 404 | 410 artifact missing
GET  /documents/{did}/pdf              -> PDF | 503 GOTENBERG_URL unset | 502 render fail
```

Job stages: `generate` → `generate {1.0..9.0}` → `regulatory-check` → `regulatory-check {n}` →
`bilingual-check` → `qa-audit` → `format` → `done`. Jobs: `queued|running|done|failed` (schema also
defines `awaiting_review`, never set).

### 12.2 Line A service (open :8600 — never expose)

```
GET  /health
POST /build        -> 200 {ok, path, verify}      (200 even on FAIL — check .ok)
POST /build.docx   -> .docx | 422 {ok:false, verify}
POST /build.pdf    -> PDF | 422 | 501 no renderer
```

### 12.3 Bilingual Markdown grammar (the UI's core data format)

```
<!--HEADERDATA
mk_title: …
en_title: …
code: …
version: 1.0
doctype: SOP|ANNEX|FORM|CHECKLIST|LOG
parent: …
orient: portrait|landscape
bilingual: no          # disables a QC check — surface loudly
-->
# 1.0 ЦЕЛ|PURPOSE
MK text ||| EN text
[[TABLE:mode]] … [[/TABLE]]
[[FORM:grid]] … [[/FORM]]
cell MK ~~ cell EN
```

No `-->` anywhere inside metadata values.

### 12.4 Model map (summary)

| Domain | Producer (Moonshot ALEGRETTO) | Checker/Operator (DeepSeek) |
|---|---|---|
| Authoring | SOP sections (1.0–9.0), annexes/forms, MK⇄EN translation, metadata suggestions, version-diff narrative | Orchestration, RACI section, regulatory check + citations, QA audit, assembly repair |
| Certificates | CoA-QA cited answer synthesis | CoA extraction, limit/identity/reissue verification, CoQ verdict assembly, label mapping, discrepancy wording |
| Platform | App assistant, voice capture, UI translation, task descriptions, weekly snapshot summaries, training content | Intent/lane routing, notification mirroring, classification/tagging, report narration |
| Auditor separation | author = MS | **auditor = DS (cross-provider, deliberate)** |

---

*End of design document. This is a proposal for owner review; no production system was modified.*


