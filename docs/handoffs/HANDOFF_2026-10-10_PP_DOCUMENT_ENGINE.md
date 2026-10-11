# Handoff — the PP document engine in the letta-stack (10.10.2026)

Blagoj Nikolov, M.Pharm., Head of QC. Everything a new session needs to keep developing the
Purely Plant document engine: the engine itself, the DocEngine service, the PP Doc Wiz backend,
the PP Suite frontend built from the Claude Design handoff, the renderer, the RAGFlow link, the
tests and CI, what changed in PRs #26–#32, and what is still open. The server side (KVM4
deployment) is in `docs/handoffs/HANDOFF_2026-10-09_KVM4_DEPLOY.md` and
`server/runbooks/docengine_knowledge_and_render.md`; this document refers to them instead of
repeating them.

Secrets: only variable **names** appear here. Values live in the KVM4 `.env` files (0600, host only)
and in the Claude environment settings ("Environment F", `env_01EzdXRuyMqkCHwgaR8ox98W`). Never write
a value into the repository, a PR, a chat or Open Brain.

---

## 1. The system in one picture

```
 Browser / phone / laptop
        │  https://docwiz.srv1231216.hstgr.cloud
        ▼
 ┌──────────────── ppdocwiz (apps/ppdocwiz) ────────────────┐
 │  web/ → frontend/suite   PP Suite (React+TS, Hybrid v2)   │
 │  backend/app.py          FastAPI: session, wizard, build, │
 │                          download (pp_render), chat,      │
 │                          /api/docengine/* proxy           │
 │  engine: ../../pp-document-suite/scripts (canonical)      │
 └──────┬───────────────────────┬───────────────┬────────────┘
        │ X-API-Key             │ Letta API     │ GOTENBERG_URL
        ▼                       ▼               ▼
 ┌── pp-docengine ──────┐   ┌─ letta ─┐   ┌─ pp-render (gotenberg) ─┐
 │ apps/wwf-docengine   │──▶│ gf_*    │   │ Gotenberg 8.37.0 +      │
 │ FastAPI + Postgres   │   │ agents  │   │ LibreOffice + house     │
 │ pipeline, /build,    │   └─────────┘   │ fonts (server/render/)  │
 │ /documents, /pdf,    │──────────────────▶ /forms/libreoffice/... │
 │ /knowledge/*         │                 └─────────────────────────┘
 │ engine/ = exact copy │──▶ RAGFlow (ragflow-cpu): DB01_REG, eCOA_DB, examples
 └──────────────────────┘
```

One engine, one renderer, one knowledge link:

- **Engine**: `pp-document-suite/scripts`. It is canonical. DocEngine runs an exact, CI-checked copy.
- **Renderer**: `pp_render.py`, which renders through Gotenberg when it is reachable and through
  local LibreOffice when it is not.
- **Knowledge**: RAGFlow, reached only through DocEngine's `app/ragflow.py`.

---

## 2. The engine — `pp-document-suite/`

| file | role |
|---|---|
| `scripts/build_from_md.py` | bilingual Markdown → controlled `.docx`. Routes SOP → two-column, ANNEX/FORM/CHECKLIST/LOG → inline annex shell. CLI: `python3 build_from_md.py src.md out.docx` |
| `scripts/pp_format.py` | SOP/annex shells on `assets/PP_BASE_TEMPLATE.docx` (logo header, Page X of Y), section rows, native TOC. Ported 09.10 from the DocEngine canon line: `kv_block`, `cell08`, `value_span`, `_merge`, `sop_nested_table` |
| `scripts/pp_report.py` | reports and records: `fixed()` (the column-width brain), native OMML equations, `calc_step`, `entry_table`, sign-offs, `cover_page`, `toc_page` |
| `scripts/pp_charts.py`, `pp_theme.py` | figures; the single house navy `#2B547E`, 6 pt font floor |
| `scripts/pp_verify.py` | the delivery gate (§2.2) |
| `scripts/pp_assets.py` | fonts and glyph coverage; `must_cover(ch)` |
| `scripts/pp_render.py` | DOCX → PDF on any device (§5) |
| `scripts/pp_format_layout_addons.py` | compatibility shim for older imports |
| `scripts/render_pdf.ps1` | Word-COM rendering on a Windows PC (manual use only) |
| `assets/lo_profile/` | LibreOffice user profile with the `Standard.Module1.ToPdf` macro (updates fields and indexes, then exports) |
| `tests/` | `test_layout.py` (column sizing), `test_glyph_guard.py`, `test_render.py` |
| `SKILL.md`, `references/` | the skill text (Modes A/B/C, 9-section SOP, formatting specs) |

### 2.1 Markdown grammar (what every route accepts)

- **`<!-- HEADERDATA … -->`** at the top: `code`, `version`, `title_mk`, `title_en`, `doctype`,
  orientation and similar fields. The parser is line-anchored: a line that is only `-->` closes the
  block, so a title containing `-->` cannot leak into the body (ported 09.10.2026).
- Headings `#`/`##`/`###` give the section structure. In SOPs they carry Heading 1–3 so the TOC fills.
- Bilingual pairs `МК | EN`. Macedonian comes first, uses decimal commas, and abbreviations are not translated.
- `[[TABLE]] … [[/TABLE]]` is a data table: navy header row, zebra rows, header repeated on page breaks.
- `[[FORM]]` / `[[FORM:grid]]` is a label|value form or an entry grid. Name/Date/Signature columns are sized to purpose.
- `[[BOX:<cm>]] caption … [[/BOX]]` reserves a marked space of a minimum height (for example label specimens).
- `[[PAGEBREAK]]` / `[[NEWPAGE]]`.
- The authority is the parser itself, `build_from_md.parse()`. The `PP_UNIFIED_DOCX_GUIDE.md` that its docstring names is **not in this repository**; the worked sources in `deliverables/inland_transport_2026-10/` are the best examples.

### 2.2 The verify gate — `pp_verify.py`

Usage: `python3 pp_verify.py out.docx [--source src.md …] [--min-pt 6] [--require-bilingual true|false]`.

- It prints `RESULT PASS` or `RESULT FAIL`. Every route deletes a FAIL build and never offers it for download.
- It checks: the font floor; content fidelity against `--source`; the bilingual check (off by default; DocEngine
  turns it on for generated SOPs); and the **glyph guard**.
- **Glyph rule** (house font rule, 09.10.2026):
  - Letters, digits and `№` must be present in the declared font.
  - Symbols (Unicode category `S*`: ☐ ☒ ✓ ≤ Δ …) may fall back.
  - `pp_assets.must_cover()` implements this.
  - Before the rule existed, every form failed on ☐ as soon as fontTools was installed.

---

## 3. DocEngine — `apps/wwf-docengine/`

A FastAPI service with an asyncpg Postgres. It is internal-only and has no public route.
Every call except `/health` needs the header `X-API-Key: $DOCENGINE_API_KEY`.

### 3.1 Routes (`app/main.py`)

| route | what |
|---|---|
| `GET /health` | `db`, `letta`, `ragflow` (configured), `engine: "pp-document-suite (synced copy, canon revision 2026-10-09)"` |
| `GET /questionnaires`, `/questionnaires/{key}` | Mode-A question banks (`app/questionnaires.py`: `sop_qc`, `annex_form`) |
| `POST /workflows`, `GET /workflows/{id}` | questionnaire → SOP pipeline job (background task, strong ref kept; stale jobs reaped at start-up) |
| `POST /build` | Markdown → verified `.docx` (422 with the verify report on FAIL), registered in `documents` |
| `GET /documents`, `/documents/{id}`, `/download`, `/pdf` | registry; `/pdf` posts to Gotenberg with `updateIndexes=true` and optional basic auth (`GOTENBERG_USERNAME/PASSWORD`) |
| `POST /knowledge/search` | `{corpus: regulatory\|ecoa\|examples, question, top_n, keyword}` → passages + the corpus note |
| `GET /knowledge/health` | configured, reachable, dataset ids per corpus |

### 3.2 Pipeline (`app/pipeline.py`)

1. **generate**: the `gf_*` authors draft each section from the questionnaire brief.
   `examples_for()` adds the closest house examples once `RAGFLOW_EXAMPLE_DATASETS` is set, with the
   rule "structure and style only, never a value".
2. **regulatory check**: `gf_reg_checker` receives the DB01_REG passages for the section as
   `[R1]…[Rn]`. The job result keeps `regulatory_sources` (document, page, chunk id, similarity).
   If RAGFlow is unconfigured or unreachable, the check falls back to the agent's attached Letta
   sources (`DOCENGINE_REG_SOURCES`) and records the fallback in `knowledge.notes`.
3. **bilingual**: `gf_translator_mk_en` translates, and `_bilingual_gaps` catches the sections it missed.
4. **§6A audit**: `gf_qa_auditor`.
5. **build**: `builder.build` runs the synced engine and `pp_verify`.

### 3.3 Agents (`agents/fleet.yaml`, `app/fleet.py`, `app/letta.py`)

- The fleet: `gf_doc_orchestrator`, `gf_sop_author`, `gf_annex_author`, `gf_translator_mk_en`,
  `gf_reg_checker`, `gf_raci_specialist`, `gf_qa_auditor`, `gf_app_assistant`.
- `ensure_fleet` is idempotent and seeds the `gf_house_rules` memory block.
- The Letta client refuses to touch any agent whose name does not start with `gf_`.
- Each exchange runs on an ephemeral clone.
- The model is chosen at run time. The placeholder in `fleet.yaml` is not the model.
- **On KVM4 since 10.10.2026** all eight `gf_` agents run on `openai-proxy/nvidia/nemotron-3-ultra`:
  - LiteLLM `nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b`, router fallback `nvidia/kimi-k3`
    (`nvidia_nim/moonshotai/kimi-k3`), `num_retries: 0` (`/opt/stacks/litellm/config.yaml`).
  - Before: `openai-proxy/moonshot/kimi-k2.6`, whose balance ran out. The old configuration is in
    `/opt/wwf-deploy/backups/gf_agents_llm_config_pre-nvidia_20261010.json`.
  - The ephemeral clone copies the agent's model handle, so a new LiteLLM model is usable only after
    the Letta provider is refreshed (`PATCH /v1/providers/{id}/refresh`). Without the refresh the clone
    fails with "Handle … not found" (job `8e188e35`).

### 3.4 RAGFlow client (`app/ragflow.py`)

- It makes one call, `POST {RAGFLOW_BASE_URL}/api/v1/retrieval`, with `RAGFLOW_API_KEY`.
- Datasets, overridable by `RAGFLOW_REG_DATASETS` / `RAGFLOW_ECOA_DATASETS` / `RAGFLOW_EXAMPLE_DATASETS`:
  - DB01_REG `a33b0812a3d411f1858cf58865604f65`
  - eCOA_DB `dd3ea108a3fd11f1858cf58865604f65`
  - examples: none yet
- **eCOA_DB is lookup-only.** It tells you which certificate exists for a batch. A measured value is
  never read from chunk text, because chunking drops superscripts and truncates ranges. Values come from
  the typed, double-read extraction. The search response always carries that note (`ECOA_NOTE`).
- **What is in RAGFlow on 10.10.2026.** Another agent changed RAGFlow's pipelines and models on 10.10.
  Read-only status of that evening:
  - **`eCOA_INGEST`** `71b9c168b4a311f1a370a99b32e82467` was created on 20.09 as the planned replacement for
    `eCOA_DB` (`ingestion/ecoa_runner/verify_ecoa_ingest.py`). On 10.10 it was being filled: 8 certificates
    that evening. DocEngine does **not** query it, because its default is `eCOA_DB` and no
    `RAGFLOW_*_DATASETS` is set on KVM4.
    - Its pipeline is `eCOA_PIPE`: Kimi K3 via NVIDIA reads the PDF; DeepSeek v4 Flash writes the
      questions and keywords; one 8192-token chunk per certificate; RAPTOR and GraphRAG on.
    - It is embedded with **Voyage-4-large**. `eCOA_DB` is embedded with Voyage-3-large, so one
      retrieval call cannot search both.
    - Either `eCOA_DB` is re-parsed into the new embedding, or `RAGFLOW_ECOA_DATASETS` stays on `eCOA_DB`.
  - **`DB01_REG`**: 48 documents are parsed. **22 failed** ("User pipeline not found", 0 chunks): the Test Weights
    folder, uploaded 30.08 and re-run on 10.10.
    - The cause is at document level. `DB01_REG`'s documents still carry pipeline `7d8aed62a6cc11f1a0f2e9fe9c0c677b`,
      and that canvas no longer exists.
    - At dataset level, `DB01_REG`, `eCOA_DB` and `eCOA_SS` now point to `eCOA_DB_agent`, whose prompts are
      written for certificates. A re-run would therefore index regulatory texts with certificate questions.
  - Chats: 3 active (`AAAA`, `zZz`, `bbb`, which are test names too). The 46 `ZZ*`/`tmp_*` probe chats are
    already deleted: status 0 is RAGFlow's soft delete.
  - Account defaults: chat `deepseek-v4-pro`, embedding `voyage-4-large`, rerank `rerank-2.5`, image
    `kimi-k3` (NVIDIA).
    - Speech-to-text and text-to-speech are OpenAI, and that account has **no credits** ("429 no credits remaining").

### 3.5 Engine sync

- `engine/` is a byte-exact copy of `pp-document-suite`.
- To refresh it: `engine/sync_from_suite.sh`. Its record is `engine/PROVENANCE.md`.
- `tests/test_engine_sync.py` fails CI on any drift, so a fix goes into the suite first and is then synced.
- The decision record is `docs/ENGINE_CONSOLIDATION_2026-08-29.md` (one engine). The revision note is in
  `docs/wwf_DOCENGINE-CANON-2026-07.md` (canon revision 09.10.2026).

The WWF stack's own `wwf-docengine` (`growflow-docengine:v26`, built from WEEKLY_WEED_FLOW) is a separate,
untouched deployment. The Head of QC ruled on 09.10.2026 that it is merged into WWF later.

---

## 4. PP Doc Wiz backend — `apps/ppdocwiz/backend/`

| route | what |
|---|---|
| `GET /api/health` | engine, renderer, DocEngine and Letta reachability |
| `POST /api/session` | exchanges `PPDOCWIZ_API_KEY` for an HttpOnly HMAC-signed cookie (401 bad key, 503 not configured) |
| `GET /api/doctypes`, `/api/example` | wizard data |
| `POST /api/wizard/preview`, `/api/wizard/build` | form answers → Markdown (`wizard.compose_markdown`) → engine → gate |
| `POST /api/build` | **raw Markdown → the current engine** (the Builder's Source view); the build is named by the pasted HEADERDATA |
| `GET /api/download/{name}` | `.docx`, or `.pdf` through `pp_render` (`?inline=1` for Preview) |
| `POST /api/chat` | Letta, restricted to the agent allowlist in `config.py` (400 outside it, 503 without Letta) |
| `/api/docengine/{health,questionnaires,workflows,build,documents…}` | same-origin proxy that adds `DOCENGINE_API_KEY`. Calls run in `asyncio.to_thread`; HEAD goes upstream as a 1-byte Range GET; any other path → 404, no session → 401, unconfigured → 503 |
| `/` and `/legacy` | the PP Suite and the old single-file SPA |

Configuration names: `PPDOCWIZ_API_KEY`, the session secret, `DOCENGINE_URL`, `DOCENGINE_API_KEY`,
the Letta URL/key and agent allowlist, `GOTENBERG_URL` (+ `GOTENBERG_USERNAME/PASSWORD` outside the stack).

---

## 5. Rendering — `pp_render.py` and `pp-render`

- **The rule.** CLAUDE.md §9 (Head of QC, 09.10.2026): rendering must not depend on the device.
  Every DOCX goes through `pp_render.render_pdf()` / `python3 pp_render.py in.docx out.pdf`.
  Never use a bare `soffice --convert-to pdf`: it leaves the TOC empty.
- **Order** (`PP_RENDER=auto`):
  1. Gotenberg (`/forms/libreoffice/convert`, `updateIndexes=true`, basic auth if a user is set).
  2. Local LibreOffice with a fresh copy of `assets/lo_profile` per render.

  The output is written with an atomic rename. If both routes fail, a `RenderError` names both reasons.
- **The service**: `pp-render` (Head of QC, 10.10.2026, PR #32).
  - It is Gotenberg 8.37.0 (LibreOffice) with the house fonts built in (`server/render/`: `Dockerfile`,
    `compose.yaml`, `get_fonts.py`).
  - Fonts come from `/opt/fonts/pp/{free,licensed}` on KVM4. The licensed Microsoft fonts are never committed.
  - Addresses: `http://gotenberg:3000` in-stack; `https://render.srv1231216.hstgr.cloud` behind basic auth.
- **Why LibreOffice and not OnlyOffice**: in a side-by-side test against Word-made PDFs with the real fonts,
  - LibreOffice matched Word: SOP-017 23/23 pages, QCSOP_018 A01 14/14, label sheet identical;
  - OnlyOffice 9.4 did not: 19/23 pages, a column cut off, Arial Narrow ignored.

  OnlyOffice was removed.
- **Fonts are part of the result.** A missing face changes line breaks and page count. To add a font,
  follow runbook §2: copy the file, rebuild with the next `fonts.<n>` tag, set the tag in compose.
- **Status in Environment F (checked 10.10.2026).** The network already reaches
  `render.srv1231216.hstgr.cloud`: it answers 401 without credentials. The three variables below are
  **not set yet**. `GOTENBERG_URL` is `https://render.srv1231216.hstgr.cloud`; the username and password are on
  KVM4 in `/opt/stacks/pp-render/credentials.env` (`GOTENBERG_USERNAME`, `GOTENBERG_PASSWORD`). Until the Head of QC
  adds them, `pp_render` in a session falls back to local LibreOffice. KVM4's own services are not
  affected, because they reach `http://gotenberg:3000` directly.
- **Inside a Claude cloud session**: set `GOTENBERG_URL`, `GOTENBERG_USERNAME` and `GOTENBERG_PASSWORD`
  in the environment settings and allow `render.srv1231216.hstgr.cloud` in the network policy. With
  those, `pp_render` needs no local office suite.

---

## 6. PP Suite frontend — `apps/ppdocwiz/web/` (Claude Design "PP Suite Hybrid v2")

- **Stack.** React + TypeScript + Vite. `npm run build` writes to `../frontend/suite`, which the backend
  serves at `/`.
- **Design.** The Claude Design handoff "PP Suite Hybrid v2": a dark pipeline console, a three-pane
  desk, and margin stamps on the A4 page.
- **The design-versus-engine rule** (CLAUDE.md §6, applied here): the design decides colour, type and
  layout only. Wherever the prototype's text differs from what the engine prints, **the engine wins**.
  No wording, claim or value comes from the mock-up.

### 6.1 Structure

| path | role |
|---|---|
| `src/api/client.ts` | one typed interface for every screen |
| `src/api/live.ts` / `mock.ts` | adapters. Live calls the real backend; mock returns the same response shapes, with jobs that advance through the stages. `?api=live\|mock` (remembered) or Fleet › Settings. Production builds default to live, `npm run dev` to mock |
| `src/api/normalize.ts`, `types.ts` | response shapes |
| `src/store/store.ts` | session state, incl. `lastBuild` (the last real build, read by Verify and Preview) |
| `src/components/Shell.tsx` | frame, top bar, breadcrumbs (`LIVE_CRUMB`: neutral in live mode) |
| `src/components/LiveViews.tsx` | `VerifyLive`, `PreviewLive`, `EmptyState`, `SampleRibbon`, `WithRibbon` |
| `src/components/Create.tsx`, `PPPage.tsx`, `Charts.tsx`, `ui.tsx` | Create menu + New-document sheet (code pattern, MK/EN title checks), A4 page renderer, charts, primitives |
| `src/lib/compose.ts` | in-browser Markdown composer, pinned to `wizard.compose_markdown` by shared fixtures (`lib/fixtures`; Python side: `tests/test_suite_ui.py`) |
| `src/lib/docparse.ts` | `headerMeta()`: reads HEADERDATA so a pasted document is filed under its own code |
| `src/lib/verify.ts`, `diff.ts`, `stats.ts`, `newdoc.ts` | verify report display, diffs, statistics (tested), new-document scaffolds |
| `src/data/questionnaires.ts`, `samples.ts` | mock-mode data only |

### 6.2 Screens → backend

| screen | live calls |
|---|---|
| Sign-in | `POST /api/session` |
| Builder (Source · Page · Blocks) | example, wizard preview/build, download; Source view → `POST /api/build` |
| Agent chat | `POST /api/chat`. It starts empty and shows only what the server returns |
| Questionnaire | DocEngine `GET /questionnaires/{key}`, `POST /workflows` via the proxy |
| Jobs | `GET /workflows/{id}`, polled every 1 s while running |
| Library | `/documents`, detail, `.docx`, `/pdf`. Errors show inline (410/502/503) |
| Verify / Preview | the session's `lastBuild`: its real `pp_verify` report and its PDF (`?inline=1`), or an empty state |
| Formatter | Mode B → DocEngine `/build`. It builds only a loaded or pasted file, never the on-screen sample |
| Reports | no backend yet ("Sample content, not connected" ribbon) |
| Fleet & health | `/api/health`, DocEngine `/health`. The agent list and log tail carry the sample ribbon |

**Live mode never shows sample data as if it were real.** This was the main finding of the 09.10 test.

### 6.3 Run it locally

```bash
cd apps/ppdocwiz/web && npm ci && npm run dev          # :5173, mock; /api proxied to :8770
npm run typecheck && npm test && npm run build          # what CI runs
cd .. && uvicorn backend.app:app --port 8770            # backend (env names in §4)
```
The end-to-end scripts and screenshots of the 09.10 test are in `deliverables/frontend_test_2026-10-09/`
(`TEST_REPORT.md`, `e2e/`). They are Playwright scripts that use the pre-installed Chromium.

---

## 7. Tests and CI (`.github/workflows/ci.yml`)

| job | covers | local |
|---|---|---|
| `engine-layout` | `pp-document-suite/tests` (layout, glyph guard, render) | `python3 -m pytest pp-document-suite/tests -q` |
| `docengine-tests` | DocEngine against a real Postgres service, incl. engine sync and RAGFlow | Postgres 16 (as root: `runuser -u postgres`), set the test DB URL from the job's `env`, `cd apps/wwf-docengine && python3 -m pytest tests -q` |
| `ppdocwiz-tests` | auth, path handling, proxy, composer parity | `cd apps/ppdocwiz && python3 -m pytest tests -q` |
| `ppdocwiz-web` | typecheck, vitest, build | §6.3 |
| `policy`, `secrets` (gitleaks), `deps` (pip-audit), `build` | repository integrity, secret scan over history, advisories, deliverable builders | — |

DocEngine pins `fonttools==4.62.1`. Without fontTools the glyph guard has nothing to check against.

---

## 8. History — what was done (all merged to `main`)

| PR | date | change |
|---|---|---|
| #26 | 09.10 | PP Suite frontend (Hybrid v2). Full end-to-end test with nine defects fixed (`TEST_REPORT.md`): pasted documents filed under the wrong code, raw builds on a stale engine, empty PDF TOC, samples written into the Library, sample data shown as real, no DocEngine proxy, HEAD 405, PDF errors leaving the app, FAIL builds still downloadable. Result: UI builds identical to the delivered documents (WHSOP_003 15/15 pages, 26/26 TOC; QASOP_0XX 10/10) |
| #27 | 09.10 | Inland transport package (QASOP_0XX, USP <1079.2> brackets), T1 example package, duplex merge |
| #28 | 09.10 | DocEngine runs the current suite. The canon-2026-07 features (`--require-bilingual`, line-anchored HEADERDATA, `kv_block`/`sop_nested_table` …) were ported into the suite, the glyph rule was added, `engine/` was synced, and CI holds the copy identical |
| #29 | 09.10 | RAGFlow link (`app/ragflow.py`, `/knowledge/*`, regulatory check cites DB01, eCOA lookup with its note, examples slot) and `pp_render` (Gotenberg first, local LibreOffice fallback, bundled macro profile) |
| #30 | 09.10 | KVM4 deployment handoff for the Environment F session |
| #31 | 09.10 | Runbook "Deployed": Gotenberg, pp-docengine (`/opt/stacks/pp-docengine`, own Postgres), ppdocwiz (`docwiz.srv1231216.hstgr.cloud`) live on KVM4 from `5ecf6a6` |
| #32 | 10.10 | `pp-render` replaces the plain Gotenberg: house fonts built in; OnlyOffice rejected after the Word comparison |
| #33 | 10.10 | This handoff |
| — | 10.10 | Server only, KVM4, no code change: the `gf_` agents moved from Moonshot Kimi K2.6 to NVIDIA Nemotron 3 Ultra (fallback Kimi K3) (§3.3); the redundant test SOP was removed from the pp-docengine Library (0 documents registered) |

---

## 9. Lessons that cost time (do not repeat)

1. **Two engines drift silently.** The canon-2026-07 copy in DocEngine lacked months of fixes, and A03
   printed `[[BOX:7]]` as text. There is one engine now, and `test_engine_sync.py` holds the copy.
2. **`soffice --convert-to pdf` does not update fields.** Use `pp_render` (macro or `updateIndexes`).
3. **Concurrent soffice processes on one profile hang.** Use a fresh profile per render and serialise
   local renders.
4. **Fonts decide the page count.** Compare with Word only once the real faces are installed on the renderer.
5. **A mock is not a feature.** Live mode must show the server's truth or an empty state, and a sample
   needs its ribbon.
6. **Name the build from the document**, never from the screen's sample (HEADERDATA → `headerMeta`).
7. **A `pkill` pattern that matches its own shell kills the shell.** Use pid files (`wiz_start.sh`).
8. **Postgres refuses to run as root.** Use `runuser -u postgres` with the script in `/var/tmp`.
9. **This session's environment blocks KVM4 hosts.** KVM4 work runs from Environment F.
10. **A model that passes in English can fail in Macedonian.** Test the Macedonian output before moving the authors and the translator to a new model. The 10.10 switch to Nemotron ran end to end and failed only at the §6A audit, 16 minutes later.

---

## 10. Open items

| # | item | where |
|---|---|---|
| 1 | **Done 11.10.2026 (PR #35).** The five Macedonian-writing and audit agents run on DeepSeek v4 Flash; the workflow runs end to end and, where a §6A FIX survives two repair rounds, stops at `awaiting_review` with a verified `.docx` (job `2ddd58d1`). Runbook "Deployed — 11.10.2026". Job `2ddd58d1` waits for the Head of QC's Approve / Return | KVM4 / ppdocwiz Jobs |
| 2 | Two uvicorn workers race on `CREATE SCHEMA` on an empty database (one respawns). Use an advisory lock or create the schema once before the workers start | `app/db.py` |
| 3 | **Review decision done 11.10.2026 (PR #35)**: `POST /workflows/{id}/review`, wired in ppdocwiz. Still no backend for report builds (`pp_report`), Formatter Mode C or the engine-environment check (live mode shows 501) | ppdocwiz + DocEngine |
| 4 | Fleet agent list and log tail, and Chat's left pane (agents, memory, sources, tools), are still sample content | `Fleet.tsx`, `Chat.tsx` |
| 5 | `DB_EXAMPLES` RAGFlow dataset for house examples. Then set `RAGFLOW_EXAMPLE_DATASETS` | runbook §3 |
| 6 | Jobs list survives only in session state. A server-side job list route would make it robust | DocEngine `/workflows` |
| 7 | Merging this DocEngine into the WWF stack's `wwf-docengine` (Head of QC, later) | WEEKLY_WEED_FLOW |
| 8 | **Done 11.10.2026 (PR #35).** A failed job keeps its draft, sources and knowledge; a FIX verdict gets up to two repair rounds, then goes to review | `app/pipeline.py` |
| 9 | RAGFlow after the other agent's changes (§3.4): **10.10.2026** `DB01_REG` moved to the built-in laws parser and its 22 failed documents re-queued — confirm they finished. Still the Head of QC's: one embedding model for the eCoA datasets (`eCOA_INGEST` or `eCOA_DB`); OpenAI top-up or another speech provider; RAGFlow chats still pointing at dead models | RAGFlow |
| 10 | LiteLLM: the DeepSeek key was replaced on 10.10.2026 with the working one RAGFlow uses. The Anthropic and OpenAI keys are still dead: renew or remove them. The Gemini keys exposed during the 10.10 setup must be revoked and reissued (Head of QC) | `/opt/stacks/litellm/.env`, Google AI Studio |
| 11 | Environment F: add `GOTENBERG_URL`, `GOTENBERG_USERNAME`, `GOTENBERG_PASSWORD` (§5) | Claude environment settings |

## 11. Where to look first

`CLAUDE.md` §6 and §9 → this file → `server/runbooks/docengine_knowledge_and_render.md` →
`apps/ppdocwiz/web/README.md` → `deliverables/frontend_test_2026-10-09/TEST_REPORT.md` →
`docs/ENGINE_CONSOLIDATION_2026-08-29.md`. The record is also in Open Brain
(`thoughts`, `metadata.source = claude-code-desk`).

## References

1. European Commission. *EudraLex Volume 4 — EU GMP Guidelines, Chapter 4: Documentation* (2011),
   §4.1–4.10 (generation and control of documentation; templates; electronic documents), pp. 1–3.
2. European Commission. *EudraLex Volume 4, Annex 11: Computerised Systems* (2011), §4 Validation
   (pp. 2–3), §7 Data storage, §8 Printouts, §10 Change and configuration management (p. 4).
3. ICH Q9(R1) *Quality Risk Management* (2023), §5 (risk-based approach to change), pp. 6–9.
4. ICH Q10 *Pharmaceutical Quality System* (2008), §3.2.3 Change Management System, pp. 11–12.
5. PIC/S PI 041-1 *Good Practices for Data Management and Integrity in Regulated GMP/GDP
   Environments* (2021), §8 (computerised systems), pp. 23–40 (ALCOA+, which underlies the
   content-fidelity and "engine wins" rules).
