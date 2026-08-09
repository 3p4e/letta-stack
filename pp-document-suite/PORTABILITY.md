# PORTABILITY — using the engine off-Claude (other platforms, harnesses, models, agents)

The suite is **plain Python + one `.docx` template**. `SKILL.md` describes how a *Claude* skill
runtime drives it, but the engine has no dependency on Claude, Anthropic, or any particular IDE.
Anything that can run Python 3.9+ can call it. This document shows the four ways to use it.

The one invariant, everywhere: **load the base template so every page gets the house header/footer**,
build the body with the engine's helpers, `save()`, then run `pp_verify.py`. Never hand-roll styling.

---

## Path A — as a Claude / Anthropic skill (the native path)

Drop `pp-document-suite/` where the harness discovers skills (e.g. `~/.claude/skills/`,
`/mnt/skills/user/`, or a repo the agent has open). The `SKILL.md` front-matter (`name`,
`when_to_use`, triggers) makes it auto-activate. This is what `SKILL.md` documents; nothing else
to configure. Works identically in Claude Code (CLI, web, desktop, IDE extensions) and the Agent SDK.

## Path B — as a plain Python library (any script, any OS, no agent at all)

The engine's public functions **are** its API. Put `scripts/` on `sys.path` and import:

```python
import sys; sys.path.insert(0, "pp-document-suite/scripts")
import pp_format as pf

d = pf.new_annex(code="WHSOP_002_A02", version="01",
                 mk_title="Записник за ослободување од царински склад",
                 en_title="Customs-Warehouse Release Record", orient="portrait")
pf.annex_title_block(d, "WHSOP_002_A02", "…MK…", "…EN…", "WHSOP_002")   # 5th arg = parent SOP
t = pf.annex_table(d, [4.0, 14.46])
pf.annex_section_header(t, "Пратка", "Consignment")
pf.annex_row(t, ["MRN", "________"], bold_first=True)
pf.annex_finalize(t); pf.annex_signoff(d)
pf.save(d, "A02.docx")
```

Reports/records with formulas, worked calcs, forms and charts use `pp_report.py`
(`cover_page → chapter → calc_step/eqn → entry_table/step_signoff → figure`) — see `SKILL.md` §3.7.

**Bilingual-Markdown fast path** (no Python knowledge needed to author): write the content as
bilingual Markdown per `references/GUIDE_bilingual_markdown.md`, then:

```bash
python3 pp-document-suite/scripts/build_from_md.py  source.md  out.docx
python3 pp-document-suite/scripts/pp_verify.py      out.docx      # RESULT: PASS
```

`build_from_md.py` is a thin adapter — all appearance comes from the engine, so a document authored
in Markdown is byte-for-byte in house style. This is the exact pipeline used for the `WHSOP_002`
transport suite.

## Path C — as a tool exposed to ANY agent framework (function-calling)

Wrap one function and hand its JSON schema to the model. This works for OpenAI/GPT, Gemini, Llama,
Mistral, LangChain/LlamaIndex tools, Agent Zero, Kilo, Hermes — any framework that does tool-calling.

```python
# pp_tool.py — a single portable tool any agent can call
import sys, subprocess, tempfile, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

def build_pp_document(markdown: str, out_path: str) -> dict:
    """Generate a Purely Plant bilingual MK|EN controlled .docx from bilingual Markdown.
    `markdown` follows references/GUIDE_bilingual_markdown.md (HEADERDATA block + `|||` MK|EN).
    Returns {ok, out_path, verify}. House header/footer/logo and layout are applied automatically."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(markdown); src = f.name
    here = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(here, "scripts")
    subprocess.run([sys.executable, os.path.join(S, "build_from_md.py"), src, out_path], check=True)
    v = subprocess.run([sys.executable, os.path.join(S, "pp_verify.py"), out_path],
                       capture_output=True, text=True)
    os.unlink(src)
    return {"ok": "RESULT: PASS" in v.stdout, "out_path": out_path, "verify": v.stdout.strip()}
```

JSON schema to register with the model (OpenAI / Gemini / Anthropic tool-use all accept this shape):

```json
{
  "name": "build_pp_document",
  "description": "Generate a Purely Plant bilingual MK|EN controlled .docx (SOP/Annex/report) from bilingual Markdown. Applies the house template, header/footer/logo, and layout automatically; verifies the result.",
  "parameters": {
    "type": "object",
    "properties": {
      "markdown": {"type": "string", "description": "Bilingual Markdown per GUIDE_bilingual_markdown.md: a <!--HEADERDATA ...--> block then sections; '|||' separates MK|EN."},
      "out_path": {"type": "string", "description": "Destination .docx path."}
    },
    "required": ["markdown", "out_path"]
  }
}
```

The model decides *what to write* (content); the engine decides *how it looks* (house style). Keep
that split — do not let the model emit styling.

## Path D — behind a REST service (share one engine across many agents / machines)

Expose the same function over HTTP so thin clients (or agents on other hosts) need no Python:

```python
# service.py  —  pip install fastapi uvicorn python-docx lxml
from fastapi import FastAPI; from fastapi.responses import FileResponse
from pydantic import BaseModel; import pp_tool, tempfile, os
app = FastAPI(title="PP Document Suite")
class Req(BaseModel): markdown: str; name: str = "document"
@app.post("/build")
def build(r: Req):
    out = os.path.join(tempfile.gettempdir(), r.name + ".docx")
    res = pp_tool.build_pp_document(r.markdown, out)
    if not res["ok"]: return res
    return FileResponse(out, filename=r.name + ".docx")
```

`uvicorn service:app --host 0.0.0.0 --port 8600` → `POST /build {markdown,name}` returns the `.docx`.
Chain a DOCX→PDF step (LibreOffice/`soffice` container, or Gotenberg) for a PDF endpoint. This is the
pattern the existing Purely Plant **QMS API (:8500)** already follows — see `LETTA_INTEGRATION.md`.

---

## Portability notes & limits

- **Cross-model content quality:** the engine renders identically regardless of which model wrote the
  content. What varies off-Claude is *content* quality (bilingual MK precision, correct citations,
  9-section discipline). Carry `SKILL.md` §2/§2.1, `references/questionnaire_library.md` and
  `regulatory_and_context.md` into the other model's system prompt so it authors to the same standard.
- **Equations** need `latex2mathml` + `MML2OMML.XSL` (Office/Windows). Elsewhere they degrade to text —
  functional, not pretty. Render on a Windows/Word node if editable OMML matters.
- **Fonts:** Calibri / Arial Narrow are assumed by the template. On Linux render nodes install the
  matching fonts (or Carlito/Liberation as metric-compatible substitutes) so the PDF matches Word.
- **The template is the contract:** `assets/PP_BASE_TEMPLATE.docx` carries the logo, header, footer and
  A4 geometry. Ship it with the code; the engine loads it by relative path. Do not regenerate the
  header in code.
- **Determinism:** given the same input, the engine is deterministic — good for CI. Add
  `python3 scripts/pp_verify.py <doc>` as a build gate (exit non-zero on FAIL).
