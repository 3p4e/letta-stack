# PP Doc Wiz frontend — end-to-end test, 09.10.2026

**What was tested.** The PP Suite frontend (`apps/ppdocwiz`, PR #26) in **live mode**, driven by
Playwright (Chromium) against the real ppdocwiz backend, a real DocEngine and a real Postgres 16.
Branch `feat/pp-suite-frontend` with `main` merged in, so the engine is the one that built the
inland-transport package. Not available in this container: Letta (chat and questionnaire workflows
answer 503) and Gotenberg (DocEngine PDF answers 503). Their error paths were tested; their happy
paths were not.

**Test documents.** The controlled sources of `WHSOP_003`, `WHSOP_003_A03`, `WHSOP_003_A05` and
`QASOP_0XX` (`deliverables/inland_transport_2026-10/md/`), pasted into the Builder; a new SOP created
through Create → SOP → Write in Markdown; the Builder's own wizard document.

Scripts: `e2e/` (run with a ppdocwiz on :8770). Screenshots: `screens/` (`01–05` before the fixes,
`06–14` after).

## Result

After the fixes, a document built in the frontend is **identical to the delivered one**:

| Document | Pages UI / delivered | TOC entries UI / delivered | `[[BOX]]` markers | Text lines that differ |
|---|---|---|---|---|
| WHSOP_003 | 15 / 15 | 26 / 26 | 0 | 0 |
| WHSOP_003_A03 | 4 / 4 | — | 0 | 0 |
| WHSOP_003_A05 | 3 / 3 | — | 0 | 0 |
| QASOP_0XX | 10 / 10 | 26 / 26 | 0 | 0 |

Every build passed `pp_verify`. Backend tests 40/40 (11 new), frontend tests 8/8, typecheck clean.

## Defects found and fixed

| # | Defect (as found) | Fix |
|---|---|---|
| 1 | **Pasted documents filed under the wrong code.** WHSOP_003, A03 and A05 pasted into the Builder were all registered as `WHSOP_002_A02` (the Builder's sample), titled "Release Record — Propagation Material", as three versions of one document. | The pasted HEADERDATA names the build. |
| 2 | **Raw-Markdown builds used a stale engine.** They went to DocEngine, whose vendored engine is the canon-2026-07 copy: A03 printed `[[BOX:7]] … [[/BOX]]` as text instead of the four example-label spaces, lost the DRAFT line and wrapped the code; A03 and A05 came out a page short. | The Builder's Source view now builds through ppdocwiz `POST /api/build`, the same engine as the wizard path. |
| 3 | **SOP PDFs had an empty table of contents.** The download rendered with `soffice --convert-to pdf`, which does not update fields (0 of 26 entries). | PDFs render through a bundled LibreOffice profile (`backend/lo_profile`) whose macro updates fields and indexes, as the engine's deliverables do. |
| 4 | **Sample documents written into the real Library.** In live mode, Verify "Re-verify" built the sample `WHSOP_009_A01` pest checklist and Formatter "Build" built the sample `WHSOP_002_A02`; both were registered as controlled documents. | Verify shows the session's last real build; the Formatter refuses to build its on-screen sample. |
| 5 | **Live mode showed sample data as if real**: a canned WHSOP_009_A01 rejection (Verify), sample pages (Preview), a sample conversation with invented tool output even on a 503 (Chat), sample breadcrumbs. | Verify and Preview show the last real build or an empty state; Chat starts empty and shows only what the server returns; breadcrumbs are neutral; Reports and the Fleet agent list / log tail carry a "Sample content, not connected" ribbon. |
| 6 | **Questionnaire, Jobs and Library could not reach DocEngine** — no same-origin proxy existed (the README said so). | ppdocwiz forwards `/api/docengine/{health,questionnaires,workflows,build,documents}` with its own key; anything else 404, no credential 401, unconfigured 503. |
| 7 | **Library availability check 405** (HEAD not accepted upstream). | The proxy sends HEAD upstream as GET. |
| 8 | **Library "PDF" on an error left the app** for a bare JSON page. | The error shows inline (`PDF → 503 · PDF renderer unavailable`). |
| 9 | A wizard build that FAILed the gate stayed downloadable by its id. | A FAIL build's files are deleted. |

## What works (verified)

Sign-in (bad key 401, good key opens a cookie session); Create menu and new-document sheet with its
pre-checks (code pattern, MK/EN titles); Builder Source, Page and Blocks views; wizard build and raw
build with `.docx` and `.pdf` downloads; Questionnaire loads the real `sop_qc` rounds from DocEngine
and starts a workflow (503 shown when Letta is down); Jobs; Library listing, detail and `.docx`
download; Verify and Preview of the last build; Chat error path; Fleet health panels.

## Still open (decisions or missing backends, not fixed here)

1. **DocEngine's engine is the canon-2026-07 copy** (`apps/wwf-docengine/engine`, "BINDING" per
   `docs/wwf_DOCENGINE-CANON-2026-07.md`). Formatter, questionnaire workflows and anything else built
   by DocEngine still lack this autumn's engine fixes (`[[BOX]]`, spacing, keep rules). Bringing it to
   the current `pp-document-suite` is a canon revision — the owner's decision.
2. **No backend yet** for: report builds (`pp_report`), the review decision on an `awaiting_review`
   job, Formatter Mode C, the engine-environment check, the Fleet agent list and log.
3. **Chat's left pane** (agents, core memory, sources, tools) is still static sample content.
4. **Not testable here:** Letta (chat replies, questionnaire workflow to completion) and Gotenberg
   (DocEngine PDF). Run those two paths once on KVM4.
