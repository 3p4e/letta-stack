# DEPLOY — Purely Plant Document Suite on the Letta stack

Two deployment shapes. **A** is what is already live (in‑place on the Letta volume, no rebuild).
**B** is the cleaner long‑term shape (a dedicated container). Both make the builder tool functional
for the Letta document agents.

---

## A. In‑place on the Letta volume — LIVE (permanent, no docker rebuild)

The engine is installed inside the Letta server container on its **persistent** `/root/.letta`
volume (the rest of the container FS is throwaway overlay), so it survives container **recreation**:

- `/root/.letta/pp-document-suite/` — the engine (scripts + `assets/PP_BASE_TEMPLATE.docx`).
- `/root/.letta/pp-libs/` — `python-docx` + `lxml` (added to `sys.path` by the tool).
- `/root/.letta/pp-out/` — generated `.docx` output.

Registered Letta tools (source stored in Letta's DB → also persistent), attached to the document
agents (`qms_docx_formatter`, `pharma_docx_formatter`, and the five `pp_annex_*` agents):

- **`build_pp_document(markdown, out_name)`** — bilingual Markdown → house‑style `.docx`; runs the QC
  gate; returns `{ok, verify, path, bytes}`.
- **`fetch_pp_document(path)`** — returns a produced `.docx` as base64 for download/attachment.

Shared memory block **`pp_house_rules`** (navy `#2B547E`, MK‑first, abbreviations untranslated,
9‑section SOP, font floor, layout) is attached to all document agents.

Re‑deploy after an *image rebuild* (which replaces the volume’s companion venv) is only needed if
`/root/.letta/pp-libs` is cleared — re‑run the volume install (`pip install --target=/root/.letta/pp-libs python-docx`).

## B. Dedicated container in the Letta stack (recommended long‑term)

Cleaner isolation, reproducible from the repo, upgraded by `docker compose build`.

```bash
# on KVM4, from the repo's pp-document-suite/ directory:
LETTA_NETWORK=$(docker network ls --format '{{.Name}}' | grep -i letta | head -1)
LETTA_NETWORK=$LETTA_NETWORK docker compose -f docker-compose.letta.yml up -d --build
docker exec pp-document-suite curl -s localhost:8600/health     # {"ok": true, ...}
```

This runs `integrations/service.py` (FastAPI) on `:8600`, on the Letta network, so agents reach it at
`http://pp-document-suite:8600`. Then register the **REST** variant of the tool so agents call the
container instead of building in‑sandbox:

```bash
export LETTA_BASE_URL=https://ui.srv1231216.hstgr.cloud
export LETTA_MODE=rest
export QMS_API_BASE=http://pp-document-suite:8600
export PP_AGENTS=qms_docx_formatter,pharma_docx_formatter
python3 integrations/letta_register.py
```

`service.py` endpoints: `POST /build` (→ `{ok, path, verify}`), `POST /build.docx` (streams the file),
`POST /build.pdf` (LibreOffice), `GET /health`.

### A vs B

| | A — in‑place on volume | B — dedicated container |
|---|---|---|
| Live now | ✅ | needs one `docker compose up` |
| Survives container recreate | ✅ (`/root/.letta` volume) | ✅ (own image + volume) |
| Survives Letta image rebuild | re‑install libs only | ✅ |
| Isolation from Letta runtime | shares the Letta container | ✅ separate container |
| Tool variant | `build_pp_document` (in‑sandbox) | `build_pp_document_via_api` (REST) |

Keep the repo's `pp-document-suite/` as the master; both shapes deploy *from* it.
