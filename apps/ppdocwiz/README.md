# PP Doc Wiz — Purely Plant Document Wizard

A standalone app that puts a **front door** on the `pp-document-suite` engine and the Letta document
agents. One container: **frontend** (single-file SPA) + **backend gateway** (FastAPI) with the engine
**embedded**.

Two ways to create a document:
- **🧩 Wizard** — deterministic (no LLM). Pick a doc type (SOP / Annex / Form), fill guided header
  fields, add sections with **text / form / table** blocks, → **Generate** → the engine builds the
  house-style `.docx`, runs `pp_verify` (must be `RESULT: PASS`), and offers `.docx` / `.pdf` download.
- **💬 Chat** — freeform. Talk to a Letta agent (default `qms_docx_formatter`); it composes the
  bilingual Markdown and builds the doc via the `build_pp_document` tool. Requires `LETTA_BASE_URL`.

## Architecture

```
 browser ──HTTP──►  ppdocwiz (FastAPI :8770)
                      ├── /api/wizard/build  → wizard.compose_markdown() → pp-document-suite engine (in-process) → .docx + pp_verify
                      ├── /api/download/…     → .docx / .pdf (LibreOffice)
                      └── /api/chat           → Letta REST (/v1/agents/…/messages) → build_pp_document tool
```

The wizard path needs **no Letta** — it builds locally in the container. The chat path proxies Letta.

## Run (dedicated container on the Letta network)

```bash
# from the repo root. PPDOCWIZ_API_KEY is required — compose hard-fails without it.
PPDOCWIZ_API_KEY=$(openssl rand -base64 32) \
LETTA_BASE_URL=https://ui.srv1231216.hstgr.cloud \
LETTA_NETWORK=$(docker network ls --format '{{.Name}}' | grep -i letta | head -1) \
  docker compose -f ppdocwiz/docker-compose.yml up -d --build
curl -s 127.0.0.1:8770/api/health          # {"ok":true,"pdf":true,...}
```

The published port is **loopback-only** (`127.0.0.1:8770`), matching the house rule that Traefik is
the sole public ingress — so `http://<host>:8770` no longer reaches it from another machine. Use
either:

```bash
ssh -L 8770:127.0.0.1:8770 <host>          # then open http://127.0.0.1:8770
```

or wire the Traefik labels in the compose file, which need **two** changes (join the network Traefik
is on, *and* uncomment the labels including `entrypoints`/`certresolver`) — see the comment there.

## Run locally (dev)

```bash
pip install -r ppdocwiz/requirements.txt      # pinned; do not install unpinned
cd ppdocwiz/backend
PPDOCWIZ_API_KEY=dev-key-change-me \
PPDOCWIZ_COOKIE_SECURE=0 \
PP_SUITE_DIR=$(cd ../../pp-document-suite && pwd) uvicorn app:app --reload --port 8770
```

## Config (env)

| Var | Purpose |
|---|---|
| `PPDOCWIZ_API_KEY` | **required** — shared secret for every gated route. Generate with `openssl rand -base64 32`; store in `/opt/stacks/ppdocwiz/.env` (0600 root). Unset ⇒ the service 503s everything. |
| `PPDOCWIZ_COOKIE_SECURE` | `0` only for plain-HTTP loopback development; default is a `Secure` cookie |
| `PP_SUITE_DIR` | path to `pp-document-suite` (auto-detected; `/opt/pp-document-suite` in the image) |
| `PP_OUT_DIR` | where built docs are written (`/data` volume in the image) |
| `LETTA_BASE_URL` | Letta REST base — **enables the Chat tab** |
| `LETTA_TOKEN` | only if the Letta server requires auth |
| `LETTA_AGENT` | **allowlist** of agents the chat proxy may reach, comma-separated (default `qms_docx_formatter`). Not a fallback: a request naming anything else is refused with 400. |

## API

Every route except `/api/health`, `/api/session` and `/` requires a credential, in either form:

- `X-API-Key: $PPDOCWIZ_API_KEY` — for machine callers. Identical contract to the DocEngine
  (`apps/wwf-docengine/app/security.py`), so a caller needs no special-casing between them.
- the `ppdocwiz_session` cookie — for the browser. `POST /api/session {"key": "..."}` exchanges the
  key for an **HttpOnly** cookie whose value is HMAC-derived from the key, never the key itself.
  This exists because the download links are plain `<a href>` anchors and a browser cannot put a
  header on an anchor navigation; the cookie rides both `fetch` and navigations.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | — | liveness (Letta on/off, PDF on/off). Open **by design**: the compose healthcheck calls it with no headers. Returns no filesystem paths. |
| POST | `/api/session` | — | `{key}` → sets the HttpOnly session cookie (this *is* the authenticator) |
| GET | `/api/doctypes` | ✔ | doc types for the wizard |
| GET | `/api/example` | ✔ | a ready example payload + its Markdown |
| POST | `/api/wizard/preview` | ✔ | payload → Markdown (no build) |
| POST | `/api/wizard/build` | ✔ | payload → `.docx` + verify (`{ok,verify,doc_id,download_*}`) |
| GET | `/api/download/{id}.docx\|.pdf` | ✔ | download a built doc (`.docx`/`.pdf` only; name is sanitised and containment-checked) |
| POST | `/api/chat` | ✔ | `{message,agent}` → Letta agent reply (+ built doc). `agent` must be in the `LETTA_AGENT` allowlist |

```bash
# machine caller
curl -sS -H "X-API-Key: $PPDOCWIZ_API_KEY" http://127.0.0.1:8770/api/doctypes
# browser-equivalent flow
curl -sS -c /tmp/j -X POST http://127.0.0.1:8770/api/session \
     -H 'Content-Type: application/json' -d "{\"key\":\"$PPDOCWIZ_API_KEY\"}"
curl -sS -b /tmp/j http://127.0.0.1:8770/api/doctypes
```

If `PPDOCWIZ_API_KEY` is unset the service answers **503 to every gated route** — it fails closed
rather than running open.

## Notes
- The engine is the **same** `pp-document-suite` master; the wizard just composes the Markdown the
  engine already consumes, so wizard output is byte-for-intent identical to hand-authored docs.
- Native OMML equations need Office `MML2OMML.XSL` (Windows) — on Linux they fall back to text, as
  documented for the engine. PDF works here via LibreOffice + Carlito/Liberation fonts.
- MVP scope: wizard supports header + text/form/table blocks. Extend `wizard.py` (`DOCTYPES`,
  `compose_markdown`) and the frontend block editors for more constructs (status grids, sign-off, charts).
