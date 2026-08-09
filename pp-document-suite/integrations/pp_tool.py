#!/usr/bin/env python3
"""
pp_tool.py — the Purely Plant Document Suite exposed as ONE portable, self-contained tool
function that any agent framework or model can call (OpenAI/Gemini/Llama/Mistral, LangChain,
Letta, Agent Zero, …). Two variants:

  build_pp_document(markdown, out_path)        -> runs the engine IN-PROCESS on this host
  build_pp_document_via_api(markdown, name)    -> calls a remote QMS build SERVICE over HTTP

Both take bilingual Markdown (references/GUIDE_bilingual_markdown.md) and return a controlled
Purely Plant .docx in the house style (logo header/footer, one navy #2B547E, intelligent tables).
Content is decided by the caller; appearance is decided by the engine — keep that split.

The functions are written to be COPIED VERBATIM into a tool registry (their source is extracted
by letta_register.py), so each is self-contained and imports what it needs internally.
"""


def build_pp_document(markdown: str, out_path: str) -> dict:
    """Generate a Purely Plant bilingual Macedonian|English controlled .docx from bilingual Markdown.

    Runs the pp-document-suite engine in-process. The Markdown uses a <!--HEADERDATA ...--> block
    (mk_title, en_title, code, version, doctype, supersedes, parent, orient) then sections; '|||'
    separates the MK and EN halves. The house template (logo header, Page X of Y footer), the one
    navy #2B547E, the two-column SOP / inline Annex layout and the intelligent table sizing are all
    applied automatically. Requires python-docx (+ lxml) on this host and the suite at $PP_SUITE_DIR
    (defaults to this file's parent package).

    Args:
        markdown (str): bilingual Markdown source (see references/GUIDE_bilingual_markdown.md).
        out_path (str): destination .docx path.

    Returns:
        dict: {ok: bool, out_path: str, verify: str} — ok is True when pp_verify prints RESULT: PASS.
    """
    import os, sys, tempfile, subprocess
    suite = os.environ.get("PP_SUITE_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts = os.path.join(suite, "scripts")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(markdown)
        src = f.name
    try:
        subprocess.run([sys.executable, os.path.join(scripts, "build_from_md.py"), src, out_path], check=True)
        v = subprocess.run([sys.executable, os.path.join(scripts, "pp_verify.py"), out_path],
                           capture_output=True, text=True)
    finally:
        os.unlink(src)
    return {"ok": "RESULT: PASS" in v.stdout, "out_path": out_path, "verify": v.stdout.strip()}


def build_pp_document_via_api(markdown: str, name: str = "document") -> dict:
    """Generate a Purely Plant bilingual MK|EN controlled .docx by calling the QMS build service.

    No engine or template needed on the caller's host — only `requests` and the service URL. The
    service (integrations/service.py, or the site QMS API on :8500) owns the engine, fonts and
    LibreOffice/Gotenberg. Reads the base URL from $QMS_API_BASE (default http://localhost:8600).

    Args:
        markdown (str): bilingual Markdown source (see references/GUIDE_bilingual_markdown.md).
        name (str): base file name (no extension).

    Returns:
        dict: the service JSON, e.g. {ok, path|url, verify}.
    """
    import os, requests
    base = os.environ.get("QMS_API_BASE", "http://localhost:8600").rstrip("/")
    r = requests.post(base + "/build", json={"markdown": markdown, "name": name}, timeout=180)
    r.raise_for_status()
    return r.json()


# JSON schema (framework-agnostic tool definition — OpenAI / Gemini / Anthropic tool-use all accept it)
TOOL_SCHEMA = {
    "name": "build_pp_document",
    "description": ("Generate a Purely Plant bilingual Macedonian|English controlled .docx "
                    "(SOP, Annex, or report/record) from bilingual Markdown. Applies the house "
                    "template, header/footer/logo, the one navy #2B547E and intelligent table "
                    "layout automatically, then verifies the result."),
    "parameters": {
        "type": "object",
        "properties": {
            "markdown": {"type": "string", "description": ("Bilingual Markdown per "
                          "references/GUIDE_bilingual_markdown.md: a <!--HEADERDATA ...--> block "
                          "then sections; '|||' separates the MK and EN halves.")},
            "out_path": {"type": "string", "description": "Destination .docx path."},
        },
        "required": ["markdown", "out_path"],
    },
}


if __name__ == "__main__":
    # tiny CLI: build_pp_document <src.md> <out.docx>
    import sys
    if len(sys.argv) != 3:
        print("usage: python3 pp_tool.py <src.md> <out.docx>"); raise SystemExit(2)
    res = build_pp_document(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2])
    print(res["verify"]); raise SystemExit(0 if res["ok"] else 1)
