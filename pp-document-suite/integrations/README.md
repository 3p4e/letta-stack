# integrations/ — working code to run the engine off-Claude

Concrete, runnable companions to `../PORTABILITY.md` and `../LETTA_INTEGRATION.md`. These are the
actual files those docs describe — not snippets.

| File | What it is | Needs |
|---|---|---|
| **`pp_tool.py`** | The builder as one portable tool function (`build_pp_document` in-process, `build_pp_document_via_api` over HTTP) + a framework-agnostic `TOOL_SCHEMA`. Also a CLI. | in-process: `python-docx`, `lxml`; rest: `requests` |
| **`letta_register.py`** | Registers the builder as a Letta custom tool and attaches it to your agents by name, via the documented Letta REST API. | `requests`, a running Letta server |
| **`service.py`** | FastAPI build service: `POST /build`, `/build.docx`, `/build.pdf`, `GET /health`. One engine shared by many clients. | `fastapi`, `uvicorn`, `python-docx`, `lxml`; PDF needs `soffice` |
| **`verify_letta_connection.py`** | READ-ONLY smoke check: is Letta reachable + authenticated, do the target agents exist, is the builder tool already registered. Run it before `letta_register.py`. Stdlib only; never prints the key. | a running Letta server (or a cloud key) |

## Use as a tool for any model/agent (OpenAI, Gemini, Llama, Mistral, LangChain, Agent Zero…)

```python
from integrations.pp_tool import build_pp_document, TOOL_SCHEMA
# hand TOOL_SCHEMA to the model as a function/tool; when it calls back, run:
result = build_pp_document(markdown, "out.docx")   # {ok, out_path, verify}
```

## Check the Letta connection first (read-only, mutates nothing)

```bash
# Cloud: set LETTA_API_KEY (sk-let…) and the base URL defaults to https://api.letta.com
# Self-hosted: set LETTA_BASE_URL (+ LETTA_TOKEN if the server needs auth)
export LETTA_API_KEY=sk-let...            # or LETTA_BASE_URL=https://<letta-host> LETTA_TOKEN=...
python3 integrations/verify_letta_connection.py
# -> reports reachability, auth, which target agents exist, and whether the tool is registered.
```

Note: a Letta **Cloud** key and a **self-hosted** server are different workspaces with different
agents. Point the smoke check (and `letta_register.py`) at whichever one actually hosts your
document agents.

## Wire into your Letta agents

```bash
export LETTA_BASE_URL=https://<your-letta-host>
export LETTA_TOKEN=<token>                 # if the server requires auth
export LETTA_MODE=rest                      # 'rest' (default) or 'inprocess'
export QMS_API_BASE=http://<build-service>:8600
export PP_AGENTS=qms_docx_formatter,pharma_docx_formatter
python3 integrations/letta_register.py
```

`rest` mode registers the HTTP variant (the Letta sandbox needs only `requests` + a reachable build
service — recommended). `inprocess` mode registers the direct variant (the Letta host then needs
`python-docx` and the suite at `$PP_SUITE_DIR`). After attaching, write the house rules into each
agent's persona/core memory so a stateful agent remembers them across sessions.

### Reaching a self-hosted Letta behind a runner / Traefik

When the Letta Docker stack sits behind a reverse proxy (Traefik) or you enter through a runner,
point `LETTA_BASE_URL` at that entrypoint and let the proxy route by **Host**. Both
`verify_letta_connection.py` and `letta_register.py` honour:

```bash
export LETTA_BASE_URL=https://<runner-or-traefik-entrypoint>   # the reachable front door
export LETTA_HOST_HEADER=letta.internal                        # Traefik Host rule for the letta service
export LETTA_EXTRA_HEADERS='X-Runner-Token: <token>'           # any auth the runner itself requires
export LETTA_TOKEN=<letta-server-token>                        # or LETTA_API_KEY
python3 integrations/verify_letta_connection.py                # read-only, confirms routing works
```

`LETTA_HOST_HEADER` sets the HTTP `Host:` so Traefik selects the `letta` container even when the URL
is a runner/IP; `LETTA_EXTRA_HEADERS` (`'K: v; K2: v2'`) adds any front-door auth. Nothing is guessed —
you supply the real entrypoint and routing values.

## Stand up the build service

```bash
pip install fastapi uvicorn python-docx lxml
uvicorn integrations.service:app --host 0.0.0.0 --port 8600
curl -s localhost:8600/health
curl -s -X POST localhost:8600/build -H 'content-type: application/json' \
     -d '{"markdown":"<!--HEADERDATA\ncode: T\nversion: 01\ndoctype: ANNEX\n-->\n# 1. X | X\na ||| b","name":"t"}'
```

## Security

All hosts/tokens/URLs come from **environment variables** — nothing here contains credentials, and
nothing committed should. Keep `LETTA_TOKEN` and any API keys in the environment or a secrets store.
