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

## 2. Gotenberg

On the letta stack's network (the DocEngine and the Letta sandbox both use `http://gotenberg:3000`):
```yaml
  gotenberg:
    image: gotenberg/gotenberg:8.<x>.<y>   # pin the exact current 8.x tag; never :latest
    restart: unless-stopped
    command: ["gotenberg", "--api-timeout=120s"]
    networks: [default]                    # no published port: internal only
```
DocEngine `.env`: `GOTENBERG_URL=http://gotenberg:3000` (and the DocEngine on that network).
Check: `curl -s http://gotenberg:3000/health` from a container on the network → `{"status":"up"}`.

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
