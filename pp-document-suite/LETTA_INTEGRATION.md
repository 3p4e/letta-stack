# LETTA_INTEGRATION — connecting the engine to stateful Letta agents

This wires the Purely Plant Document Suite into **Letta** stateful agents so a persistent agent
(with long-term memory of house rules, codes, and prior documents) can generate controlled `.docx`
on demand. It targets the existing Purely Plant deployment and stays generic enough to re-create
elsewhere. Letta REST surface: see the in-repo `openapi_letta.json` (Letta API v0.16.8).

> **Secrets:** never hard-code the Letta token, DB URL, SSH key, or OpenAI key in a tool. Read them
> from environment variables at runtime. Nothing in this package contains credentials and nothing
> committed should.

---

## 0. The two ways to attach the engine to a Letta agent

| Mode | What the agent calls | Where the engine runs | Use when |
|---|---|---|---|
| **A. Custom tool (in-process)** | a Python function registered as a Letta tool | inside the Letta tool sandbox (needs `python-docx` there) | the Letta host can `pip install python-docx lxml` and reach the template file |
| **B. REST tool (out-of-process)** | a tool that HTTP-POSTs to the QMS build service | a separate service/container owning the engine + template + fonts + LibreOffice | you want ONE engine shared by many agents, clean dependency isolation, and DOCX→PDF via Gotenberg |

Mode B matches the current site topology (QMS API on `:8500`, Gotenberg for DOCX→PDF). Prefer it.

---

## 1. Mode A — register a Letta custom tool (in-process)

A Letta tool is a plain Python function with typed args and a docstring; Letta derives the schema
from the signature + docstring. Define it against the engine:

```python
# pp_letta_tool.py  — attach to an agent as a source-code tool
def build_pp_document(markdown: str, out_path: str) -> str:
    """Generate a Purely Plant bilingual Macedonian|English controlled .docx from bilingual Markdown.

    The Markdown uses a <!--HEADERDATA ...--> block (mk_title, en_title, code, version, doctype,
    supersedes, parent, orient) then sections; '|||' separates the MK and EN halves. The house
    template (logo header, Page X of Y footer), the one navy #2B547E, the two-column SOP / inline
    Annex layout and the intelligent table sizing are ALL applied by the engine automatically.
    Returns the verify-gate output (must contain 'RESULT: PASS').

    Args:
        markdown (str): bilingual Markdown source (see references/GUIDE_bilingual_markdown.md).
        out_path (str): destination .docx path on the Letta host.
    """
    import os, sys, tempfile, subprocess
    SUITE = os.environ.get("PP_SUITE_DIR", "/opt/pp-document-suite")   # where this package lives
    S = os.path.join(SUITE, "scripts")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(markdown); src = f.name
    subprocess.run([sys.executable, os.path.join(S, "build_from_md.py"), src, out_path], check=True)
    v = subprocess.run([sys.executable, os.path.join(S, "pp_verify.py"), out_path],
                       capture_output=True, text=True)
    os.unlink(src)
    return v.stdout.strip()
```

Register and attach it (Letta Python SDK; the host must have `python-docx lxml` and the package at
`$PP_SUITE_DIR`):

```python
from letta_client import Letta
client = Letta(base_url=os.environ["LETTA_BASE_URL"], token=os.environ.get("LETTA_TOKEN"))

tool = client.tools.upsert_from_function(func=build_pp_document)          # derives schema from docstring
client.agents.tools.attach(agent_id=QMS_DOCX_FORMATTER_ID, tool_id=tool.id)
```

Attach it to the document-facing agents in the existing fleet — **`qms_docx_formatter`** and
**`pharma_docx_formatter`** — and let **`qms_pipeline_orchestrator`** call them as a step. Put the
house rules the agent must remember (one navy `#2B547E`; 9-section SOP; MK-first, abbreviations never
translated; codes `WHSOP_/QCSOP_/…`) into the agent's **persona / core memory** so they persist across
sessions — that is the point of a stateful agent over a one-shot skill.

## 2. Mode B — REST tool pointing at the QMS build service (recommended)

Stand up the engine as a service once (see `PORTABILITY.md` Path D), then give agents a tiny tool
that just calls it. This keeps `python-docx`, the template, the fonts and LibreOffice in ONE place.

```python
def build_pp_document_via_api(markdown: str, name: str = "document") -> str:
    """Generate a Purely Plant bilingual MK|EN controlled .docx by calling the QMS document service.
    Returns a URL/path to the produced .docx. House template + layout applied server-side.

    Args:
        markdown (str): bilingual Markdown source (GUIDE_bilingual_markdown.md).
        name (str): base file name (no extension).
    """
    import os, requests
    base = os.environ.get("QMS_API_BASE", "http://localhost:8500")     # existing QMS API
    r = requests.post(f"{base}/api/v1/sop/format",
                      json={"markdown": markdown, "name": name}, timeout=120)
    r.raise_for_status()
    return r.json().get("path") or r.text
```

The existing **QMS API (:8500)** already exposes the relevant surface — `/api/v1/sop/format`,
`/api/v1/sop/generate`, `/api/v1/document/convert-to-pdf` — and is wired to **Gotenberg**
(DOCX→PDF) and the Letta daemon. Point the service's formatter at THIS package (`build_from_md.py`
+ `pp_verify.py`) so the REST output is the same house-style `.docx` the skill produces. For PDF,
chain `/api/v1/document/convert-to-pdf` (Gotenberg) after the build.

## 3. Server-side build worker (what the service should run)

Whichever mode, the actual build step on the server is exactly the skill's loop:

```
build_from_md.py <src.md> <out.docx>          # engine — house style, header/footer/logo, layout
pp_verify.py <out.docx>                        # gate  — RESULT: PASS (font floor, bilingual, fidelity)
soffice --headless --convert-to pdf <out.docx> # or Gotenberg — DOCX -> PDF
```

Fail the request if `pp_verify.py` does not print `RESULT: PASS`. Install Calibri/Arial Narrow (or
Carlito/Liberation substitutes) on the render node so the PDF matches Word.

## 4. Division of labour (keep content and formatting separate)

- **The Letta agent owns CONTENT** — it reasons over its memory (regulatory backbone, house codes,
  prior SOPs, the RAG corpus already ingested into `gmp_rag_agent`/`eu_gmp_compliance_expert`) to
  produce correct bilingual Markdown per `SKILL.md` §2 and `references/`.
- **The engine owns APPEARANCE** — never let the agent emit colours, fonts, or table widths. It emits
  the Markdown; `build_from_md.py` renders the house style. This is the same content/format split that
  keeps output consistent across models (`PORTABILITY.md`).

## 5. Checklist to go live

- [ ] Package deployed to `$PP_SUITE_DIR` (Mode A) **or** behind the QMS service (Mode B).
- [ ] `python-docx` + `lxml` installed on whichever host runs the engine; template present.
- [ ] Fonts (Calibri / Arial Narrow or substitutes) + LibreOffice/Gotenberg on the render node.
- [ ] Tool registered and attached to `qms_docx_formatter` / `pharma_docx_formatter`.
- [ ] House rules written into each agent's persona/core memory (persist across sessions).
- [ ] `LETTA_BASE_URL` / `LETTA_TOKEN` / `QMS_API_BASE` supplied via env, not hard-coded.
- [ ] Build gate enforced: reject any output that is not `RESULT: PASS`.
