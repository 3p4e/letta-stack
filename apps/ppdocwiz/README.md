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
# from the repo root:
LETTA_BASE_URL=https://ui.srv1231216.hstgr.cloud \
LETTA_NETWORK=$(docker network ls --format '{{.Name}}' | grep -i letta | head -1) \
  docker compose -f ppdocwiz/docker-compose.yml up -d --build
curl -s localhost:8770/api/health          # {"ok":true,"pdf":true,...}
# open http://<host>:8770  (or wire the Traefik labels in the compose for HTTPS)
```

## Run locally (dev)

```bash
pip install fastapi "uvicorn[standard]" python-docx lxml
cd ppdocwiz/backend
PP_SUITE_DIR=$(cd ../../pp-document-suite && pwd) uvicorn app:app --reload --port 8770
```

## Config (env)

| Var | Purpose |
|---|---|
| `PP_SUITE_DIR` | path to `pp-document-suite` (auto-detected; `/opt/pp-document-suite` in the image) |
| `PP_OUT_DIR` | where built docs are written (`/data` volume in the image) |
| `LETTA_BASE_URL` | Letta REST base — **enables the Chat tab** |
| `LETTA_TOKEN` | only if the Letta server requires auth |
| `LETTA_AGENT` | default agent for chat (`qms_docx_formatter`) |

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | status (suite path, Letta on/off, PDF on/off) |
| GET | `/api/doctypes` | doc types for the wizard |
| GET | `/api/example` | a ready example payload + its Markdown |
| POST | `/api/wizard/preview` | payload → Markdown (no build) |
| POST | `/api/wizard/build` | payload → `.docx` + verify (`{ok,verify,doc_id,download_*}`) |
| GET | `/api/download/{id}.docx\|.pdf` | download a built doc |
| POST | `/api/chat` | `{message,agent}` → Letta agent reply (+ built doc) |

## Notes
- The engine is the **same** `pp-document-suite` master; the wizard just composes the Markdown the
  engine already consumes, so wizard output is byte-for-intent identical to hand-authored docs.
- Native OMML equations need Office `MML2OMML.XSL` (Windows) — on Linux they fall back to text, as
  documented for the engine. PDF works here via LibreOffice + Carlito/Liberation fonts.
- MVP scope: wizard supports header + text/form/table blocks. Extend `wizard.py` (`DOCTYPES`,
  `compose_markdown`) and the frontend block editors for more constructs (status grids, sign-off, charts).
