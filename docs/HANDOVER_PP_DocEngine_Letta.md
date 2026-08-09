# HANDOVER — Purely Plant Unified Document Suite · Letta Agents · RAG (v2.0)

**Audience:** the main AI agent (or engineer) taking over the Purely Plant document
creation/formatting system.
**Repo:** `3p4e/ACME_SOP` · **Working branch:** `claude/cannabis-import-sop-docs-uju5fb`
(fully pushed; **draft PR #13** tracks the post-#11 commits — see §7).
**Handover date:** 2026‑08‑08. Live-infra facts carry their own verification dates
(Docker inventory 2026‑07‑15; Letta engine sync + smoke test 2026‑07‑30). Re-verify anything
older than a week before relying on it — recipes for every check are in §9.
**Supersedes:** v1 of this file (commit `2ad7be8`).

> **One-line summary.** A self-contained Python engine — **`pp-document-suite`** — turns bilingual
> **Macedonian | English** Markdown into house-style controlled `.docx` (SOPs, Annexes, records).
> It runs three ways: (1) as a repo CLI, (2) embedded in the **PP Doc Wiz** app (built, not deployed),
> and (3) inside **Letta** stateful agents on the KVM4 server via the tools `build_pp_document` /
> `fetch_pp_document`. This session upgraded the engine's table/form **layout brain** substantially and
> **synced the upgraded engine to the live Letta volume (hash-verified, backed up, smoke-tested)**.
> Content and appearance are strictly separated: the author writes Markdown; the engine owns styling.

**Contents:**
§0 Standing rules · §1 System map · §2 The engine (deep) · §3 Letta server & agents (deep) ·
§4 RAG · §5 This session's work products (AM02.1 moisture thread) · §6 Version-state matrix ·
§7 Git/PR state & compliance gaps · §8 Known issues & environment gotchas · §9 Quick-start recipes ·
§10 Open threads / recommended next steps · §11 Key files index

---

## 0. Standing rules (non-negotiable)

1. **Content ≠ appearance.** The author (you / a model / an agent) decides *what a document says* —
   bilingual, quantified, clause-cited. The **engine** decides *how it looks* — the one house navy
   `#2B547E`, Calibri, the 6 pt floor, the intelligent table layout, the base-template header/footer.
   Never hand-roll styling, never invent colours, never guess widths. Build with the engine, verify
   with `pp_verify.py` (must print `RESULT: PASS`), render, eyeball.
2. **Never fabricate pharmaceutical data** (from `PERSONA.md`/`AGENTS.md`). Extract reference values
   from real source documents; if a value isn't in the source, leave the field blank for an admin —
   never guess. This session applied it twice: the HMA↔DO correlation equation was *computed* from
   the real validation workbook (not typed), and meaningless per-range regressions (r²≈0) were
   labelled diagnostic rather than presented as usable correlations.
3. **Reported figures are DERIVED, never typed.** Statistics come from `pp_data.py`
   (`ols()`, `pearson()`, …) bound to a real dataset.
4. **Secrets:** never commit `secrets.env`/`cookies.txt`; never echo API keys; credentials live in
   env vars (names in §3.6). Never disable TLS verification or unset `HTTPS_PROXY`; don't retry
   org-policy 403/407 denials — report them.
5. **Delivery gate:** any `.docx` that does not verify `RESULT: PASS` is not delivered. Ever.
6. **Reference-company confidentiality** (`PERSONA.md`): DB2 reference material (Nedcann etc.) is
   structural leverage only — **never disclose source company names, stakeholders, or equipment IDs
   in any Purely Plant document.**
7. `AGENTS.md` security rules also require: service_role JWT backend-only, rotate Supabase keys on
   any exposure, prefer fine-grained GitHub PATs, and route LLM calls through Langfuse tracing.

---

## 1. System map

```
                     ┌──────────────────────────── 3p4e/ACME_SOP (repo = MASTER of the engine) ───┐
                     │  pp-document-suite/            TRANS_DIST/          HANDOVER (this file)   │
                     │  ├─ scripts/  ← canonical      ├─ md/ + docx/ (WHSOP_002 suite)            │
                     │  ├─ assets/PP_BASE_TEMPLATE    └─ moisture/  (AM02.1 thread, §5)           │
                     │  └─ integrations/ + Dockerfile + docker-compose.letta.yml (Mode B, unused) │
                     └───────────────┬─────────────────────────────────────────────────────────────┘
                                     │  manual hash-verified sync (§3.7, done 2026-07-30)
   ┌─────────────────────────────────▼───────────────── KVM4 VPS 1231216 · crimson.blaze ─────────┐
   │  docker "letta" stack:  letta :8283  ← engine lives INSIDE on /root/.letta (Mode A)          │
   │    ├─ letta-postgres (pgvector)  ├─ letta-mcp-rust :6507 (MCP bridge → this session's tools) │
   │    ├─ qms-api :8500 (REST front: /api/v1/sop/format, /generate, /document/convert-to-pdf)    │
   │    └─ suma-api :8501                                                                          │
   │  gotenberg :3000 (DOCX→PDF)   qdrant :6333 (SUMA vectors — NOT the Letta RAG store, §4)      │
   │  dockge :5001 (stack UI for /opt/stacks/*)   kvm4-runner   code-server :32771                 │
   └───────────────────────────────────────────────────────────────────────────────────────────────┘
        Letta agents (54): qms_docx_formatter · pharma_docx_formatter · pp_annex_* fleet ·
        qms_pipeline_orchestrator (chain: sop_expert → gmp_auditor → docx_formatter) ·
        gmp_rag_agent · eu_gmp_compliance_expert · qms_sop_expert · … (§3.4)
        Tools: build_pp_document / fetch_pp_document (§3.3) · shared memory: pp_house_rules (§3.5)
        RAG: 9 Letta sources + 30 archives, ALL pgvector-native (§4)
```

---

## 2. The engine — `pp-document-suite` (v1.6.2 + session upgrades)

Pure Python (`python-docx` + `lxml`). No API key, no internet, no specific IDE. Python 3.9+.

### 2.1 Modules & canonical files (with current hashes)

| File (under `pp-document-suite/scripts/`) | sha256[:8] | Role |
|---|---|---|
| `build_from_md.py` | `a8a35700` | bilingual-Markdown → `.docx` adapter (parser + emitters; carries form-packing *geometry* but no visual tokens — colours/fonts come only from `pp_theme`/`pp_report`) |
| `pp_report.py` | `1be84f35` | reports/records engine **and the table-layout brain `fixed()`**; forms, equations, status grids |
| `pp_format.py` | `1d54edab` | SOP (two-column) + Annex (inline) shells; base-template loading; page geometry |
| `pp_verify.py` | `a2060978` | QC gate → prints `RESULT: PASS`/`FAIL` (font floor, bilingual check, fidelity) |
| `pp_data.py` | — | dataset binding + statistics (`ols()` returns a **dict** `{slope,intercept,r,r2}`, not a tuple) |
| `pp_charts.py` | — | matplotlib figures (optional; matplotlib currently missing in the cloud env) |
| `pp_theme.py` | — | canonical tokens: navy `#2B547E`, labels `#EDF2F7`, zebra `#F7FAFC`, 6 pt floor |
| `assets/PP_BASE_TEMPLATE.docx` | — | mandatory logo header + "Page X of Y" footer + A4 geometry |

⚠️ **Stale duplicate:** repo-root `scripts/build_from_md.py` (`0aeb5942`, 8,544 B) is an **outdated
shim** predating all session upgrades. Never invoke it; edit/run only the
`pp-document-suite/scripts/` copy. (Recommended cleanup: delete the shim or replace it with a
two-line forwarder — see §10.)

⚠️ **No current skill zip exists.** The zips handed out earlier in the session
(`pp-document-suite-v1.6.2.zip`, `pp-doc-wiz-app-v1.0.zip`) predate the upgrades **and are no longer
in the repo** (`.gitignore` covers `pp-document-suite-*.zip`; the untracked files were lost to a
container reset). Any copy of those zips in circulation is outdated — build a fresh zip from
`pp-document-suite/` before distributing the skill (§10).

### 2.2 Bilingual Markdown grammar (complete input reference)

```
<!--HEADERDATA
mk_title: …                       en_title: …
code: AM02.1-R01                  version: 01
doctype: SOP | ANNEX | FORM | LOG | CHECKLIST      (SOP → two-column build; else annex build)
parent: AM02.1                    supersedes: …    orient: portrait | landscape
-->
# 1. ЦЕЛ | PURPOSE                → SOP: section row · Annex: navy #2B547E banner
## 1.1 Наслов | Subtitle          → subsection row / label sub-bar
Реченица. ||| Sentence.            → bilingual body paragraph (MK ||| EN)
- Точка ||| Bullet                 → bullet
[[TABLE]] … [[/TABLE]]             → row 1 = navy header, rest zebra; cells use MK~~EN; cols split by |||
[[FORM]] Поле ||| Field ||| _      → label|value form, one field per row; `_` = blank write-in cell
[[FORM:grid]] … [[/FORM]]          → NEW: content-packed form — as many fields per row as fit (§2.3)
[[PAGEBREAK]]  (or [[NEWPAGE]])    → NEW: hard page break (annex build)
```
Separators: `|||` = MK|EN split (body, form fields, table columns) · `~~` = MK~~EN inside one table
cell · a `[[FORM]]`/`[[TABLE]]` block of `☐ option` items (≥2 options, ≤2 rows) becomes a compact
`status_grid` checkbox grid. Values inside form fields carry MK/EN as `"MK | EN"`.

### 2.3 The layout brain — what changed this session and how it now works

All appearance decisions live in `pp_report.fixed()` (tables) and `build_from_md.emit_form()`
(forms). Six upgrades were made this session (commits `9d078c8`, `72d2b53`, `aaef395`, `dbccf82`,
`78965da`, `d46d78e`); **default behavior of old inputs is unchanged — everything is additive**:

1. **Data-driven compression in `fixed()`** (`pp_report.py`). When a data table would overflow the
   page, each column is floored to `max(widest DATA cell, header's longest word)` — **data never
   wraps; headers wrap instead** — and the spare width goes preferentially to the columns with the
   longest headers. Previously headers stole width and squeezed data onto two lines.
2. **Word-boundary entry-column matching** (`pp_report.py`, `_ENTRY_TARGETS`). Hand-writing columns
   (Потпис/Signature 3.8 cm, Датум/Date 2.6 cm, Име/Name/Позиција 5.2 cm) are detected by keyword —
   now with `re.search(r'\b'+kw)` so `'име'` no longer false-matches inside `'примерок'` (Sample ID).
   That bug once forced a 5.2 cm "name" width onto the Sample-ID column and wrecked a whole table.
3. **Form label columns size to the longer of MK/EN**, not their concatenation (bilingual labels
   stack on two lines) — roughly halves label columns.
4. **Bulk form values** (> 110 chars, e.g. a provenance note) render as a **full-width block**
   (bold label heading + justified paragraph spanning the page) instead of squeezing into the value
   column; bulk rows are excluded from label-column sizing.
5. **`[[FORM:grid]]` content-packed forms** (`emit_form`, grid branch). Per-field measurement:
   label width = own text, floored to its longest word (never breaks mid-word, capped 5.8 cm);
   value width = own text (blank write-ins get `VMIN = 2.6 cm`); fields pack greedily left-to-right,
   as many per row as genuinely fit `PAGE_W`; too-wide fields span their row; bulk fields become
   full-width blocks; each packed row is its own table with exact widths via `pr._apply_widths()`.
   Result seen in AM02.1-R01: §1 form 6 rows → 4, §2 form 5 rows → 4 (r and r² side by side).
6. **Landscape-aware page width** (`build_annex`). `PAGE_W` = 18.46 cm portrait / **27.16 cm
   landscape** (base-template 1.27 cm margins); previously landscape pages used only portrait width.
   Plus the `[[PAGEBREAK]]` token. `PAGE_W` is restored to 18.46 after each annex build.

### 2.4 The one command loop (+ render fallbacks)

```bash
pip install python-docx lxml                       # (openpyxl for xlsx parsing; matplotlib for charts)
python3 pp-document-suite/scripts/build_from_md.py  src.md  out.docx
python3 pp-document-suite/scripts/pp_verify.py      out.docx          # → RESULT: PASS  (hard gate)
soffice --headless --convert-to pdf --outdir <dir> out.docx           # render
pdftoppm -png -r 150 out.pdf page                                     # rasterize → eyeball page-*.png
```
Render fallbacks, in order of preference when LibreOffice misbehaves (see §8):
Gotenberg on KVM4 (`:3000`, or via qms-api `/api/v1/document/convert-to-pdf`) → Word on the user's
machine → **Tectonic LaTeX** (a self-contained ~37 MB binary; this session downloaded it to `.tec/`
— gitignored, local only — and used it with `fontspec` + **Liberation Serif** for Cyrillic; the
`.tex` sources in `TRANS_DIST/moisture/` compile with XeLaTeX/Tectonic).

### 2.5 SKILL routing (from `SKILL.md` — the master spec)

Two axes before doing anything: **TYPE** (SOP → 9-section two-column; Annex → form/log/template/
checklist inline; Annex if code contains `_A`) × **MODE** (A: develop content via the pre-populated
questionnaire method; B: format approved content; C: reformat arbitrary drafted text). Mandatory SOP
structure: 1 ЦЕЛ · 2 ПОДРАЧЈЕ (2.1/2.2/2.3) · 3 ОДГОВОРНОСТИ · 4 РЕФЕРЕНТНИ ДОКУМЕНТИ ·
5 ДЕФИНИЦИИ (5.1/5.2) · 6 ПОСТАПКА (ALL procedural content; training & deviation as final 6.x) ·
7 ЗАПИСИ · 8 ПОВРЗАНИ ДОКУМЕНТИ · 9 РЕВИЗИЈА. House language: MK first, decimal commas in MK,
**never translate abbreviations** (QA, QC, QP, GMP, CoA, SOP, HPLC, LoD, pH …), never duplicate
symbols/numbering. Full references: `references/GUIDE_bilingual_markdown.md` (≡ root
`PP_UNIFIED_DOCX_GUIDE.md`), `references/formatting_specs.md`, `references/questionnaire_library.md`,
`references/regulatory_and_context.md`.

---

## 3. Letta server & agents (KVM4) — deep

Letta REST surface: in-repo `openapi_letta.json` (Letta API v0.16.8). Base URL `$LETTA_UI`
(`https://ui.srv1231216.hstgr.cloud/`), bearer `$LETTA_API_KEY`.

### 3.1 Infrastructure (Docker inventory, verified live 2026‑07‑15 via Hostinger API)

VPS `1231216` / `crimson.blaze`, Ubuntu 24.04 with Docker + Traefik. 15 compose projects:

| Project | Containers (image · port) | Relevance |
|---|---|---|
| **letta** | `letta` (letta/letta:latest · :8283) · `letta-postgres` (pgvector/pgvector:pg15) · `letta-mcp-rust` (:6507) · `qms-api` (qms-api:latest · :8500) · `suma-api` (:8501) | **the core** — Letta server hosts the engine (Mode A); qms-api is the REST front |
| **gotenberg** | gotenberg/gotenberg:8 · :3000 | DOCX→PDF for the doc pipeline |
| **qdrant** | qdrant/qdrant:latest · :6333–6334 | vector DB for the **SUMA Platform** (`PERSONA.md`) — **NOT the Letta RAG store**; all 30 Letta archives are `vector_db_provider: "native"` = pgvector (§4) |
| **traefik** | traefik:latest | TLS/routing for `*.srv1231216.hstgr.cloud` |
| **dockge** | louislam/dockge:1 · :5001 | compose-stack manager UI for `/opt/stacks/*` |
| kvm4-runner · visual-studio-code-server (:32771) · voxcpm (:32770) · agent-zero (:32769) · zoneminder (:8081, +mariadb) | — | unrelated utilities |
| wwf_app (8 containers) · wwf_mass (4) | weekly_weed_flow backend/frontend/scheduler + postgres ×5 | separate product (Weekly Weed Flow) — not part of the doc system |
| 9router · deepseek-tui · open-webui | — | **stopped** |

Read the live inventory any time (no SSH needed):
`curl -s -H "Authorization: Bearer $HOSTINGER_API_KEY" https://developers.hostinger.com/api/vps/v1/virtual-machines/1231216/docker`

### 3.2 Engine deployment shape — Mode A (live), Mode B (available)

**Mode A (LIVE):** the engine is installed inside the `letta` container on its persistent
`/root/.letta` volume (survives container recreation; an *image rebuild* only clears `pp-libs`):
- `/root/.letta/pp-document-suite/` — engine (scripts + `assets/PP_BASE_TEMPLATE.docx`)
- `/root/.letta/pp-libs/` — `python-docx` + `lxml` (tool adds to `sys.path`; reinstall after image
  rebuild: `pip install --target=/root/.letta/pp-libs python-docx lxml`)
- `/root/.letta/pp-out/` — generated `.docx`
- `/root/.letta/pp-stage/` — chunked-transfer staging area used by the sync procedure (§3.7)

**Mode B (NOT deployed):** dedicated container `pp-document-suite:8600`
(`Dockerfile` + `docker-compose.letta.yml` + `integrations/service.py`: `POST /build`, `/build.docx`,
`/build.pdf`, `GET /health`). Cleaner isolation, survives image rebuilds; recommended long-term (§10).

### 3.3 Registered Letta tools (confirmed live)

| Tool | ID | Behavior |
|---|---|---|
| `build_pp_document(markdown, out_name)` | `tool-c4921b81-46b1-4c69-bde3-12c42429fb2f` | writes markdown to a temp file → `build_from_md.main()` (with `importlib.reload`, so **engine file changes take effect without restarting Letta**) → runs `pp_verify` → returns JSON `{ok, verify, path, bytes}`; `ok` requires `RESULT: PASS`; output under `/root/.letta/pp-out/` |
| `fetch_pp_document(path)` | `tool-d88e8e21-eb75-4524-b0e0-20d04af5b8a9` | returns a produced `.docx` as base64 for download/attachment |

Tags: `purely-plant`, `docx`, `pp-document-suite`. Attached to the document agents below.

### 3.4 Agent fleet (54 agents live; IDs verified 2026‑07‑15)

**Document-production core (the ones this project drives):**

| Agent | ID | Model | Role |
|---|---|---|---|
| `qms_docx_formatter` | `agent-762996ac-d553-4c80-aed5-e644f17f5636` | deepseek-v4-flash | primary DOCX formatter; terminal stage of the orchestrator chain; default chat target of PP Doc Wiz; calls `build_pp_document`; carries exactly one core-memory block: `pp_house_rules`. ⚠️ its description hardcodes Gotenberg at `http://143.244.132.80:3000` — a **stale IP** (current KVM4 host is `72.60.35.12` per `PERSONA.md`); fix per §10 |
| `pharma_docx_formatter` | `agent-4aee57f2-479f-46df-805a-be74e0364060` | deepseek-v4-flash | GMP DOCX formatter (second formatter) |
| `qms_pipeline_orchestrator` | `agent-3f3de9f1-3bc4-46a8-83d9-3cf60c0076ee` | deepseek-v4-pro | coordinates the SOP chain (verified from its live config): **request → `qms_sop_expert` → `qms_gmp_auditor` → `qms_docx_formatter`**. Note: the chain lives only in its *description* — the system prompt is Letta's generic stock prompt and `tool_rules` is empty, so nothing enforces the sequencing |
| `qms_sop_expert` | `agent-2ddd47a5-…` | deepseek-v4-pro | SOP content author in the chain; shares `pp_house_rules`; references a 16-section equipment-SOP template (see the 9-vs-16-section doc conflict, §10) |
| `qms_gmp_auditor` | (id not captured) | — | GMP validation stage of the chain |
| `pp_annex_orchestrator` | `agent-f2178ef6-a2b4-4e03-be0f-851ab22d5587` | deepseek-v4-pro | leads the 5-agent annex fleet |
| `pp_annex_translator` | `agent-7ef8ce45-e68f-464f-ab47-257a57ace659` | deepseek-v4-flash | MK⇄EN for annexes |
| `pp_annex_body_formatter` | `agent-ae59502a-3cbf-43bc-a02d-817d88656088` | deepseek-v4-pro | annex body formatting |
| `pp_annex_table_specialist` | `agent-f33a0663-3038-4913-bc9a-908e367b73fa` | deepseek-v4-pro | annex tables |
| `pp_annex_auditor` | `agent-335668ac-9ad1-4d2b-8bad-95673e69a5b4` | deepseek-v4-pro | annex QA gate |

**Knowledge / RAG / compliance (see §4):**

| Agent | ID | Model | Role |
|---|---|---|---|
| `gmp_rag_agent` | `agent-e15c8ea4-dc65-439f-9653-ebb9c872b069` | deepseek-v4-pro | "GMP Knowledge Base RAG Agent. Query Google Drive documents via localhost:8787 for regulatory …" |
| `eu_gmp_compliance_expert` | `agent-36d85817-fb2c-4f89-8e82-21213030d2e8` | deepseek-v4-pro | EU GMP Annexes 1–19 / PIC/S expertise |
| `fastapi_letta_qms_patterns` | `agent-f7352bb3-7b28-4485-8bbb-b906c29d6c9b` | deepseek-v4-pro | API/integration design patterns for the QMS stack |

**Other fleets on the same server (not part of the doc system — don't touch without reason):**
CoA/CoQ pipeline agents (CoA Ingestion, Parameter Extraction, Compliance Analysis, Specification
Advisor, CoQ Assembly, Report Generation, Search Assistant), `VariationF*` design-system agents,
`ars_*` SOP-review skill agents, `wwf_*`/planner agents (Weekly Weed Flow product), QC agents
(`imb_qc_coa_agent`, `pq1_water_qc_agent`, `ecoa-qc-agent`, `equipment_manuals_agent`),
`warehouse_quarantine_ocr_agent`, code/security/design reviewers.

### 3.5 Shared memory — `pp_house_rules` (verified live, full text recovered)

Block **`block-eed2112b-a1b4-4593-b607-9c16444fe254`**, 1,955 chars, limit 100,000, writable,
description "Mandatory Purely Plant house-style rules for all pp-document-suite documents."
**Shared by 9 agents:** `qms_docx_formatter`, `pharma_docx_formatter`, `qms_pipeline_orchestrator`,
`qms_sop_expert`, and the five `pp_annex_*` agents. **`gmp_rag_agent` does NOT carry it** (correct —
it's a retrieval agent, not a formatter). Content (condensed; full text retrievable via
`letta_agent_advanced` op `context` — the bridge's `get_block` truncates at ~500 chars):
engine + `build_pp_document` contract & PASS gate · MK-first bilingual rules + never-translate
abbreviation list · the one navy `#2B547E` + full palette · Calibri + 6 pt floor · 9-section SOP
layout spec · annex inline spec incl. entry-column purpose sizes (Name ~5.2 / Date ~2.6 /
Signature ~3.8 cm) · header/footer mandate · precision & ALCOA+ ("reformatting is ADDITIVE —
never summarise/omit/drop detail").

⚠️ **Known error in the block text:** it says the engine lives at `/opt/pp-document-suite`; the real
Mode-A install is `/root/.letta/pp-document-suite` (the tool's `PP_SUITE_DIR` default). Harmless to
tool execution (the tool reads the env default, not the block) but misleading to agents — fix per §10.

**Division of labour:** the Letta agent owns CONTENT (reasoning over memory, house codes, prior
SOPs, the RAG corpus); the engine owns APPEARANCE. Never let an agent emit colours/fonts/widths —
it emits Markdown; `build_pp_document` renders the house style.

### 3.6 Access methods & credentials (env-var NAMES only — never commit values)

| Var | Purpose |
|---|---|
| `LETTA_UI` | Letta base URL (`https://ui.srv1231216.hstgr.cloud/`) |
| `LETTA_API_KEY` | bearer for Letta REST `/v1/...` |
| `LETTA_SERVER_PASS` | Letta server password |
| `HOSTINGER_API_KEY` | Hostinger VPS API (incl. the live Docker-inventory endpoint, §3.1) |
| `KVM4_API_TOKEN`, `KVM4_HOSTNAME`, `KVM4_IPv4/IPv6/REVERSE_DNS` | KVM4 addressing |
| `KVM4_SSH_KEY` | **public** ed25519 key only — **no SSH from the cloud env** (no private key, no ssh binary) |

Three working access paths, in order of reliability:
1. **Direct Letta REST** — `curl -H "Authorization: Bearer $LETTA_API_KEY" "$LETTA_UI/v1/…"`.
   Always works; use it for tool/agent CRUD when the bridge (path 2) chokes.
2. **`Letta_KVM4_MCP` bridge** (`letta-mcp-rust:6507`) — the `mcp__Letta_KVM4_MCP__letta_*` tools.
   Verified quirk list (all reproduced live):
   - `letta_tool_manager list` / `letta_agent_advanced list_tools` fail with `missing field
     'package'` (the bridge's tool struct lacks `pip_requirements[].package` that this Letta version
     emits) → **tool attachments are not enumerable via the bridge**; use direct REST.
   - `letta_memory_unified list_blocks` requires an `agent_id` (no server-wide enumeration), and
     `get_block`/`get_block_by_label` truncate `value` at ~500 chars — get full block text via
     `letta_agent_advanced` op `context` (beware: `context` on a busy agent can return >200 K chars).
   - `letta_source_manager list` reports `attached_agent_count: 0` / `file_count: 0` for every
     source — those aggregates are unreliable; use per-source `list_files` / `list_agents_using`.
     Its advertised `list_folders`/`get_folder_contents` ops are **not implemented** server-side.
   - The agent-get `memory` field can return `[]` even when blocks are attached (cross-check with
     `list_agents_using_block`).
   - `letta_mcp_ops list_servers` → 0: Letta is an MCP *provider* (via the bridge), not a consumer.
   - Internal URL visible in errors: `http://letta:8283`.
   Agent listing/messaging, `run_from_source`, source/memory reads (with the caveats above) work.
   **`run_from_source` recipe** (this is how ad-hoc code runs *inside* the Letta sandbox — probes,
   installs, smoke tests): pass `operation: "run_from_source"`, `tool_args: {…}` (a JSON object,
   required even if empty), and `source_code` = a single Python function that **must have a
   docstring including an `Args:` section describing every parameter** (Letta derives the JSON
   schema from it; missing docs → schema error). The sandbox has: write access to
   `/root/.letta/*`, `curl`, outbound network (github.com reachable), **no git, no GitHub token**.
3. **Hostinger VPS API** — infra-level facts (Docker projects/containers/state/ports) without SSH.

### 3.7 Engine sync procedure (executed 2026‑07‑30 — how to repeat it)

The repo is the engine's master; the Letta volume is a deployment target. This session's sync:

1. **Diff first**: probe the volume's file hashes + feature flags via `run_from_source` (§9 recipe)
   and compare to repo hashes (§2.1). Only `build_from_md.py` and `pp_report.py` differed.
2. **Transfer**: repo is private + sandbox has no git/token, and paste services are proxy-blocked —
   so files went as **gzip+base64 through `run_from_source`**, with a **SHA-256 gate at the
   destination**: decode → hash → compare to the expected repo hash → **only then** back up the old
   file (`<name>.bak.<timestamp>`) and overwrite → re-hash the installed file. A one-shot transfer
   of the 14 KB gz+b64 payload succeeded; the 32 KB one corrupted in transit (caught by the gate,
   **not installed**) and was re-sent as **3 hash-verified chunks** staged in `/root/.letta/pp-stage/`
   and reassembled. Never bypass the hash gate.
3. **Result** (verified): `build_from_md.py` → `a8a35700` (backup `build_from_md.py.bak.20260730133754`),
   `pp_report.py` → `1be84f35` (backup `pp_report.py.bak.20260730135516`). All 6 feature flags true.
4. **Smoke test on the volume**: built a landscape `[[FORM:grid]]`+`[[PAGEBREAK]]` doc through the
   volume engine → `WROTE … (ANNEX)`, `pp_verify` → `RESULT: PASS`. Because `build_pp_document`
   reloads modules per call, **no Letta restart was needed**.
5. **Rollback**: restore the `.bak.*` files via the same `run_from_source` mechanism.
6. **After a Letta image rebuild**: reinstall `pp-libs` (§3.2) and re-run the volume probe; the
   volume files themselves persist.

---

## 4. RAG (retrieval-augmented generation) layer — audited live 2026‑08‑08

**Architecture in one paragraph.** Two RAG mechanisms coexist in Letta: **sources** (file-backed
corpora with per-source embedding config; 9 exist) and **archives/passages** (agent-scoped vector
stores; 30 exist). **Every archive is `vector_db_provider: "native"` → the RAG store is pgvector
inside `letta-postgres`. Qdrant is NOT part of this pipeline** (it serves the separate SUMA
Platform). Flow: **RAG corpus → content agents → bilingual Markdown → `build_pp_document` →
house-style `.docx`**. RAG feeds *content*; it never touches *formatting*.

### 4.1 The 9 Letta sources (IDs verified; all `text-embedding-3-small` 1536-dim unless noted)

| Source | ID | Chunk | Files | Contents |
|---|---|---|---|---|
| `DB1_REGULATORY` | `source-0b9a8f2e-…` | 300 | 3 | EudraLex Vol. 4, ICH, WHO TRS, EMA, MK law 106/2007, HBEL, CTD-herbal. ⚠️ attached only to `gf_reg_checker` — **not** to `gmp_rag_agent` (which got DB1 content as archival passages instead, §4.2) |
| `DB2_GMP_PRO` | `source-2cc09182-…` | **512** | 0 | Nedcann historical GMP (N_SOURCE), Memmert IQ-OQ-PQ (EQIP_SOUR), current PP SOPs (H_SOURCE), external-lab CoAs/methods (Y_SOURCE); Drive folder `1qtrGnHKIckJ90Bi6BY-pwPkles9AfJxs`. ⚠️ Confidentiality rule applies (§0.6) |
| `DB3_PP_CURRENT_unified` | `source-89b764c4-…` | 300 | **25** | approved QCSOPs/QCWIs/QCT, env-monitoring reports, RO-water system docs, packaging, instrumentation, **and the peer-reviewed Nikolov 2025 HMA-vs-DO moisture-bias paper (IOSR J. Pharmacy 15(4) 33–38, 2 files)** — prior art directly relevant to the §5 correlation work. Ingested 2026‑06‑18, all 25 files `Completed` |
| `PQ1 Water Testing Results Report` | `source-dd320361-…` | 300 | 0 | PQ1 water testing, RO system `EQP-PPS002` |
| `ImB_QC_COAs` | `source-271bc3be-…` | 300 | 0 | in-process/bulk/FP CoAs, Drive `16oMK_j0FUusjveV61B5rxWi6Sl5kQsn5`; records the **voyage-3 → openai migration** (Letta lacks a first-class voyage provider; `VOYAGEAI_API_KEY` absent from the container) |
| `Equipment_Manuals_PP` | `source-08e8b594-…` | 300 | 0 | Memmert manuals |
| `CoA_Individual_Split` | `source-aa59e5ef-…` | 300 | 0 | CoA PDFs split from merged scans |
| `Superior_Primary_Packaging` | `source-930d9d33-…` | 300 | 0 | supplier qualification, 400 g bulk primary packaging |
| `GrowFlow_Weekly_Snapshots` | `source-7ad49834-…` | 300 | 0 | weekly digests from GrowFlow Postgres (WWF product, not doc-engine) |

### 4.2 `gmp_rag_agent` — the retrieval workhorse (`agent-e15c8ea4-dc65-439f-9653-ebb9c872b069`)

- deepseek-v4-pro, 64 K context; embedding `text-embedding-3-small` 1536d.
- **Attached sources: `DB3_PP_CURRENT_unified` + `DB2_GMP_PRO`** (not DB1).
- **Archival memory: 547+ passages** (ingested 2026‑05‑17) tagged
  `[REG_DB | source | filename | chunk X/Y]` covering EudraLex Vol. 4 Ch. 1–9 + Annexes
  7/8/11/15/16/17/19/21, EMA (HBEL, cross-contamination, cleaning validation, CTD herbal), ICH
  Q8/Q9/Q10, WHO GACP + Annex 9, MK GMP Pravilnik, ALCOA++/data-integrity/balance guides.
- **Operational rule baked into its prompt:** with `archival_memory_search`, pass ONLY the query —
  do NOT use the `tags` parameter (passages aren't tagged that way); answers must cite the
  `[REG_DB | …]` header.
- Description confirms the **`localhost:8787`** Google-Drive query sidecar. ⚠️ Nothing in the repo
  or Docker inventory defines what runs on 8787 — "what is it, is it still up" is an open item (§10).
- Carries **no tools and no `pp_house_rules`** (it retrieves; formatters format).

### 4.3 Embedding-stack facts (matter when you add corpora)

28 of 30 archives use `openai/text-embedding-3-small` (1536d, chunk 300). Two outliers cannot share
passages with the rest (dimension mismatch): `pq1_water_qc_agent` → `voyage-3-large` (1024d, chunk
512) and `ecoa-qc-agent` → `letta-free` (huggingface `embeddings.memgpt.ai`, 1024d). Use
`text-embedding-3-small` for anything new unless you have a reason and a migration plan.

**Related history:** PR #1 ("warehouse quarantine labels with OCR and Letta RAG agent") started the
RAG line; `warehouse_quarantine_ocr_agent` still exists. `PERSONA.md` records the original scale-up:
"77 files … → 547 chunks each into 4 Letta agents" on `text-embedding-3-small`.

---

## 5. This session's work products — the AM02.1 moisture thread

The session's applied storyline; every number below is derived from real sources (rule §0.2).

### 5.1 The record — `AM02.1-R01` (Moisture Content Determination Record)

Built from a **handwritten worksheet** (photo via the user's Drive; file `1784032990197.jpg` in the
"CowoRK" folder `145ppxBmNS5_id-ETq-Xx1LK3nH3PmV69`): 16 halogen-moisture-analyzer (HMA, method
AM02.1) determinations on two analyzers (**Eq. ID 067 & 041**), each row = Sample ID, m₀, m₁, %MC,
start–end time. Every %MC was independently recomputed from m₀/m₁ (100 % match) before building.
Corrections made on user instruction: A4 **portrait** (not landscape); three OCR-misread sample IDs
fixed (`FB012602`, `GP0824_02`, `HPA1024_01`). Structure: §1 record info (`[[FORM:grid]]`) ·
§2 correlation equation (`[[FORM:grid]]`) · §3 results table (8 columns incl. **Проектирана DO %**) ·
§4 sign-off. Date on record: 14.07.2026. Product/Analyst fields intentionally blank (rule §0.2).

### 5.2 The correlation study — dataset provenance & the numbers

Source: the user's Drive → folder `1MZYJOs9LKplBh_McrPj8YzSLCDP5VJhE` → subfolder **AM_VALALL**
(`1CPXWG20Uh77ACZt_YNz_5k26I2IC9HmZ`) → workbook **`PPlant MV_SAM (1).xlsx`**
(`1Ab0yr4Y503ieuHMx6wlV_l_sztAsLkoS`), parsed cell-level with openpyxl (`data_only=True`).
Structure: 5 ranges R1–R5, each a sheet pair (`Rn` raw + `Rn int & cor` paired x=%MCHMA / y=%MCDO).
**Data caveats found & handled:** `R5 int & cor` is all `#REF!` (used the R5 base sheet cols D/M
instead); R3 has two erroneous `0` DO values (excluded); a trailing `231225_IPCR_LoD DO` section has
all-zero HMA (ignored). A sibling workbook `PPlant MV a02.2.xlsx` (`1nP06mR6CndNGdTc6roWyoMefKNTjuira`)
exists, **never opened** — potential extra data.

Per-range replicate facts (x = HMA):

| Range | HMA min–max | N(HMA) | mean HMA | mean DO | N(DO valid) | within-range OLS (diagnostic only) | r² |
|---|---|---|---|---|---|---|---|
| R5 | 3.00 – 4.33 | 10 | 3.213 | 2.136 | 10 | DO = −0.1841·HMA + 2.727 | 0.116 |
| R4 | 8.00 – 9.00 | 10 | 8.550 | 6.369 | 10 | DO = −0.0066·HMA + 6.426 | 0.000 |
| R3 | 18.40 – 20.40 | 10 | 19.510 | 18.045 | 8 | DO = −0.0115·HMA + 18.271 | 0.001 |
| R2 | 36.70 – 38.80 | 11 | 37.836 | 35.467 | 9 | DO = 0.1318·HMA + 30.463 | 0.009 |
| R1 | 58.50 – 68.10 | 12 | 62.642 | 61.421 | 8 | DO = 0.0208·HMA + 60.116 | 0.017 |

- **THE equation (all ranges, authoritative for projection)** — OLS on the 5 level means via
  `pp_data.ols()`: **DO % = 1,00095 × HMA % − 1,68774** · r = 0,9997 · r² = 0,9994.
  Inverse: HMA % = (DO % + 1,68774) / 1,00095.
- **Within-range r² ≈ 0 is range restriction**, not error: one narrow moisture level has no spread
  for a correlation to appear — the variation is measurement scatter. Those per-range fits are
  documented as DIAGNOSTIC and excluded from the final deliverables at the user's request.
- **Piecewise band equations** (between adjacent level means; produced in v02, later dropped from
  the final docs): 3.21–8.55: `0.79327x−0.41324` · 8.55–19.51: `1.06533x−2.73939` ·
  19.51–37.84: `0.95066x−0.50206` · 37.84–62.64: `1.04630x−4.12077`.
- **Verified range by replicate extremes: 3,0 – 68,1 % HMA** (the user's chosen definition;
  supersedes the earlier level-mean span 3,2–62,6). Projected DO at the ends: 1,32 % / 66,48 %.
- Conversion values: DO rounded half-up to 2 dp with `Decimal`; because slope > 1 a few DO steps are
  0,11 at rounding boundaries — correct, not a bug. Spot anchors: 10,0→8,32 · 14,0→12,33 ·
  45,0→43,36 · 62,6→60,97 · 68,1→66,48.
- **Prior art in the RAG corpus:** `DB3_PP_CURRENT_unified` contains the peer-reviewed **Nikolov
  2025 HMA-vs-DO moisture-bias paper** (IOSR J. Pharmacy 15(4) 33–38) — directly on this topic.
  If the correlation work is ever extended or challenged, query `gmp_rag_agent` for it first.

### 5.3 Final deliverables in `TRANS_DIST/moisture/` (all verify `RESULT: PASS`)

| File | What it is |
|---|---|
| `AM02.1-R01.md` + `_Moisture_Record.docx/.pdf` | the 16-sample record (v01, portrait, grid forms, projected-DO column) |
| `AM02.1-R01-A1.md` + `_Correlation_Equation.docx` | **equation-only doc** (v04, landscape): the overall equation + inverse + r/r² + validity range + a term-by-term explanation table |
| `AM02.1-R01-A2.md` + `_Conversion_Table.docx` | **HMA→DO lookup** (landscape): 3,0–68,1 % in 0,1 % steps = **652 values**, decade-aligned rows, 10 HMA\|DO pairs per row |
| `AM02.1_Correlation_Equation.tex/.pdf` | LaTeX rendition (equation at max size, placeholders explained) — Tectonic/XeLaTeX, Liberation Serif |
| `AM02.1_HMA_DO_Conversion_Table.tex/.pdf` | LaTeX rendition of the table, HMA columns blue / DO columns green |

⚠️ The A1/A2 **DOCX have no rendered PDFs yet** (LibreOffice docx-import broke in the reset
container, §8). The LaTeX PDFs show identical content. Regenerate suite PDFs when a renderer is
available (§10).

---

## 6. Version-state matrix (who has which engine)

| Location | build_from_md.py | pp_report.py | State |
|---|---|---|---|
| **Repo `pp-document-suite/scripts/`** | `a8a35700` | `1be84f35` | ✅ **MASTER** — all session upgrades |
| **Letta volume** `/root/.letta/pp-document-suite/scripts/` | `a8a35700` | `1be84f35` | ✅ synced 2026‑07‑30, smoke-tested PASS; backups `.bak.20260730*` on volume |
| Repo root `scripts/build_from_md.py` (shim) | `0aeb5942` | n/a | ❌ **STALE** — do not use (§10 cleanup) |
| Skill zips in circulation (v1.6.2 / doc-wiz v1.0) | pre-upgrade | pre-upgrade | ❌ outdated **and no longer in the repo** (gitignored, lost to reset) — rebuild before distributing (§10) |
| PP Doc Wiz container | — | — | not deployed; embeds engine at build time, so build fresh when deploying |

`pp_format.py` (`1d54edab`) and `pp_verify.py` (`a2060978`) are identical everywhere.

---

## 7. Git / PR state & compliance gaps

- Branch `claude/cannabis-import-sop-docs-uju5fb`, fully pushed. **PR #11 (this branch) was merged
  mid-session; the post-merge commits are tracked by draft PR #13**
  (https://github.com/3p4e/ACME_SOP/pull/13, opened 2026‑08‑08 — undraft/merge when reviewed; no CI
  is configured on the repo). Other open PRs (#12, #5, #4, #3, #2, #1) belong to other threads.
- Session commit arc (oldest→newest): `b68a3e3` original AM02.1 record → `c7cd1e1` portrait fix →
  `88accfe` sample-ID fixes → `dbe4114` correlation column → `9d078c8` layout-brain fix → `72d2b53`
  label sizing → `aaef395` bulk blocks → `dbccf82` FORM:grid → `78965da` content-aware packing →
  `2ad7be8` handover v1 → `d46d78e` lookup table + landscape width → `66b4aa4` decade alignment →
  `27b36c4` replicate-range v02 → `d5eff2e` per-range v03 → `e25434f` LaTeX pair → `9ba8d2b` A1/A2
  split → `6dbf898`+ this handover v2.
- **Unregistered document codes:** `AM02.1-R01`, `-A1`, `-A2` appear in **neither**
  `QMS_TRACKING.md` **nor** `QC_QMS_Document_Code_Registry.md` (verified 2026‑08‑08). The AM02.1
  codes were provisional from the start — confirm real controlled codes with the user, then
  register (§10).

---

## 8. Known issues & environment gotchas (cloud Claude-Code environment)

1. **`SendUserFile` (in-chat attachment) returns HTTP 403** — persisted the entire session.
   Delivery channel that works: commit + GitHub links
   (`https://github.com/3p4e/ACME_SOP/{blob|raw}/<branch>/<path>`; repo is private, so links work
   for the logged-in user's browser but NOT for anonymous curl/other machines).
2. **Container resets are destructive and silent**: they wipe `/tmp` (scratchpad), pip packages
   (`python-docx`, `openpyxl`, `matplotlib`), `poppler-utils` (`pdftoppm`), and revert the git
   checkout to a stale clone. After any reset: `pip install python-docx lxml openpyxl`, re-fetch the
   branch (`git fetch origin <branch> && git reset --hard origin/<branch>` — work was always safe on
   origin), and re-check tool availability. Current state (2026‑08‑08): docx+openpyxl OK,
   **matplotlib MISSING, pdftoppm MISSING**.
3. **LibreOffice docx→PDF broke after one reset** (fails to load even a trivial docx — filter-level
   breakage, not our files). `soffice` binary exists; conversion may or may not work at any given
   time. Fallbacks in §2.4. This is why A1/A2 PDFs are pending.
4. **MCP-bridge decode bug** (`missing field 'package'`) on Letta tool-listing endpoints — use
   direct REST (§3.6). `run_from_source` functions **must** have full docstrings (incl. `Args:`)
   and a `tool_args` JSON object or the call 400s.
5. **Base64-through-context transfers are expensive and fragile** — a ~14 KB payload survives; a
   ~32 KB one corrupted in transit once. Chunk ≤ ~5 KB with per-chunk SHA when it's unavoidable;
   never install without an end-to-end hash gate. (And never relay whole binary files through model
   context — an earlier attempt burned ~100 K tokens and failed; that lesson is standing.)
6. **Two `build_from_md.py` copies** (§6). Edit only `pp-document-suite/scripts/`.
7. **`.tec/` Tectonic binary is local-only** (gitignored, ~37 MB). Fresh clones must re-download
   (github release `tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz`) to rebuild the `.tex` files.
8. **Word-field artifacts:** native TOC and "Page X of Y" show blank until fields update (`Ctrl+A →
   F9` in Word; `soffice --convert-to pdf` updates them automatically). On Linux the Office
   `MML2OMML.XSL` is absent → equations fall back to text (build still passes).
9. **Letta `run_from_source` sandbox** has no git/GitHub token; repo raw URLs 404 anonymously —
   that's why the sync uses chunked payloads (§3.7).

---

## 9. Quick-start recipes

**Build any document (repo):** write bilingual Markdown per §2.2 (copy
`TRANS_DIST/moisture/AM02.1-R01.md` or `-A2.md` as a template) → §2.4 loop → ship only on PASS.

**Have Letta build it:** message `qms_docx_formatter` (or call the tool directly) via REST:
```bash
curl -s -H "Authorization: Bearer $LETTA_API_KEY" "$LETTA_UI/v1/tools/?name=build_pp_document"
# then send a message to agent-762996ac-… asking it to call build_pp_document with your markdown,
# and fetch bytes with fetch_pp_document(path).
```

**Probe the volume engine (read-only) / smoke-test after any change:** call
`mcp__Letta_KVM4_MCP__letta_tool_manager` with `operation: run_from_source`, `tool_args: {}`, and a
docstring-complete function that reads `/root/.letta/pp-document-suite/scripts/*`, hashes files,
greps feature flags (`FORM:grid`, `PAGEBREAK`, `27.16`, `_form_bulk`, `data_cm`, `re.escape`), or
builds a test doc via `build_from_md.main()` + `pp_verify.main()`. Working examples are in this
session's history (probe: `pp_engine_probe`; sync: `pp_sync`/`pp_stage`; smoke: `pp_smoke`).

**Read KVM4 infra without SSH:** the Hostinger endpoint in §3.1.

**Regenerate the conversion table values** (if the range or equation ever changes):
`Decimal`-based loop, slope `1.00095`, intercept `−1.68774`, `quantize(0.01, ROUND_HALF_UP)`,
tenths as integers (`range(30, 682)`) to avoid float drift; decade-aligned rows = one HMA integer
per row. The generator script pattern is embedded in the git history of `AM02.1-R01-A2.md`.

**Audit the RAG layer (first task if you touch content generation):**
`GET $LETTA_UI/v1/sources/` (direct REST) → list corpora; inspect `gmp_rag_agent` config
(`letta_agent_advanced` op `get`); identify the `:8787` Drive-query service on the host; map qdrant
collections (`curl http://<kvm4>:6333/collections` from a host that can reach it).

---

## 10. Open threads / recommended next steps (prioritized)

1. ~~Open a draft PR~~ **DONE 2026‑08‑08 — draft PR #13** is open for the branch; shepherd it to
   review/merge.
2. **Register the AM02.1 codes** (or replace with real controlled codes from the user) in
   `QMS_TRACKING.md` + `QC_QMS_Document_Code_Registry.md` (§7).
3. **Render A1/A2 PDFs** once a docx renderer works (LibreOffice recovery, Gotenberg on KVM4, or
   user's Word) and commit them next to the DOCX.
4. **Build a fresh skill zip** from the current `pp-document-suite/` (none exists in the repo —
   `.gitignore` excludes `pp-document-suite-*.zip`, and the previously distributed v1.6.2 zip
   predates the upgrades); version-bump (v1.7?) and update `SKILL.md` version +
   `GUIDE_bilingual_markdown.md` with `[[FORM:grid]]`/`[[PAGEBREAK]]` docs (the guide does not
   document them yet).
5. **Retire or forward the stale root shim** `scripts/build_from_md.py` (§6).
6. **Deploy Mode B** (`docker-compose.letta.yml`, service on `:8600` on the letta network) for
   rebuild-proof isolation, then register the REST tool variant (`integrations/letta_register.py`,
   `LETTA_MODE=rest`) — the repo ships everything needed.
7. **Deploy PP Doc Wiz** (`ppdocwiz/`, :8770) if the wizard/chat front-end is wanted; it embeds the
   engine at image build, so building now picks up the upgrades.
8. **Small live-config fixes on Letta** (found in the 2026‑08‑08 audit): (a) correct the
   `pp_house_rules` block's engine path `/opt/pp-document-suite` → `/root/.letta/pp-document-suite`;
   (b) fix `qms_docx_formatter`'s stale hardcoded Gotenberg IP `143.244.132.80:3000` (KVM4 is
   `72.60.35.12`; better: use a hostname/env, not an IP); (c) consider giving the orchestrator
   chain real `tool_rules` instead of description-only sequencing.
9. **Identify the `:8787` Drive-query sidecar** used by `gmp_rag_agent` — nothing defines it in the
   repo or the Docker inventory; confirm it still runs and document it.
10. **Resolve documentation conflicts:** `PERSONA.md` says Arial Narrow body vs. the engine/house
    rules' Calibri (Calibri is correct — the engine enforces it); `AGENTS.md` 9-section SOP vs. the
    16-section equipment-SOP template referenced by `qms_sop_expert`/`equipment-sop-generator`
    (context-dependent — equipment SOPs follow QASOP_99); `acme-config.json`'s `skills.enabled`
    still lists the legacy set (`pp-content-developer`, `pp-template-formatter`,
    `pp-annex-content-creator`, `pp-mval-formatter`) instead of `pp-document-suite` (stale —
    update or note).
11. **Open `PPlant MV a02.2.xlsx`** if the oven-method (AM02.2) validation data is ever needed —
    never examined.
12. **Google-Drive delivery** of finished docs to the "CowoRK" folder was requested once and never
    fulfilled (superseded by GitHub links) — may resurface; use `mcp__Google_Drive__create_file`
    with small files only, never base64-relay big binaries through context.

---

## 11. Key files index (read in this order)

1. `pp-document-suite/SKILL.md` — master spec / router (content modes, questionnaire, QA gates).
2. `pp-document-suite/references/GUIDE_bilingual_markdown.md` (≡ root `PP_UNIFIED_DOCX_GUIDE.md`) —
   authoring grammar (pre-session; §2.2 here is the current superset).
3. `pp-document-suite/scripts/pp_report.py` (`fixed()` layout brain) + `build_from_md.py`
   (`emit_form` grid packer) — the code that changed this session.
4. `pp-document-suite/LETTA_INTEGRATION.md` + `integrations/DEPLOY.md` — Letta wiring, Mode A/B,
   registration scripts.
5. `TRANS_DIST/moisture/*.md` — current worked examples of the grammar (record, equation doc,
   big table doc).
6. `ppdocwiz/README.md` — the app front-end.
7. `AGENTS.md` / `PERSONA.md` — house rules incl. the never-fabricate-data guardrail.
8. `openapi_letta.json` — Letta REST surface (v0.16.8).

---

## ADDENDUM v2.1 — post-handover verification & fix pack (2026-08-08, CoA_TRACK session)

Every checkable claim above was verified live (Letta REST · `run_from_source` volume probe ·
Hostinger Docker inventory). Full verdict table: `3p4e/CoA_TRACK` →
`docs/ops/LETTA_HANDOVER_VERIFICATION_2026-08-08.md`. Corrections and completions:

**Facts that moved on since the body text above:**
- Agent fleet: **66** (was 54 on 2026-07-15). `DB3_PP_CURRENT_unified`: **278 files** (was 25).
- `ImB_QC_COAs` actually holds **206 files** (the §3.6 aggregate quirk hides them), incl. two
  QC errata notices owned by the CoA_TRACK thread.
- **PR #13 is merged** (`e9872c9` on main) — §10.1 done.
- Embedding exception: the "PQ1 Water Testing Results Report" source uses
  **text-embedding-3-large** (not -small as §4.1 implies) — dimension-incompatible with the rest.
- §3.7 "all 6 feature flags true": as literal strings only PAGEBREAK/27.16/_form_bulk (build_from_md)
  and data_cm (pp_report) grep true; `FORM:grid` is parsed, not stored verbatim. Hash equality is
  the authoritative sync check.
- **Port 8787 (§4.2/§10.9): resolved — nothing in the Docker inventory maps 8787.** The
  gmp_rag_agent Drive sidecar is not running; treat as defunct until rebuilt.
- Infra deltas vs §3.1: zoneminder stopped; agent-zero gone; new projects cvat (stopped),
  sentinel, wwf_letta, wwf-watchdog, open-design (created); dockge :5001 is container-exposed only.

**Fixes applied 2026-08-08** (old values preserved in the CoA_TRACK verification doc):
- §10.8a `pp_house_rules` block: engine path corrected to `/root/.letta/pp-document-suite`.
- §10.8b `qms_docx_formatter` description: stale IP replaced with **`http://gotenberg:3000`** —
  the in-stack DNS address, live-verified (external `:3000` is firewalled; `172.17.0.1` and
  `host.docker.internal` do NOT work from the sandbox; `gotenberg:3000` returns 200).
- §10.3 **A1/A2 PDFs rendered and committed** — built on the Letta volume engine (byte sizes match
  the repo DOCX exactly), converted by in-stack Gotenberg, transferred back with end-to-end
  SHA-256 gates.
- §10.5 root shim `scripts/build_from_md.py` replaced with a forwarder that execs the canonical
  `pp-document-suite/scripts/` copy.
- §10.4 (docs half): `[[FORM:grid]]`/`[[PAGEBREAK]]` documented in both guide copies;
  `SKILL.md` bumped to v1.7.0. (Zip build still pending — zips are gitignored.)
- §10.2: AM02.1-R01/-A1/-A2 registered as **PROVISIONAL** in `QMS_TRACKING.md` §9 and
  `QC_QMS_Document_Code_Registry.md` §8 — visible and collision-guarded, QA confirmation pending.
- §10.10: PERSONA.md got a dated superseding entry (Calibri, engine-enforced); AGENTS.md
  clarifies 9-section (general) vs 16-section QASOP_99 (equipment); `acme-config.json`
  `skills.enabled` → `pp-document-suite` (legacy list preserved as deprecated).

**Engine testing (upgraded engine, from this clone):** FORM:grid+PAGEBREAK+landscape test doc →
PASS (6 fields packed into 2 rows); AM02.1-R01-A2 rebuilt from source → PASS, structure identical
to the committed DOCX (67×20), anchor values 10,0→8,32 · 45,0→43,36 · 68,1→66,48 present; a
CoA_TRACK production generator (PP-QC-SPEC-001) rebuilt on the upgraded engine → PASS with all
42 ranges/nominals intact — the upgrade is backward-compatible.

**Still open after this pack:** Mode B deploy (§10.6) · PP Doc Wiz deploy (§10.7) · orchestrator
`tool_rules` (§10.8c) · fresh skill zip distribution (§10.4, zip half) · QA confirmation of the
AM02.1 codes · rebuilding or retiring the 8787 Drive sidecar · `PPlant MV a02.2.xlsx` (§10.11) ·
Drive delivery thread (§10.12).
