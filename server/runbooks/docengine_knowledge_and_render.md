# DocEngine on KVM4 — RAGFlow knowledge link and Gotenberg PDF (runbook, 09.10.2026)

Head of QC, 09.10.2026: the document engine must have a persistent, seamless connection to the
RAGFlow regulatory database (and eCOA_DB), checkable while content is generated; example
documents will follow; install whatever is missing after the server reinstall.

The code is in `apps/wwf-docengine` (`app/ragflow.py`, pipeline regulatory check,
`/knowledge/*` routes). This runbook is the server side. Every value marked `<…>` comes from the
server; no secret goes into this repository.

## 0. Inventory — what must be running

Hostinger VPS API (`GET https://developers.hostinger.com/api/vps/v1/virtual-machines/1231216/docker`)
or `docker ps` on the host. Required:

| Service | Why | If missing |
|---|---|---|
| `letta` (+ `letta-postgres`) | the DocEngine's authoring and checking agents | redeploy the letta stack |
| `ragflow-cpu` (+ its mysql, es/infinity, minio, redis) | DB01_REG, eCOA_DB, examples | redeploy `/opt/stacks/ragflow` with `server/ragflow/docker-compose.override.yml` |
| `gotenberg` | DocEngine Library "PDF" (DOCX → PDF) | §2 |
| `wwf-docengine` + its Postgres | the engine | redeploy the WWF stack |
| `ppdocwiz` | the PP Suite frontend | `apps/ppdocwiz/docker-compose.yml` |

The 2026-08-09 container snapshot (`server/LIVE_CONTAINERS_2026-08-09.md`) lists **no Gotenberg**
in the letta stack although `GOTENBERG_URL=http://gotenberg:3000` is configured there.

## 1. RAGFlow → DocEngine

1. In RAGFlow (https://ragflow.srv1231216.hstgr.cloud), avatar › **API** › create an API key for
   the DocEngine. Read-only use: it only calls `POST /api/v1/retrieval` and `GET /api/v1/datasets`.
2. In the DocEngine stack's `.env` (0600 root):
   ```
   RAGFLOW_BASE_URL=http://ragflow-cpu:9380        # in-stack (needs step 3); or https://ragflow.srv1231216.hstgr.cloud
   RAGFLOW_API_KEY=<the key from step 1>
   # defaults, override only if the datasets are recreated:
   # RAGFLOW_REG_DATASETS=a33b0812a3d411f1858cf58865604f65    # DB01_REG
   # RAGFLOW_ECOA_DATASETS=dd3ea108a3fd11f1858cf58865604f65   # eCOA_DB
   # RAGFLOW_EXAMPLE_DATASETS=                                 # §3
   ```
3. In-stack address: join the DocEngine service to RAGFlow's network in its compose
   (`networks: [default, ragflow]` with `ragflow: {external: true, name: <ragflow network>}`; the
   name from `docker network ls | grep ragflow`). The public URL works without this, through Traefik.
4. `docker compose up -d wwf-docengine`, then verify (§4).

## 2. Gotenberg — the one PDF renderer for every service and every device

Head of QC, 09.10.2026: rendering must not depend on whether the current device has Word or
LibreOffice (phone, laptop, cloud session). Every renderer in the repository goes through
`pp-document-suite/scripts/pp_render.py`, which uses this service when `GOTENBERG_URL` is set and
falls back to local LibreOffice only when it is not. Users: ppdocwiz downloads, the DocEngine
Library "PDF", the engine CLI, and Claude sessions.

Head of QC, 10.10.2026: the service is **`pp-render`** — Gotenberg 8.37.0 (LibreOffice) with the house fonts
built in. Definition: `server/render/` (`Dockerfile`, `compose.yaml`, `get_fonts.py`); on KVM4 `/opt/stacks/pp-render`,
container `gotenberg` on `ai-net`, **public HTTPS route behind basic auth** (`render.srv1231216.hstgr.cloud`) so a phone,
a laptop or a cloud session can render too. The basic-auth hash is in `/opt/stacks/pp-render/.env`, the user/password
in `credentials.env` (both 0600, host only).

**Fonts are what make the PDF match Word.** The image is built from `/opt/fonts/pp` (never from this repository):
- `free/` — `get_fonts.py`: Microsoft core fonts (Arial, Arial Black, Times New Roman, Courier New, Verdana, Trebuchet,
  Georgia …), the CoQ/iCoA faces (Montserrat, Orbitron, Roboto Mono, Roboto Condensed — static weights, not variable
  fonts), Carlito, and the WWF web faces.
- `licensed/` — copied from a licensed Windows/Office PC: Calibri (+Light), Arial Narrow, Cambria Math, Segoe UI,
  Segoe UI Symbol, MS Gothic, Tahoma, Arial Rounded MT Bold.
Add a font: put the file in `/opt/fonts/pp/…`, then
`docker build -t pp-render:8.37.0-fonts.<n+1> -f /opt/stacks/pp-render/Dockerfile /opt/fonts/pp`, set the tag in
`compose.yaml`, `docker compose up -d`. Only symbols the faces lack (✓ ✗ ★ ⟨ ⟩) may fall back to DejaVu.

In-stack services use `GOTENBERG_URL=http://gotenberg:3000` (no auth: internal network only).
Anything outside the stack uses `GOTENBERG_URL=https://render.srv1231216.hstgr.cloud` with
`GOTENBERG_USERNAME` / `GOTENBERG_PASSWORD`. For Claude cloud sessions, put those three in the
environment's settings (Network secrets) and allow `render.srv1231216.hstgr.cloud` in its network
policy; `pp_render` then renders on KVM4 with no local office suite at all.

Checks: `curl -s http://gotenberg:3000/health` → `{"status":"up"}`; from outside,
`python3 pp-document-suite/scripts/pp_render.py any.docx out.pdf` prints `rendered via gotenberg`,
and an SOP's PDF has its table of contents filled (`updateIndexes`).

## 3. Example documents (next)

Create a RAGFlow dataset `DB_EXAMPLES` holding **approved, effective** house documents only
(SOPs, annexes, reports — the PDFs as issued). Parser: General, chunk ~500 tokens, metadata
`doc_code`, `doctype`, `version`. Put its id in `RAGFLOW_EXAMPLE_DATASETS` and restart. From then
on each author agent receives the three closest examples, with the instruction to take structure
and style only — never a value, batch, name, date or result.

## 4. Verification (all through the DocEngine, with its key)

```bash
H="X-API-Key: $DOCENGINE_API_KEY"; D=http://wwf-docengine:8000
curl -s $D/health                                   # "ragflow": true
curl -s -H "$H" $D/knowledge/health                 # configured true, reachable true
curl -s -H "$H" -H 'Content-Type: application/json' $D/knowledge/search \
  -d '{"corpus":"regulatory","question":"transport of medicinal products temperature conditions"}'
#   → EU GDP 2013/C 343/01 §9.1/9.2, EU GMP Annex 21 §5.1.3 (as retrieved on 09.10.2026)
curl -s -H "$H" -H 'Content-Type: application/json' $D/knowledge/search \
  -d '{"corpus":"ecoa","question":"SJ102501","keyword":true}'
#   → certificates for the lot; the response note: chunk text is not a source of values
```
Then one questionnaire workflow end to end: the job result's `regulatory_sources` lists the DB01
passages each section was checked against, and `knowledge.notes` is empty.

## Rollback

Unset `RAGFLOW_BASE_URL` / `RAGFLOW_API_KEY` and restart: the regulatory check returns to the
checker agent's attached Letta sources (`DOCENGINE_REG_SOURCES`), and every job records that it did.

## Deployed — 09.10.2026 (from `main` 5ecf6a6)

| Service | Where | Image | Address |
|---|---|---|---|
| Gotenberg | `/opt/stacks/gotenberg` | `gotenberg/gotenberg:8.37.0` | `http://gotenberg:3000` on `ai-net`; `https://render.srv1231216.hstgr.cloud` (basic auth, user `pp`, credentials in `/opt/stacks/gotenberg/credentials.env` on the host) |
| pp-docengine | `/opt/stacks/pp-docengine` (+ own Postgres 16 `pp-docengine-db`) | `pp-docengine:5ecf6a6` (`apps/wwf-docengine`) | `http://pp-docengine:8000` on `ai-net`, no public route |
| ppdocwiz | `/opt/stacks/ppdocwiz` | `ppdocwiz:5ecf6a6` (`apps/ppdocwiz`) | `https://docwiz.srv1231216.hstgr.cloud` |

The WWF stack's `wwf-docengine` (`growflow-docengine:v26`, built from WEEKLY_WEED_FLOW) is **left
untouched** (Head of QC, 09.10.2026): it is the WWF-integrated engine, and this one will be merged into
WWF later. Images were built on the host from `git archive` tarballs, SHA-256 checked on both sides.

Verified: Gotenberg `/health` up; public route 401 without or with a wrong password; WHSOP_003 through
`pp_render` over the public route → "rendered via gotenberg", 15 pages, TOC 26 lines. pp-docengine
`/health` `"ragflow": true`; `/knowledge/health` reachable; regulatory search → EU GDP §9.2/§9.1;
eCOA `SJ102501` (keyword) → Farmahem certificates with the "not a source of values" note. ppdocwiz:
sign-in, Builder build of WHSOP_003 (verify PASS, PDF TOC filled), Questionnaire `sop_qc` via
`/api/docengine`, Library.

Open: the questionnaire workflow end to end fails at the first Letta call — the `gf_` agents run
`moonshot/kimi-k2.6` through LiteLLM and Moonshot answers "account suspended due to insufficient balance".
Rerun §4's last check after the balance is restored or the model is changed. Known defect: on an empty
database the two uvicorn workers race on `CREATE SCHEMA` at first start (one worker respawns).

## Deployed — 10.10.2026: renderer replaced by `pp-render` (LibreOffice + house fonts)

Head of QC, 10.10.2026, after a side-by-side test against Word-made PDFs (quarantine label sheet, PP-QC-SOP-017,
QCSOP_018 A01, WHSOP_003) with the real fonts installed on both candidates: LibreOffice matched Word (23/23 and
14/14 pages, label layout identical, Arial Narrow and Calibri used); OnlyOffice 9.4 did not (19/23 pages, right-hand
column cut off, label title split, Arial Narrow ignored). OnlyOffice and its gateway were removed; the plain
Gotenberg of 09.10 was replaced by `pp-render:8.37.0-fonts.1` (166 free + 20 licensed fonts). Same addresses as
before: `http://gotenberg:3000` inside, `render.srv1231216.hstgr.cloud` outside, same credentials.

Verified: public route 401 without / with a wrong password; WHSOP_003 through the public route → "rendered via
gotenberg", 15 pages, TOC 26 lines, Calibri and Arial Narrow embedded; label, SOP-017, QCSOP_018 A01 → 1, 23, 14 pages,
real fonts embedded; ppdocwiz Builder PDF and pp-docengine Library PDF → 15 pages, TOC 26 lines.

