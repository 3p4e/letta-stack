# PP Suite — frontend

React + TypeScript (Vite) front end for the pp-document-suite engine, implementing the
Claude Design handoff **PP Suite Hybrid v2** (dark pipeline console, three-pane desk,
margin stamps on the A4 page). It replaces the single-file PP Doc Wiz SPA, which stays
reachable at `/legacy`.

```bash
npm ci
npm run dev        # http://localhost:5173 — mock data by default; /api proxied to :8770
npm run build      # → ../frontend/suite, served by backend/app.py at "/"
npm test           # composer parity with wizard.py, pp_data mirror
npm run typecheck
```

## Live and mock

Every screen talks to one typed interface (`src/api/client.ts`) with two adapters:

| | `live.ts` | `mock.ts` |
|---|---|---|
| ppdocwiz `/api/*` | real (session cookie, wizard preview/build, download, chat) | sample data, same response shapes |
| DocEngine | `window.PP_SUITE_CONFIG.docengineBase` (default `/api/docengine`) | in-memory jobs that advance through the pipeline stages |

Choose with `?api=live` / `?api=mock` (remembered), or in **Fleet & health › Settings**. A
production build defaults to live; `npm run dev` defaults to mock. Mock mode shows a
`mock` tag in the top bar and can simulate every degraded state.

**DocEngine is internal-only** (no published port; the WWF `/qms` proxy is its caller), so
in live mode the Questionnaire, Jobs and Library screens need a same-origin proxy to it.
Until one exists they show the 404 / unreachable state rather than sample data.

## Screens → backend

| Screen | Calls |
|---|---|
| Sign-in | `POST /api/session` (401 bad key, 503 not configured) |
| Builder (Source · Page · Blocks) | `GET /api/example`, `POST /api/wizard/preview`, `POST /api/wizard/build`, `GET /api/download/{id}`; raw Markdown → DocEngine `POST /build` |
| Agent chat | `POST /api/chat` (allowlist → 400, no Letta → 503) |
| Questionnaire | `GET /questionnaires/{key}`, `POST /workflows` |
| Jobs | `GET /workflows/{id}`, polled every 1 s while running |
| Library | `GET /documents`, `GET /documents/{id}`, `/download` (410), `/pdf` (502/503) |
| Verify | `POST /build` (422 on gate fail) |
| Fleet & health | `GET /api/health`, DocEngine `GET /health` |

Not yet backed by a route (live mode shows the 501 explaining so): the review decision on an
`awaiting_review` job, report builds (`pp_report`), Formatter Mode C, and the engine
environment check.

## Design coverage

All ten Hybrid v2 screens plus the Create menu and New-document sheet, and the eleven gaps in
the handoff's `COVERAGE.md`:

1. sign-in · 2. wizard block editor (Builder › Blocks: sections level 1–3, text / bullets / form /
table, reorder, column editor, Load example, server preview) · 3. review gate (Jobs,
`awaiting_review`) · 4. SOP / annex lifecycle (Builder meta box → `status`, `effective_date`,
`review_date` in HEADERDATA) · 5. version history + diff (Library › versions) · 6. degraded
states (dots, per-screen banners, mock fault switches) · 7. report data binding (provenance
sha256 / bytes / modified, statistics, `assert_consistent` blocks the build) · 8. chart picker
(7 `pp_charts` types) · 9. status_grid, databox, minilabel, note, bullet, eqn_result, editable
execution sign-off · 10. engine environment (fonts, glyph audit, sync hash, manifest drift) ·
11. platform notes (TOC F9, OMML on Linux).

## Where it follows the engine instead of the mock-up

The handoff's own rule is that design governs colour, type and layout only. Where the
prototype's text differed from what the engine prints, the engine wins:

- The running header shows `DRAFT` / `IN REVIEW` until approval and `vNN` after
  (`pp_format.header_version`); the annex title block carries the status line.
- The in-review band reads `IN REVIEW / FOR APPROVAL — NOT FOR USE` (`pp_format.status_label`).
- There is no `[[SIGNOFF]]` tag in `build_from_md`; the sample's approval block is a `[[TABLE]]`.
- Agent-suggested EN halves come from a terminology table, never invented text.
- Page highlights and margin stamps are positioned from measured block positions, not hand-placed.
