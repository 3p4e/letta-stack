# Handoff — deploy the document stack on KVM4 (09.10.2026)

From the Claude Code session of 08–09.10.2026 (repo `3p4e/letta-stack`, environment without KVM4
access) to the next session, which runs in **Environment F** (`env_01EzdXRuyMqkCHwgaR8ox98W`), the
environment that holds the KVM4 credentials. Read this whole file first, then `CLAUDE.md`.

## 0. Who you work for, and how

- **Blagoj Nikolov, M.Pharm., Head of QC**, Purely Plant DOOEL Skopje (GACP indoor cultivation +
  GMP dry-flower production). Your outputs are written in his voice when they are documents.
- He wants the task done, not narrated: short answers, no long reports, **do exactly what he
  asks**. Standing correction (09.10.2026): *do not track or comment on whether documents are
  approved, draft or effective — that is not our job.*
- Every finished change: commit, push, PR, review, merge **when he says merge**, and save a record
  to **Open Brain** (Supabase project `open_brain` = `tggqftquioxuxnhdptoy`, table `thoughts`,
  `metadata.source = "claude-code-desk"`). Never write a secret value into Open Brain, a commit, a
  PR or the chat; refer to secrets by variable name only.
- `CLAUDE.md` holds the standing rules (certificate desk §1–8, **§9 rendering**). They apply.

## 1. The goal of this session

Make the document stack on KVM4 complete and connected, so documents are generated, checked against
regulation and rendered the same way from any device:

1. **Gotenberg** running on KVM4 — the one PDF renderer for every service and every device
   (internal `http://gotenberg:3000`, public `https://render.srv1231216.hstgr.cloud` behind basic
   auth). The 2026-08-09 container snapshot shows **no Gotenberg** although `GOTENBERG_URL=http://gotenberg:3000`
   is configured in the Letta stack; after the server reinstall it is probably missing.
2. **DocEngine (`wwf-docengine`) redeployed from `main`** (it now runs the current
   `pp-document-suite` engine and has the RAGFlow link), with `RAGFLOW_BASE_URL`,
   `RAGFLOW_API_KEY`, `GOTENBERG_URL` set, and on RAGFlow's Docker network.
3. **ppdocwiz (PP Suite frontend)** deployed from `main` with `GOTENBERG_URL`, `DOCENGINE_URL`,
   `DOCENGINE_API_KEY`.
4. **Inventory** of everything that should run on KVM4 after the reinstall; anything missing that
   the stack needs is installed and wired (the Head of QC authorised this explicitly).
5. Then (separately, when he asks): the **example-documents dataset** in RAGFlow
   (`RAGFLOW_EXAMPLE_DATASETS`).

The step-by-step server runbook is **`server/runbooks/docengine_knowledge_and_render.md`**. Follow it.

## 2. How to reach KVM4 (proven routes — from Open Brain records)

| Route | What it is | Notes |
|---|---|---|
| **kvm4-runner** | HTTPS service on KVM4 with `POST /shell` and `POST /file/write {path, content_b64}`; has docker CLI, docker compose, `/opt/stacks` bind-mounted, the host docker socket | Used by Claude Code sessions for the WWF deploys of July 2026. Gotchas: `/shell` 500s on commands of ~200 KB — upload payloads with `/file/write` in chunks and verify SHA-256 on both sides; nested heredocs do not survive the JSON transport — write a script file and run it. Its URL and token are in Environment F (look for a `KVM4_RUNNER_*`/`RUNNER_*` variable). |
| **Hostinger VPS API** | `https://developers.hostinger.com/api/vps/v1/virtual-machines/1231216/...` (Docker project list/deploy, VM facts) | Token variable name in earlier records: `VPS_KVM4_API_TOKEN`. |
| **Letta MCP / REST** | `https://mcp-letta.srv1231216.hstgr.cloud` (MCP), Letta REST at `https://ui.srv1231216.hstgr.cloud` | Agent operations only; `run_from_source` runs in a sandbox without docker. |
| SSH | `srv1231216.hstgr.cloud` / 72.60.35.12, user root | **Port 22 is unreachable from Claude cloud sessions** (outbound 443 only; the hostname resolves IPv6-only). Do not spend time on it. |

**First thing to do:** list environment variable *names* (`env | cut -d= -f1 | sort`) and confirm
which of the above credentials Environment F carries, and that its network policy allows
`*.srv1231216.hstgr.cloud` and `developers.hostinger.com` (`curl -sS -o /dev/null -w '%{http_code}'`).
If a host answers `CONNECT tunnel failed, response 403`, the network policy blocks it: tell the
Head of QC the exact host to add under the environment's Allowed domains, in one line.

Server facts (from records): host `crimson`, Debian; stacks under `/opt/stacks/<stack>`; Traefik on
`traefik_network` with `certresolver=letsencrypt`, entrypoint `websecure`; the shared service mesh
is `letta_letta_stack` + `letta_default` (DNS names `letta:8283`, `gotenberg:3000`, `qdrant:6333`);
the `letta` container has also been found on `agent-zero-t4sx_default` — **check with
`docker inspect letta -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'`, never assume.**
Env-var change pattern that works: append to `/opt/stacks/<stack>/.env`, then
`docker compose up -d <service>` (not `docker restart`, which keeps the old env). On "endpoint
already exists in network" during recreate: disconnect the stale endpoint with force, retry.
Image builds without staging a GitHub token on the host: `git archive --format=tar <SHA> <dir> | gzip`
locally → upload via `/file/write` → verify SHA-256 → extract → `docker build`.

## 3. State of the repository (main = `8847d3b`)

Merged on 09.10.2026:

| PR | What |
|---|---|
| #26 `6577455` | PP Suite frontend (`apps/ppdocwiz`): live-mode fixes from the end-to-end test (raw Markdown builds use the current engine via `POST /api/build`; files named from HEADERDATA; no sample data shown or registered in live mode; `/api/docengine/*` same-origin proxy; PDF errors inline) + review fixes. Report: `deliverables/frontend_test_2026-10-09/TEST_REPORT.md`. |
| #27 `2c57b5d` | Inland transport SOP **WHSOP_003** + annexes A01–A07, transport validation SOP **QASOP_0XX** + A01–A06, worked example T1/T2 (`deliverables/inland_transport_2026-10/`). |
| #28 `522594a` | **DocEngine runs the current `pp-document-suite`** — `apps/wwf-docengine/engine/` is an exact copy, refreshed by `engine/sync_from_suite.sh`, held identical by `tests/test_engine_sync.py` (CI). Canon revision recorded in `docs/wwf_DOCENGINE-CANON-2026-07.md`. `fonttools==4.62.1` pinned (glyph guard). |
| #29 `8847d3b` | **RAGFlow knowledge link** (`apps/wwf-docengine/app/ragflow.py`, `/knowledge/search`, `/knowledge/health`, regulatory check cites DB01 passages, `regulatory_sources` in job results, examples slot) **+ one PDF renderer** `pp-document-suite/scripts/pp_render.py` (Gotenberg first, local LibreOffice macro fallback; `assets/lo_profile`). Runbook `server/runbooks/docengine_knowledge_and_render.md`. |

Still open from earlier work (not part of this task): draft PRs #15, #16, #17, #25 (certificate desk).

### Configuration each service reads (names only)

- **DocEngine**: `DOCENGINE_API_KEY`, `DOCENGINE_DATABASE_URL`, `DOCENGINE_OUT_DIR`, `LETTA_BASE_URL`,
  `LETTA_API_KEY`, `LETTA_READ_TIMEOUT`, `LETTA_CONNECT_TIMEOUT`, `DOCENGINE_REG_SOURCES`,
  `GOTENBERG_URL`, `GOTENBERG_USERNAME`, `GOTENBERG_PASSWORD`, `RAGFLOW_BASE_URL`, `RAGFLOW_API_KEY`,
  `RAGFLOW_REG_DATASETS` (default `a33b0812a3d411f1858cf58865604f65` = DB01_REG),
  `RAGFLOW_ECOA_DATASETS` (default `dd3ea108a3fd11f1858cf58865604f65` = eCOA_DB),
  `RAGFLOW_EXAMPLE_DATASETS` (empty), `RAGFLOW_TOP_N`.
- **ppdocwiz**: `PPDOCWIZ_API_KEY` (required), `PPDOCWIZ_COOKIE_SECURE`, `PPDOCWIZ_UI`, `PP_SUITE_DIR`,
  `PP_OUT_DIR`, `LETTA_BASE_URL`, `LETTA_TOKEN`, `LETTA_AGENT`, `DOCENGINE_URL`, `DOCENGINE_API_KEY`,
  `GOTENBERG_URL` (+ `GOTENBERG_USERNAME`/`GOTENBERG_PASSWORD`). Compose: `apps/ppdocwiz/docker-compose.yml`
  (Dockerfile build context is the repo root and expects `ppdocwiz/` — check the paths: the app
  lives at `apps/ppdocwiz/` in this repo).
- **pp_render (any client)**: `GOTENBERG_URL`, `GOTENBERG_USERNAME`, `GOTENBERG_PASSWORD`, `PP_RENDER`.

### RAGFlow (KVM4, `https://ragflow.srv1231216.hstgr.cloud`)

| Dataset | id | Notes |
|---|---|---|
| DB01_REG | `a33b0812a3d411f1858cf58865604f65` | EudraLex Vol. 4 + Annexes, EU GDP, ICH, WHO, MK law, Ph. Eur. Verified 09.10: a transport question returns EU GDP 2013/C 343/01 §9.1/9.2 and Annex 21 §5.1.3. |
| eCOA_DB | `dd3ea108a3fd11f1858cf58865604f65` | 283 CoAs. **Chunk text is never a source of values** (dataset's own rule). |
| stability | `86a119aca4ca11f192a3d5bae3c9970f` | stability time points — never release results |
| water | `d190b27ca3d211f1858cf58865604f65` | empty |

RAGFlow compose override: `server/ragflow/docker-compose.override.yml` (container `ragflow-cpu`, API on
9380 inside, Traefik routes `ragflow.` and `ragflow-mcp.`). DocEngine needs a **RAGFlow API key**
(RAGFlow UI → avatar → API); create one for the DocEngine if Environment F does not already hold one.

## 4. Deployment plan (do it in this order, verify each step)

1. **Inventory**: `docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'`, `docker network ls`,
   `ls /opt/stacks`. Compare with the runbook §0 table. Record what is missing.
2. **Gotenberg** (runbook §2): pin an exact `gotenberg/gotenberg:8.x.y` tag (resolve it with
   `docker pull gotenberg/gotenberg:8 && docker image inspect` — never `:latest` in the compose);
   on the stack network as `gotenberg`; public route `render.srv1231216.hstgr.cloud` behind Traefik
   basic auth (generate the password on the host; store user/password as server env, and tell the
   Head of QC the variable names to add to Environment F as `GOTENBERG_USERNAME`/`GOTENBERG_PASSWORD`).
   Verify: `/health` → up; render a real SOP through it: `GOTENBERG_URL=… python3
   pp-document-suite/scripts/pp_render.py deliverables/inland_transport_2026-10/docx/WHSOP_003.docx /tmp/w.pdf`
   → "rendered via gotenberg", 15 pages, TOC filled (`pdftotext /tmp/w.pdf - | grep -cE '\.{5,}'` → 26).
   If the TOC comes back empty, Gotenberg's `updateIndexes` is not honoured by that version: pick a
   version that supports it, do not accept an empty TOC.
3. **DocEngine** from `main` (`apps/wwf-docengine`, Dockerfile in that directory): build the image
   from the committed tree at `8847d3b` (git-archive method), set the env above, join RAGFlow's
   network, recreate. Verify (runbook §4): `/health` shows `"ragflow": true` and the new engine label;
   `/knowledge/health` reachable; `/knowledge/search` regulatory returns EU GDP §9; eCOA search for
   `SJ102501` (keyword) returns certificates; Library PDF of a built document has its TOC.
4. **ppdocwiz** from `main`: build per `apps/ppdocwiz/Dockerfile`, env above, behind Traefik; verify
   sign-in, a Builder build with `.pdf` download (TOC filled), Questionnaire loads `sop_qc` through
   `/api/docengine`, Library lists documents.
5. **One questionnaire workflow end to end** (needs Letta): the job result has
   `regulatory_sources` per section and empty `knowledge.notes`.
6. Record everything in Open Brain (one record: what runs, versions, verification results, routes),
   and add a short dated "Deployed" note to `server/runbooks/docengine_knowledge_and_render.md` via a PR.

**Safety**: back up before replacing anything (`docker inspect` saved, compose files copied with a
timestamp, `pg_dump -Fc` of the DocEngine database before migrating). Change one service at a time.
Do not touch the WWF production backend/frontend, the Letta server image, or RAGFlow's own
containers except to read their network names. If a step would restart something other than the
service being deployed, ask first.

## 5. Things learned this session that save time

- Cloud sessions: Playwright cannot always reach public HTTPS through the proxy — verify deployed
  frontends with `curl`. GitHub GraphQL is blocked; use `gh api` REST.
- Local DocEngine test run: Postgres 16 is installed in the container image; start it as the
  `postgres` user from a postgres-readable path, then
  `DOCENGINE_DATABASE_URL=postgresql://docengine@127.0.0.1:5432/docengine pytest tests` in
  `apps/wwf-docengine` (venv with its `requirements.txt`). Suites: suite 22, DocEngine 66, ppdocwiz 40.
- **Never** a bare `soffice --convert-to pdf` (empty TOC). Use `pp_render.py`. Two concurrent local
  soffice instances hang — ppdocwiz serialises renders.
- The glyph guard needs `fontTools`; it now enforces the house rule (letters, digits, № must be in
  the declared face; symbols ☐ ✎ ≤ may fall back).
- `apps/wwf-docengine/engine/` must stay identical to `pp-document-suite/` — after any suite change
  run `engine/sync_from_suite.sh` or CI fails.

## 6. Security — act on it, do not repeat it

- Open Brain contains several **plaintext live secrets** in older records (server root password,
  Agent Zero web login, service passwords). The Head of QC was advised to rotate them. Never copy
  them anywhere; do not quote them back.
- On 09.10.2026 he shared a Google Doc of API keys by link; it was **not opened**. He was advised to
  delete it and rotate the keys in it. Do not open it.
- Secrets live in Environment F (environment variables / network secrets) and on the server in
  `/opt/stacks/<stack>/.env` (0600 root). Nowhere else.

## 7. Done means

Gotenberg, DocEngine and ppdocwiz running on KVM4 from `main`, each verified as in §4; the public
render route working with basic auth; the variable names the Head of QC must add to Environment F
named to him in one short message; Open Brain updated; a PR with the runbook "Deployed" note merged
on his word.

## 8. Work log of the session that wrote this (08–09.10.2026)

| Work | Where |
|---|---|
| PP Suite frontend (Hybrid v2) built, end-to-end tested in live mode, 9 defects fixed, reviewed (10 findings, 8 fixed) | PR #26; `deliverables/frontend_test_2026-10-09/` |
| WHSOP_003 inland transport of narcotic substances (MoIA police escort, licensed carrier, paper-based, Euro pallets 8/4 cartons × 10 IMB bags of 401.0 g ± 3 %, single-use + USB loggers, retention samples for buyer and retailer, label-template references) + annexes A01–A07 | PR #27; `deliverables/inland_transport_2026-10/md/` |
| QASOP_0XX transport validation (lane OQ + PQ, active/passive vehicle) + annexes A01–A06 | PR #27 |
| Worked example Tranche 1 (TR-20261020-001: 20 lots, 1 471.51 kg, 3 669 bags, 373 cartons, 47 pallets, 2 vehicles, 40 retention samples) and Tranche 2 (TR-20261027-001: 26 lots, 2 677.36 kg, 6 677 bags, 679 cartons, 85 pallets, 3 vehicles, 52 samples); final package incl. T1 individual annexes and a 64-page duplex T1 binder (every annex on an odd page) | `deliverables/inland_transport_2026-10/FINAL_2026-10-09/` |
| Engine fixes: spacing/keep rules, `[[BOX]]` label spaces, full-width annex tables, cover band; bag model (partial last bag) | PRs #27, #28 |
| DocEngine → current suite (canon revision), glyph guard per house rule, USP `<1079.2>` fix | PR #28 |
| DocEngine ↔ RAGFlow link; `pp_render` single renderer; CLAUDE.md §9 | PR #29 |
| Head of QC corrections this session: QC sample transport is a separate SOP (PP-QC-SOP-025); no private security company, MoIA police only; carrier is an official licensed transport company (likely Kuehne + Nagel, unconfirmed); emails short; do not track approval/draft status; render the same way on every device | Open Brain, `claude-code-desk` records of 09.10.2026 |
