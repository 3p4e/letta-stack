# DocEngine Studio

An advanced operator UI and machine gateway in front of the Purely Plant
document engine. It is deliberately additive: the engine itself (`apps/wwf-docengine`,
Line B) is never modified, and every generated document still has to pass the
engine's own `pp_verify` gate before the Studio will show it.

Design authority: `docs/DOCENGINE_UI_DESIGN_2026-09-30.md` in this repository.

## What it gives you

- **Operator UI** (vanilla-JS PWA, no build step) for the whole controlled
  document lifecycle: author, review, approve, sign, supersede.
- **Registry** with an additive lifecycle on top of the engine
  (`draft → in_review → approved → effective → superseded`), approvals and
  e-signature records, all hash-chained.
- **Knowledge assistant** with two explicitly separated lanes:
  - **official** - RAGFlow. Answers carry citations. If no verified evidence
    exists the request **fails closed** (HTTP 503) instead of guessing.
  - **advisory** - Letta. Clearly labelled as not evidence.
- **Model routing** with producer/checker separation: authoring functions run on
  Moonshot; verification functions run on DeepSeek at temperature 0. The router
  refuses to move a checker onto the producer provider.
- **Machine surface**: an MCP (JSON-RPC 2.0) endpoint with scope-filtered tools,
  plus OAuth2 client-credentials clients with **capability scopes** (never
  roles). Machine clients can never approve or sign.
- **Audit**: an append-only hash chain with a `/api/audit` verifier.

## Security model

Three ways in, in priority order:

1. **Browser session** - POST the studio key to `/api/session`; you get a signed
   HttpOnly cookie. This is what the PWA uses.
2. **Identity headers** from an upstream proxy (`X-Auth-Request-User`,
   `X-User-Role`, ...), i.e. the same pattern the WWF stack already uses.
3. **Machine bearer token** - `Authorization: Bearer <client_id>:<client_secret>`.
   Scopes are enforced per tool and per route.

The studio key is compared in constant time. Secrets are stored only as hashes.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
STUDIO_API_KEY=dev DOCENGINE_ENDPOINT=http://localhost:8000 \
  DOCENGINE_API_KEY=... uvicon app.main:app --reload --port 8080
```

Open http://localhost:8080, sign in with `dev`.

## Test

```bash
PYTHONPATH=. pytest tests -q
```

The suite runs against a faked upstream DocEngine, so it needs no network and no
real engine: it asserts the *contract* (fail-closed lanes, lifecycle rules,
role separation, audit chain integrity), not the engine's behaviour.

## Configuration

All configuration is environment-driven (see `.env.example`):

| Variable | Purpose |
| --- | --- |
| `DOCENGINE_ENDPOINT` | Line B DocEngine base URL |
| `DOCENGINE_API_KEY` | engine shared key |
| `LETTA_ENDPOINT` / `LETTA_API_KEY` / `LETTA_ADVISORY_AGENT` | advisory lane |
| `RAGFLOW_ENDPOINT` / `RAGFLOW_API_KEY` | official lane (unavailable until set) |
| `STUDIO_API_KEY` | studio key; enables sessions |
| `STUDIO_TRUST_HEADERS` | accept identity headers from an upstream proxy |
| `STUDIO_SESSION_TTL` | session lifetime in seconds |
| `STUDIO_DB_PATH` / `STUDIO_DATA_DIR` | SQLite state location |

## Deploy

`docker-compose.yml` joins the existing `weekly_weed_flow_internal` and `ai-net`
networks, publishes no host port, and is fronted by the host's Traefik exactly
like every other WWF service.

```bash
cd /opt/stacks/docengine-studio
cp .env.example .env   # fill in DOCENGINE_API_KEY and STUDIO_API_KEY
docker compose up -d --build
```

## Scope boundaries

- The Studio never writes to the engine's own store; it keeps its state in
  SQLite under `/data`.
- Machine clients cannot approve or sign; those are human actions and are
  recorded with actor, role and timestamp.
- Nothing is committed to the repository by the Studio; controlled documents
  remain in the engine's output directory and its register.
