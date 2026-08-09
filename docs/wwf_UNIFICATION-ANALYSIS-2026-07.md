# Unification Analysis: WWF/GrowFlow + QMS Creator → one Purely Plant platform

*2026-07-15 · Prepared for the owner's question: "analyze the possibility to
merge these two applications and produce a third app here in the same repo …
one unified platform for Purely Plant."*

Method: four parallel deep-dives (QMS backend, QMS frontend, domain-overlap
mapping, and a cited web-research pass on consolidation patterns), plus
direct verification of the live deployment on kvm4. Every load-bearing claim
below traces to code (file references in the repo) or a cited source.

---

## 1. Executive summary

**Yes — and the two apps are unusually well-suited to it.** They are
complementary halves of one platform: the QMS Creator authors the controlled
world ("what should be done" — SOPs, forms, RACI, training, regulatory
knowledge), WWF/GrowFlow runs the operational world ("what is being done" —
tasks, sessions, weekly locked records, notifications, analytics). They
already share the facility, the language pair (EN/MK), the SOP code
vocabulary, a near-1:1 role mapping, the same server, and the same Letta AI
instance.

**Recommendation — build the "third app" as an absorption, not a rewrite:**

> The unified platform ("Purely Plant Platform") = **WWF's foundation**
> (JWT auth, roles, Postgres RLS, hash-chained audit, bilingual PWA shell,
> deploy/CI machinery) + **QMS Creator's engine** (Letta multi-agent SOP
> generation, dual regulatory RAG, DOCX renderer, document registry &
> coding system) + **a new QMS Studio zone** built properly on that
> foundation. The QMS Creator's app shell (auth, persistence, API surface)
> is discarded — analysis shows it is the weakest layer of that codebase
> and much of it was never wired up.

This is the strangler-fig direction every line of evidence points to
(§6 research): don't rewrite WWF's battle-tested core; don't preserve QMS
Creator's thin shell; absorb the thinner app into the mature one, in phases,
with a hyperlink-federated interim so value ships immediately. A literal
third codebase written from scratch is the one option the evidence rejects
outright.

Estimated shape: **4 phases, roughly 8–12 working cycles** of the size this
project ships per cycle, each phase independently valuable and reversible.

---

## 2. What exists today (verified)

### 2.1 WWF / GrowFlow (`backend/`, `web/`)

Mature and in production (~25 real users): FastAPI backend over two
Postgres databases (`wwf_users` identity + `wwf_tasks` work data) with
row-level security, per-request identity GUCs, hash-chained tamper-evident
audit triggers, JWT auth with forced-password lifecycle, a 13-role model
(ADMIN / OWNER / CEO / COO / QP / 7 dept managers / USER), department
scoping, notifications + activity feed + canned automation rules, weekly
Plan/Report document engine with DB-enforced lock immutability, facility
board, approvals, analytics, and a bilingual vanilla-JS PWA with offline
support. 275 backend tests, 12 e2e specs, path-scoped CI, test→prod deploy
discipline on kvm4.

### 2.2 QMS Creator (`qms-creator/`, imported 2026-07-15)

A standalone SOP/QMS document generator. The deep-dive found a sharply
two-sided codebase:

**The strong half — the engine (worth absorbing):**
- Letta multi-agent SOP pipeline: 11 section agents + researcher +
  assembler (`CONTENT_CREATOR_FRAMEWORK/agent_definitions.py`), per-section
  RAG with database weights and gap detection (`letta_workflow.py`),
  Perplexity web-research tool, custom sandbox tools (GMP section
  validation, RACI matrix, Mermaid flowcharts).
- Dual regulatory knowledge base on the shared Letta server:
  `db1_regulatory` (47 EU-GMP/ICH/WHO documents) + `db2_entity_qms`
  (252 facility documents, 3,167 passages).
- A mature DOCX renderer (`docx_engine/workflow_to_docx.py`): Purely Plant
  theme, cover pages, approval/revision tables, TOC, color-coded RACI.
- The document registry and coding system (`config/document_registry.yaml`,
  `document_code_service.py`): 10 families, bilingual titles, auto-numbered
  `PREFIX-XX.YY.00` codes, annex scheme — plus the produced SOP library
  (`sops_created/`), operational form templates, and the training
  distribution matrix.

**The weak half — the shell (not worth preserving):**
- One ~2,770-line FastAPI file, 38 endpoints, no routers.
- Auth = a single shared `X-API-Key` for everyone; only 5 of 38 endpoints
  even check it. No users, no roles, no sessions.
- The live "database" is a JSON file (`data/document_status.json`); the
  entire SQLAlchemy/Postgres/Alembic layer exists but **was never wired
  in** — the `audit_logs` table has never been written, and one DB module
  would `ImportError` if loaded. No real versioning or immutability.
- Several endpoints return hardcoded mock data (QA review, annex
  list/preview, edit routing); one route is defined twice; workflow state
  is in-memory per gunicorn worker (started on worker A, unpollable from
  worker B).
- Frontend (`qms-ui-v2/`, React 19 + Vite + Tailwind 4 + Zustand): five
  screens; the read screens (dashboard, document library, knowledge search)
  are clean and portable, but the flagship 9-agent creation wizard is
  **partially simulated** — fake `setInterval` progress for two agents,
  client-side `Math.random()` document codes, silent mock fallbacks when AI
  calls fail. Two entire parallel dead implementations ship in the bundle;
  the EN/MK translation catalog is complete (174 keys each) but only 4
  components consume it; the README's test claims describe files that don't
  exist.

### 2.3 Deployment reality on kvm4 (verified live)

An **older build** of qms-api (2026-06-02) is already running on kvm4 at
port 8500 — bundled inside the `/opt/stacks/letta` compose project, with
`LETTA_URL=http://letta:8283` and Gotenberg for PDF. No QMS frontend
container runs. Both apps therefore *already share* the server, the Letta +
Qdrant AI layer, and operational ownership. A third app (`suma-api`, port
8501) also rides that stack — a candidate for the same absorption pattern
later, and a reason to make the platform's module pattern repeatable.

---

## 3. Domain overlap — the join keys already exist

| Dimension | WWF | QMS Creator | Merge move |
|---|---|---|---|
| **SOP codes** | consumed: `tasks.reference_code` is the metric key for per-SOP rollups, ribbon, PDF | minted: registry + auto-numbering (`PREFIX-XX.YY.00`) | `reference_code` becomes a validated pointer into the platform's SOP registry |
| **Departments** | canonical 7 (bilingual, seeded, manager role each) | three overlapping taxonomies, no single source of truth; merges cultivation+production; adds Sanitation/HR/Validation/Research/Premises | WWF's table is canonical; QMS "families" become a document taxonomy, each family mapped to an owning department |
| **Roles** | 13-role access-control model with RLS | documentary only: training-matrix columns (QP/QA/QC/Prod/Maint/Whse/All Staff) + prepared/checked/approved signature chain | training columns map ~1:1 onto WWF roles; the matrix becomes a real join table ("which role must be trained on which SOP"); approval chain maps to QA_MGR → (reviewer) → QP |
| **Letta** | ID-bound function bindings + 3 planner agents; `GrowFlow_Weekly_Snapshots` source | 13 named GMP agents; `db1_regulatory` + `db2_entity_qms` archives | same server, disjoint namespaces — coexist today; unify under a naming convention; synergy: feed WWF weekly snapshots into the QMS facility archive |
| **Document lifecycle** | 2-state draft→locked, DB-enforced immutability + audit chain | 6-state draft→…→approved→archived, versioned, QP-signed — but zero DB enforcement | keep both lifecycles as separate zone models; give approved SOP versions WWF-style append-only DB immutability |
| **Language** | bilingual end-to-end | bilingual registry + complete catalog, partially wired | platform inherits WWF's working bilingual discipline |

**The one hard constraint — governance.** `docs/SCOPE.md` deliberately
scopes WWF as a **non-GMP planning tool**: "authoritative CAPA, SOP,
validation and qualification records live in the QMS — not here." The QMS
Creator is precisely the authoring side of that boundary. The unified
platform must therefore be **one roof, two zones**:

- **Operations zone** (non-GMP, informational): tasks, weekly reports,
  facility board, analytics, notifications — exactly today's WWF scope.
- **QMS Studio zone** (document authoring): SOP generation, review,
  versioned outputs, registry, training matrix — carrying its own stricter
  lifecycle, and able to grow a validation posture later without dragging
  the ops zone into GxP scope.

Separate tables/schema, separate lifecycle code, an explicit zone label in
the UI, and cross-zone references only by pointer (SOP code) — which is
exactly how WWF already references SOPs today. If the merge blurred this
line (one shared "documents" table for weekly ops reports AND authored
SOPs), the whole platform would inherit the Annex 11 / Part 11 expectations
SCOPE.md §"Why this resolves cleanly" deliberately scoped out.

---

## 4. Options considered

### Option A — keep separate, federate (SSO + links)
One nginx entry, WWF issues JWTs, qms-api verifies them, cross-links in
both navs. *Cheapest; ships in days; leaves every QMS shell defect in
place (JSON persistence, mock endpoints, per-worker state bug, no roles).*
**Verdict: right as the interim step, wrong as the destination.**

### Option B — strangler-fig absorption into the WWF foundation ← RECOMMENDED
Port the QMS engine into the WWF backend as a properly-bounded module;
design real Postgres tables for the registry (with RLS + audit + append-only
approved versions); rebuild the authoring UI as views in the platform shell;
retire qms-api. The "third app" emerges as the re-branded unified platform.
*Preserves everything battle-tested, fixes everything broken, one deployable,
one auth, one audit story.* **Verdict: this is what the evidence supports.**

### Option C — big-bang third codebase from scratch
Rewrite both into a new app. *Discards WWF's tested auth/RLS/audit and two
years of accumulated fixes; months of no shipped value; the canonical
"single worst strategic mistake" (Spolsky).* **Verdict: rejected.**

## 5. Why B — the research evidence (all sources verified by fetch)

1. **Don't rewrite working systems; strangle them.** Fowler's Strangler Fig
   (martinfowler.com/bliki/StranglerFigApplication.html) and Microsoft's
   pattern doc (learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig)
   — with Microsoft's own caveat that small systems can simply be replaced,
   which applies to the QMS *shell* but not to WWF's core. Spolsky's
   "Things You Should Never Do" is the case against rewriting WWF.
2. **Modular monolith is the consensus for one team on one server.**
   Fowler's MonolithFirst; Shopify's modular-monolith engineering write-up;
   InfoQ on Prime Video cutting ~90% cost by consolidating microservices
   into one process; 2025 industry surveys put microservices' break-even
   above ~10 developers. Two FastAPI backends on one VPS for 25 users is
   the "microservice premium" with zero payout.
3. **No micro-frontends / module federation at this scale.** Thoughtworks'
   canonical micro-frontends article, Bitovi, and Feature-Sliced Design all
   put the break-even at multiple independent teams. The documented
   low-coupling interim is hyperlink integration with shared session
   (scs-architecture.org), then port screens route-by-route.
4. **No external IdP at 25 users.** FastAPI's own JWT pattern suffices;
   Keycloak/Authentik are disproportionate (Cerbos comparison). WWF becomes
   the token issuer; qms-api verifies during the interim (HS256 shared
   secret acceptable on one host we fully control; RS256 is a cheap
   upgrade); the question dissolves when the backends merge. QMS has **no
   users to migrate** — nothing exists.
5. **Database: one instance, schema separation first, expand/contract.**
   PostgreSQL schema docs; Fowler's Parallel Change + Evolutionary Database
   Design; Azure's per-domain strangling choreography. At our scale the real
   risk isn't migration downtime (trivial at 25 users) — it's extending
   RLS/audit invariants over the new tables incorrectly, so they're designed
   in from day one, not retrofitted.
6. **Plain-tools monorepo.** Compose + path-filtered GitHub Actions (native
   `paths:`; dorny/paths-filter only if workflows must fan out) + a uv
   workspace if the Python packages need a shared lockfile. No Nx/Turborepo/
   Bazel — they solve team-coordination problems we don't have. The repo is
   already structured this way (`backend/`, `web/`, `qms-creator/`).

---

## 6. Target architecture — "Purely Plant Platform"

```
                     ┌────────────────────────────────────────────┐
                     │        nginx (one host, one entry)         │
                     └──────┬─────────────────────┬───────────────┘
                            │                     │
                 ┌──────────▼──────────┐   ┌──────▼──────────────┐
                 │  Platform PWA (web/)│   │ /qms/* → same shell │
                 │  GrowFlow shell +   │   │  QMS Studio views   │
                 │  zone-labeled nav   │   │  (registry, search, │
                 │                     │   │   SOP wizard)       │
                 └──────────┬──────────┘   └──────┬──────────────┘
                            │      one JWT        │
                 ┌──────────▼─────────────────────▼──────────────┐
                 │      ONE FastAPI backend (backend/app/)       │
                 │  ops routers (today's WWF)  │  qms/ package   │
                 │  tasks·reports·facility·…   │  registry·gen·  │
                 │                             │  rag·training   │
                 └───────┬──────────┬──────────┴───────┬─────────┘
                         │          │                  │
                  wwf_users     wwf_tasks          wwf_qms   ← third DB,
                  (identity)    (ops zone)        (QMS zone)   same instance,
                                                               own alembic
                                                               chain + RLS +
                                                               audit + append-
                                                               only approved
                                                               versions
                         └──────────┴──────────┬───────┘
                                     ┌─────────▼──────────┐
                                     │ shared AI substrate │
                                     │ Letta (namespaced   │
                                     │ agents) · archives  │
                                     │ · Qdrant · Gotenberg│
                                     └─────────────────────┘
```

Concrete decisions embedded in this design:

- **Backend**: the QMS engine modules (`letta_service`, `letta_workflow`,
  `agent_definitions`, `letta_tools`, `docx_engine`, `document_code_service`
  + config YAMLs) port nearly as-is into `backend/app/qms/`; **new thin
  routers** replace the 38-endpoint monolith (the real surface is ~10
  endpoints: registry CRUD, generate/workflow, rag-query, downloads,
  training matrix). WWF auth guards them: authoring = QP + QA_MGR (+ADMIN),
  reading = managers/execs, per SCOPE.md's chain. Workflow state moves to a
  DB table — killing the per-worker bug. The mock endpoints are simply not
  ported; they're rebuilt when their features are (QA review is real in the
  engine — only its HTTP façade was fake).
- **Data**: a third database `wwf_qms` mirroring the users/tasks pattern
  (own alembic chain, own schema file, same CI lockstep, same backup
  machinery): `documents`, `document_versions` (append-only once approved —
  WWF's proven per-command-RLS immutability pattern from weekly_documents),
  `annexes`, `families`, `training_requirements` (role × SOP), audit
  triggers throughout. Seed by importing `document_registry.yaml` + the
  JSON registry + `sops_created/` files. `tasks.reference_code` gains
  optional validation against the registry (pointer semantics preserved).
- **Frontend**: the GrowFlow shell is the platform UI (it holds the mature
  auth/bilingual/PWA machinery and the 25 real users). QMS Studio arrives
  as new views: registry browser and knowledge search first (their React
  counterparts are thin and portable — roughly facility-board-sized work
  each), the authoring wizard last (its React version is partially
  simulated, so it must be *rebuilt against real backend behavior* in any
  scenario — building it once, in the platform shell, is strictly less work
  than fixing it in React and porting later). The imported `qms-ui-v2/`
  stays in-repo as reference until parity, then is archived.
- **Naming/brand**: one login, one nav with zone groups (Operations /
  Management / **QMS Studio** / System), one PWA install. "GrowFlow" can
  remain the ops zone's name; the platform identity ("Purely Plant
  Platform" or the owner's choice) appears at the shell level. This *is*
  the third app the owner asked for — new identity, new capability set —
  built without discarding either working half.
- **Letta**: one server; agents renamed under `pp_ops_*` / `pp_qms_*`
  conventions; WWF's binding admin UI filters by prefix; weekly snapshots
  feed the facility archive (`db2`), giving the SOP generator awareness of
  live operations — the first genuinely *new* capability unification
  unlocks.

## 7. Phased roadmap (each phase ships value; each is reversible)

**Phase 0 — this analysis.** ✅ (this document)

*(Phase 1 in progress since 2026-07-15 — deployed to wwf_mass; prod promotion awaits owner approval. See docs/DEPLOY.md §QMS Studio federation.)*

**Phase 1 — federation interim (1–2 cycles).** Deploy the *imported, newer*
qms-api build behind the WWF nginx at `/qms/api/*`; add WWF-JWT verification
middleware to it (shared secret, one host); retire the standalone API key;
add a zone-labeled "QMS Studio" link in the GrowFlow rail; upgrade the
running June build. *Users get one login and one front door immediately;
nothing is rewritten yet; rollback = remove the nginx block.*

**Phase 2 — engine + data (3–4 cycles).** Create `wwf_qms` DB (alembic
chain, schema file, CI lockstep, backups); port the engine into
`backend/app/qms/` with thin authed routers; import registry + SOP library;
DB-backed workflow state; Letta agent namespacing. Run old and new side by
side until parity (parallel-change), then cut the nginx route. *Rollback =
flip the route back.*

**Phase 3 — QMS Studio UI (3–5 cycles).** Registry browser → knowledge
search → training matrix view → authoring wizard (the long pole, rebuilt
honestly against the real pipeline: metadata → questionnaire → generation
progress → QA review → DOCX). Bilingual from day one via the existing
complete catalog. e2e specs per view, same gate discipline as every WWF
cycle.

**Phase 4 — decommission + brand (1 cycle).** Retire the qms-api container
and `qms-ui-v2` build; archive `qms-creator/` source (provenance stays);
platform naming/branding pass; documentation (SCOPE.md gains the two-zone
statement; DEPLOY.md gains the third DB).

**Later, optional:** absorb `suma-api` by the same pattern; PDF export via
the already-running Gotenberg; SOP-aware automations (e.g., "task references
a superseded SOP version → notify QA") — the cross-zone features that only
exist because the platform is unified.

## 8. Risks & open questions

| Risk | Mitigation |
|---|---|
| GxP scope creep onto the ops zone | the two-zone boundary is structural (separate DB, lifecycle, labels), documented in SCOPE.md from Phase 1 |
| The 9-agent wizard is bigger than it looks (its React version fakes steps) | treat wizard = *new build* in estimates (done above); ship registry/search value first |
| Letta single point of failure grows | it already is one for both apps today; namespacing + the existing 503-degradation patterns; no new coupling added |
| Dept taxonomy reconciliation surprises (3 QMS taxonomies) | families→department mapping table decided with the owner in Phase 2, not hardcoded |
| Registry import fidelity (JSON + YAML + loose files disagree) | Phase 2 includes a reconciliation report before any import is committed |
| CI/repo growth | path-scoped jobs already isolate `backend/`+`web/`; `qms/` additions ride the same backend jobs; no new tooling |

**Owner decisions (confirmed 2026-07-15):**
1. Platform name: **GrowFlow** — the unified platform keeps the existing
   name and brand; no rebrand work.
1a. Same containers, same links: the QMS capability ships inside the
   existing GrowFlow deployment (wwf stacks) at the same URLs.
1b. Test-first gating: every unification phase deploys to wwf_mass only;
   production is promoted per-phase after the owner's additional tests and
   explicit approval.

Remaining open decisions:
2. Confirm the GrowFlow (vanilla-JS PWA) shell as the surviving UI — the
   alternative (migrating the whole platform to React) is a much larger
   separate project and is *not* required by anything in this analysis.
3. Whether the QMS zone should, at some later point, pursue a validated
   (GxP) posture — this affects how formal Phase 2's lifecycle/e-signature
   design should be, but not the architecture above.
4. Whether `suma-api` should be planned into the same platform now or later.

---

*Sources for §5 (all fetched and verified during research): Fowler —
Strangler Fig Application, MonolithFirst, Parallel Change, Evolutionary
Database Design (martinfowler.com); Microsoft Azure Architecture Center —
Strangler Fig Pattern; Spolsky — Things You Should Never Do, Part I;
scs-architecture.org; Thoughtworks/Jackson — Micro Frontends; Bitovi —
micro-frontends break-even; Feature-Sliced Design 2025 micro-frontend
retrospective; Shopify Engineering — Deconstructing the Monolith; InfoQ —
Prime Video serverless-to-monolith consolidation; FastAPI OAuth2/JWT docs;
Auth0 — Signing Algorithms, User Account Linking; Cerbos — Authentik vs
Keycloak; PostgreSQL schema docs; Percona PostgreSQL migration playbook;
Docker Compose docs; dorny/paths-filter; uv workspaces docs.*
